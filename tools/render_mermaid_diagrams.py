from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
MD_PATH = ROOT / "docs" / "BAO_CAO_DO_AN_TOT_NGHIEP_UNIV_SMS.md"
OUT_DIR = ROOT / "docs" / "diagrams"
KROKI_URL = "https://kroki.io/mermaid/png"


def ps_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def clean_caption(line: str) -> str:
    text = line.strip()
    if text.startswith("**") and text.endswith("**"):
        text = text[2:-2]
    return text.strip()


def caption_slug(caption: str, index: int) -> str:
    match = re.search(r"Hình\s+(\d+)\.(\d+)", caption, flags=re.IGNORECASE)
    if match:
        return f"hinh-{match.group(1)}-{match.group(2)}-mermaid.png"
    return f"mermaid-{index:02d}.png"


def find_caption(lines: list[str], close_index: int) -> str:
    for line in lines[close_index + 1 : close_index + 9]:
        stripped = line.strip()
        if re.match(r"^\*\*Hình\s+\d+\.\d+\.", stripped):
            return clean_caption(stripped)
    return ""


def extract_blocks(lines: list[str]) -> list[dict[str, str]]:
    blocks: list[dict[str, str]] = []
    in_block = False
    start = 0
    body: list[str] = []

    for index, line in enumerate(lines):
        stripped = line.strip()
        if not in_block and stripped.startswith("```mermaid"):
            in_block = True
            start = index
            body = []
            continue
        if in_block and stripped.startswith("```"):
            caption = find_caption(lines, index)
            blocks.append(
                {
                    "start": str(start + 1),
                    "end": str(index + 1),
                    "caption": caption,
                    "code": "\n".join(body).strip() + "\n",
                }
            )
            in_block = False
            continue
        if in_block:
            body.append(line)

    return blocks


def render_png(code: str, out_path: Path) -> None:
    tmp = out_path.with_suffix(".mmd")
    tmp.write_text(code, encoding="utf-8")
    ps = (
        f"$body = Get-Content -Raw -Encoding UTF8 -LiteralPath {ps_quote(str(tmp))}\n"
        f"Invoke-WebRequest -Uri {ps_quote(KROKI_URL)} -Method Post -Body $body "
        f"-ContentType 'text/plain; charset=utf-8' -OutFile {ps_quote(str(out_path))}\n"
    )
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            check=True,
            capture_output=True,
            text=True,
            timeout=90,
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(exc.stderr or exc.stdout) from exc
    finally:
        tmp.unlink(missing_ok=True)
    if not out_path.exists() or out_path.stat().st_size == 0:
        raise RuntimeError(f"Mermaid renderer did not create {out_path}")
    flatten_transparency(out_path)


def flatten_transparency(path: Path) -> None:
    image = Image.open(path)
    if image.mode not in ("RGBA", "LA"):
        return
    background = Image.new("RGBA", image.size, "WHITE")
    background.alpha_composite(image.convert("RGBA"))
    background.convert("RGB").save(path)


def main() -> int:
    lines = MD_PATH.read_text(encoding="utf-8").splitlines()
    blocks = extract_blocks(lines)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for idx, block in enumerate(blocks, 1):
        caption = block["caption"]
        out_path = OUT_DIR / caption_slug(caption, idx)
        render_png(block["code"], out_path)
        print(f"{idx}. {caption or '(không có caption)'} -> {out_path.relative_to(ROOT)}")

    print(f"Rendered {len(blocks)} Mermaid diagram(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
