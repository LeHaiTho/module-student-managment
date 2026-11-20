# Backup database production, giữ 14 bản gần nhất.
#   powershell -ExecutionPolicy Bypass -File tools\prod_backup.ps1
# Đặt lịch hằng ngày lúc 02:00 (chạy 1 lần, quyền user hiện tại):
#   powershell -ExecutionPolicy Bypass -File tools\prod_backup.ps1 -Schedule
# Khôi phục vào DB MỚI (không ghi đè): tools/backup_restore.sh restore <file> <db_moi>
param([switch]$Schedule, [int]$Keep = 14)
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root
if ($Schedule) {
    $action = New-ScheduledTaskAction -Execute "powershell.exe" `
        -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$root\tools\prod_backup.ps1`"" -WorkingDirectory $root
    $trigger = New-ScheduledTaskTrigger -Daily -At 2am
    Register-ScheduledTask -TaskName "UnivSMS-Backup" -Action $action -Trigger $trigger -Force | Out-Null
    Write-Host "Da dat lich backup hang ngay 02:00 (task UnivSMS-Backup)"
    exit 0
}
$envs = @{}
Get-Content .env.prod | Where-Object { $_ -match '^\s*([A-Z_]+)=(.*)$' } | ForEach-Object { $envs[$Matches[1]] = $Matches[2] }
$db = if ($envs.DB_NAME) { $envs.DB_NAME } else { "univ_sms" }
$dir = Join-Path $root "backups\prod"
New-Item -ItemType Directory -Force $dir | Out-Null
$file = Join-Path $dir ("{0}_{1}.dump" -f $db, (Get-Date -Format "yyyyMMdd_HHmmss"))
cmd /c "docker compose -f docker-compose.prod.yml --env-file .env.prod exec -T db pg_dump -U odoo -Fc --no-owner --no-acl $db > `"$file`""
if ((Get-Item $file).Length -lt 100000) { throw "File backup qua nho, kiem tra lai: $file" }
Write-Host "Backup: $file ($([math]::Round((Get-Item $file).Length/1MB,1)) MB)"
Get-ChildItem $dir -Filter "$db`_*.dump" | Sort-Object LastWriteTime -Descending | Select-Object -Skip $Keep | Remove-Item -Force
