# Publish Odoo production ra Internet bằng Cloudflare Tunnel (giống cách làm với server DIAMOND VN).
#
#   powershell -ExecutionPolicy Bypass -File tools\prod_tunnel.ps1
#       Quick tunnel (không cần tài khoản): sinh link https://<ngau-nhien>.trycloudflare.com.
#       Link ĐỔI mỗi lần chạy lại; script ghi link vào backups\PUBLIC_URL.txt và cập nhật
#       web.base.url. Mã QR điểm danh luôn lấy đúng địa chỉ giảng viên đang dùng nên không bị ảnh hưởng.
#
#   powershell -ExecutionPolicy Bypass -File tools\prod_tunnel.ps1 -Hostname sms.ten-mien.com
#       Named tunnel (dashboard Cloudflare đã trỏ hostname tới http://127.0.0.1:<ODOO_PORT>):
#       chỉ cập nhật web.base.url theo hostname cố định. Cài connector bằng:
#       cloudflared.exe service install <TUNNEL_TOKEN>
param(
    [string]$Hostname = "",
    [string]$Cloudflared = "C:\Program Files (x86)\cloudflared\cloudflared.exe"
)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
$envs = @{}
Get-Content .env.prod | Where-Object { $_ -match '^\s*([A-Z_]+)=(.*)$' } | ForEach-Object { $envs[$Matches[1]] = $Matches[2] }
$db = if ($envs.DB_NAME) { $envs.DB_NAME } else { "univ_sms" }
$port = if ($envs.ODOO_PORT) { $envs.ODOO_PORT } else { "8070" }
New-Item -ItemType Directory -Force backups | Out-Null

function Set-BaseUrl([string]$url) {
    $sql = "UPDATE ir_config_parameter SET value='$url' WHERE key='web.base.url'; " +
           "INSERT INTO ir_config_parameter(key,value,create_date,write_date) VALUES('web.base.url.freeze','True',now(),now()) " +
           "ON CONFLICT (key) DO UPDATE SET value='True';"
    & docker compose -f docker-compose.prod.yml --env-file .env.prod exec -T db psql -U odoo -d $db -q -c $sql
    Set-Content -Encoding utf8 backups\PUBLIC_URL.txt $url
    Write-Host "web.base.url = $url"
}

if ($Hostname) {
    Set-BaseUrl "https://$Hostname"
    exit 0
}

if (-not (Test-Path $Cloudflared)) { throw "Khong tim thay cloudflared tai $Cloudflared" }
Get-Process cloudflared -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq $Cloudflared -and $_.CommandLine -match "127.0.0.1:$port" } | Stop-Process -Force
$log = Join-Path (Get-Location) "backups\cloudflared_univ_sms.log"
Remove-Item $log -ErrorAction SilentlyContinue
Start-Process -FilePath $Cloudflared -WindowStyle Hidden `
    -ArgumentList @("tunnel", "--no-autoupdate", "--url", "http://127.0.0.1:$port", "--logfile", $log)
for ($i = 0; $i -lt 60; $i++) {
    Start-Sleep -Seconds 2
    if (Test-Path $log) {
        $m = Select-String -Path $log -Pattern 'https://[a-z0-9-]+\.trycloudflare\.com' | Select-Object -First 1
        if ($m) {
            $url = $m.Matches[0].Value
            Set-BaseUrl $url
            Write-Host "Link public: $url"
            exit 0
        }
    }
}
throw "Khong lay duoc link quick tunnel. Xem $log"
