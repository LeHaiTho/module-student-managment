from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)


def font(size=26, bold=False):
    candidates = [
        "C:/Windows/Fonts/timesbd.ttf" if bold else "C:/Windows/Fonts/times.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for p in candidates:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


F_TITLE = font(34, True)
F_H = font(25, True)
F = font(23)
F_SMALL = font(20)
F_MONO = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 21) if Path("C:/Windows/Fonts/consola.ttf").exists() else font(20)


def save_canvas(name, title, blocks, size=(1600, 950)):
    img = Image.new("RGB", size, "#f8fafc")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, size[0], 88], fill="#0f172a")
    d.text((44, 24), title, fill="white", font=F_TITLE)
    for block in blocks:
        kind = block.get("kind", "box")
        if kind == "box":
            x, y, w, h = block["xywh"]
            fill = block.get("fill", "#ffffff")
            outline = block.get("outline", "#334155")
            d.rounded_rectangle([x, y, x + w, y + h], radius=18, fill=fill, outline=outline, width=3)
            d.text((x + 24, y + 18), block["header"], fill="#0f172a", font=F_H)
            yy = y + 62
            for line in block.get("lines", []):
                d.text((x + 26, yy), line, fill="#334155", font=F_SMALL)
                yy += 34
        elif kind == "arrow":
            x1, y1, x2, y2 = block["xy"]
            d.line([x1, y1, x2, y2], fill="#2563eb", width=6)
            if x2 >= x1:
                d.polygon([(x2, y2), (x2 - 18, y2 - 12), (x2 - 18, y2 + 12)], fill="#2563eb")
            else:
                d.polygon([(x2, y2), (x2 + 18, y2 - 12), (x2 + 18, y2 + 12)], fill="#2563eb")
        elif kind == "text":
            d.text(block["xy"], block["text"], fill=block.get("fill", "#334155"), font=block.get("font", F))
    img.save(OUT / name)


def figure_31():
    blocks = [
        {"kind": "box", "xywh": (70, 160, 340, 210), "header": "Máy người dùng", "lines": ["Chrome / Edge", "localhost:8069", "Backend + Portal"], "fill": "#e0f2fe"},
        {"kind": "arrow", "xy": (410, 265, 570, 265)},
        {"kind": "box", "xywh": (570, 140, 420, 250), "header": "Service odoo", "lines": ["image: odoo:17.0", "port: 8069:8069", "./addons -> /mnt/extra-addons", "odoo.conf -> /etc/odoo"], "fill": "#eef2ff"},
        {"kind": "arrow", "xy": (990, 265, 1160, 265)},
        {"kind": "box", "xywh": (1160, 160, 340, 210), "header": "Service db", "lines": ["image: postgres:15", "user/password: odoo", "volume: db_data"], "fill": "#dcfce7"},
        {"kind": "box", "xywh": (330, 520, 960, 210), "header": "Docker volumes", "lines": ["odoo_data: dữ liệu runtime Odoo", "db_data: dữ liệu PostgreSQL", "Giúp dữ liệu không mất khi container restart"], "fill": "#fff7ed"},
        {"kind": "arrow", "xy": (780, 390, 780, 520)},
        {"kind": "arrow", "xy": (1330, 370, 1070, 520)},
    ]
    save_canvas("hinh-3-1-docker-compose-architecture.png", "Hình 3.1 - Kiến trúc Docker Compose của University SMS", blocks)


def figure_32():
    lines = [
        "Module_quan-ly-sinh-vien/",
        "├── addons/",
        "│   ├── univ_sms_base/",
        "│   ├── univ_sms_student/",
        "│   ├── univ_sms_registration/",
        "│   ├── univ_sms_portal/",
        "│   └── univ_sms_report/",
        "├── docs/",
        "├── docker-compose.yml",
        "├── odoo.conf",
        "└── HUONG_DAN_CAI_DAT.md",
    ]
    img = Image.new("RGB", (1600, 950), "#f8fafc")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 1600, 88], fill="#0f172a")
    d.text((44, 24), "Hình 3.2 - Cấu trúc thư mục triển khai", fill="white", font=F_TITLE)
    d.rounded_rectangle([110, 150, 1490, 820], radius=18, fill="#ffffff", outline="#334155", width=3)
    y = 200
    for idx, line in enumerate(lines):
        color = "#0f172a" if idx == 0 else "#334155"
        d.text((170, y), line, fill=color, font=F_MONO)
        y += 52
    d.text((170, 765), "Các custom addon được mount vào container Odoo tại /mnt/extra-addons.", fill="#2563eb", font=F)
    img.save(OUT / "hinh-3-2-project-structure.png")


def figure_33():
    text = [
        "PS E:\\ThoDev\\Module_quan-ly-sinh-vien> docker compose ps",
        "",
        "NAME                              IMAGE         SERVICE   STATUS       PORTS",
        "module_quan-ly-sinh-vien-db-1     postgres:15   db        Up 2 hours   5432/tcp",
        "module_quan-ly-sinh-vien-odoo-1   odoo:17.0     odoo      Up 2 hours   0.0.0.0:8069->8069/tcp",
    ]
    img = Image.new("RGB", (1600, 900), "#111827")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 1600, 78], fill="#1f2937")
    d.text((38, 22), "Hình 3.3 - Kiểm tra trạng thái container", fill="#e5e7eb", font=F_H)
    y = 150
    for line in text:
        d.text((80, y), line, fill="#d1fae5" if "Up" in line else "#e5e7eb", font=F_MONO)
        y += 48
    img.save(OUT / "hinh-3-3-docker-compose-ps.png")


def figure_34():
    text = [
        "[options]",
        "addons_path = /mnt/extra-addons,/usr/lib/python3/dist-packages/odoo/addons",
        "db_host = db",
        "db_user = odoo",
        "db_password = odoo",
        "db_name = univ_sms_db",
        "admin_passwd = <hashed master password>",
    ]
    img = Image.new("RGB", (1600, 900), "#f8fafc")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 1600, 88], fill="#0f172a")
    d.text((44, 24), "Hình 3.4 - Cấu hình odoo.conf", fill="white", font=F_TITLE)
    d.rounded_rectangle([100, 150, 1500, 650], radius=18, fill="#0b1220", outline="#334155", width=3)
    y = 205
    for line in text:
        d.text((150, y), line, fill="#e5e7eb", font=F_MONO)
        y += 52
    d.text((120, 735), "Ý nghĩa: trỏ Odoo tới PostgreSQL service 'db' và thư mục custom addons.", fill="#334155", font=F)
    img.save(OUT / "hinh-3-4-odoo-conf.png")


def figure_35():
    blocks = [
        {"kind": "box", "xywh": (70, 165, 280, 160), "header": "1. Chuẩn bị", "lines": ["Docker", "Source code", "Terminal"], "fill": "#e0f2fe"},
        {"kind": "arrow", "xy": (350, 245, 470, 245)},
        {"kind": "box", "xywh": (470, 165, 290, 160), "header": "2. Start", "lines": ["docker compose up -d", "pull images"], "fill": "#dcfce7"},
        {"kind": "arrow", "xy": (760, 245, 880, 245)},
        {"kind": "box", "xywh": (880, 165, 290, 160), "header": "3. Database", "lines": ["univ_sms_db", "PostgreSQL 15"], "fill": "#fff7ed"},
        {"kind": "arrow", "xy": (1170, 245, 1290, 245)},
        {"kind": "box", "xywh": (1290, 165, 240, 160), "header": "4. Modules", "lines": ["-i univ_sms_*", "install"], "fill": "#eef2ff"},
        {"kind": "box", "xywh": (270, 520, 310, 160), "header": "5. Seed data", "lines": ["odoo shell", "demo users", "demo records"], "fill": "#fef2f2"},
        {"kind": "arrow", "xy": (1010, 325, 430, 520)},
        {"kind": "arrow", "xy": (580, 600, 730, 600)},
        {"kind": "box", "xywh": (730, 520, 310, 160), "header": "6. Kiểm tra", "lines": ["audit script", "log", "browser"], "fill": "#f0fdf4"},
        {"kind": "arrow", "xy": (1040, 600, 1190, 600)},
        {"kind": "box", "xywh": (1190, 520, 310, 160), "header": "7. Demo", "lines": ["/web", "/university", "/my/academic"], "fill": "#eff6ff"},
    ]
    save_canvas("hinh-3-5-install-flow.png", "Hình 3.5 - Quy trình cài đặt và khởi chạy hệ thống", blocks)


def figure_36():
    rows = [
        ("Backend", "http://localhost:8069/web"),
        ("Landing", "http://localhost:8069/university"),
        ("Portal", "http://localhost:8069/my/academic"),
        ("Đăng ký SV", "http://localhost:8069/student/register"),
        ("Tài khoản SV", "sv.nguyenvanan / 123456"),
        ("Tài khoản Admin", "admin.sms / 123456"),
    ]
    img = Image.new("RGB", (1600, 900), "#f8fafc")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 1600, 88], fill="#0f172a")
    d.text((44, 24), "Hình 3.6 - Các điểm truy cập sau cài đặt", fill="white", font=F_TITLE)
    x1, y1, x2, y2 = 150, 155, 1450, 730
    d.rounded_rectangle([x1, y1, x2, y2], radius=18, fill="#ffffff", outline="#334155", width=3)
    d.rectangle([x1, y1, x2, y1 + 70], fill="#dbeafe")
    d.text((x1 + 40, y1 + 20), "Khu vực", fill="#0f172a", font=F_H)
    d.text((x1 + 480, y1 + 20), "Thông tin truy cập", fill="#0f172a", font=F_H)
    y = y1 + 85
    for label, url in rows:
        d.line([x1, y - 12, x2, y - 12], fill="#cbd5e1", width=2)
        d.text((x1 + 40, y), label, fill="#334155", font=F)
        d.text((x1 + 480, y), url, fill="#2563eb", font=F_MONO if "http" in url else F)
        y += 78
    img.save(OUT / "hinh-3-6-access-links.png")


if __name__ == "__main__":
    figure_31()
    figure_32()
    figure_33()
    figure_34()
    figure_35()
    figure_36()
