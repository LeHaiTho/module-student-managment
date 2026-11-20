# Khởi tạo production trên server công ty (chạy 1 lần, chạy lại an toàn).
#   powershell -ExecutionPolicy Bypass -File tools\prod_init.ps1 [-DumpFile backups\univ_sms_demo_deploy.dump]
# - Build image, bật Postgres
# - Nếu database chưa có: nạp từ file dump (dữ liệu demo đã dựng sẵn); không có dump thì Odoo tự cài mới
# - Bật Odoo, đợi /web/health
param(
    [string]$DumpFile = "backups\univ_sms_demo_deploy.dump"
)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
if (-not (Test-Path ".env.prod")) { throw "Thiếu .env.prod (xem .env.prod.example)" }
$envs = @{}
Get-Content .env.prod | Where-Object { $_ -match '^\s*([A-Z_]+)=(.*)$' } | ForEach-Object { $envs[$Matches[1]] = $Matches[2] }
$db = if ($envs.DB_NAME) { $envs.DB_NAME } else { "univ_sms" }
$port = if ($envs.ODOO_PORT) { $envs.ODOO_PORT } else { "8070" }
$dc = @("compose", "-f", "docker-compose.prod.yml", "--env-file", ".env.prod")

Write-Host "[1/4] Build image va bat Postgres"
& docker @dc build odoo
& docker @dc up -d db
for ($i = 0; $i -lt 30; $i++) {
    & docker @dc exec -T db pg_isready -U odoo *> $null
    if ($LASTEXITCODE -eq 0) { break }
    Start-Sleep -Seconds 2
}

$exists = "$(& docker @dc exec -T db psql -U odoo -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$db'")".Trim()
if ($exists -ne "1") {
    if (Test-Path $DumpFile) {
        Write-Host "[2/4] Nap database $db tu $DumpFile"
        & docker @dc exec -T db createdb -U odoo $db
        cmd /c "docker compose -f docker-compose.prod.yml --env-file .env.prod exec -T db pg_restore -U odoo --no-owner --no-acl -d $db < `"$DumpFile`""
    } else {
        Write-Host "[2/4] Khong co file dump: Odoo se tu cai moi 16 module khi khoi dong"
    }
} else {
    Write-Host "[2/4] Database $db da ton tai, giu nguyen du lieu"
}

Write-Host "[3/4] Bat Odoo"
& docker @dc up -d odoo
Write-Host "[4/4] Doi http://127.0.0.1:$port/web/health"
for ($i = 0; $i -lt 90; $i++) {
    try {
        $r = Invoke-WebRequest -UseBasicParsing -TimeoutSec 5 "http://127.0.0.1:$port/web/health"
        if ($r.StatusCode -eq 200) { Write-Host "Odoo san sang tai http://127.0.0.1:$port"; exit 0 }
    } catch { }
    Start-Sleep -Seconds 5
}
throw "Odoo chua san sang sau 7 phut. Xem log: docker compose -f docker-compose.prod.yml logs odoo"
