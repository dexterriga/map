param(
    [string]$Message = "Auto-update $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
)

$ProjectDir = "C:\Users\DEXTER\Desktop\party_map_daugavpils_bot"
Set-Location -LiteralPath $ProjectDir

Write-Host "=== Deploy: $Message ===" -ForegroundColor Cyan

# 1. Backup database
$BackupDir = "data\backups"
New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
Copy-Item -LiteralPath "data\party_map.db" -Destination "$BackupDir\party_map_$Timestamp.db" -Force
Write-Host "  [OK] DB backup: $BackupDir\party_map_$Timestamp.db" -ForegroundColor Green

# 2. Check for changes
$Changes = git status --porcelain
if (-not $Changes) {
    Write-Host "  No changes to commit." -ForegroundColor Yellow
    exit 0
}

# 3. Stage all and commit
git add -A
git commit -m $Message
if ($LASTEXITCODE -eq 0) {
    Write-Host "  [OK] Committed: $Message" -ForegroundColor Green
} else {
    Write-Host "  [WARN] Nothing to commit" -ForegroundColor Yellow
}

# 4. Push to GitHub
git push origin main
if ($LASTEXITCODE -eq 0) {
    Write-Host "  [OK] Pushed to GitHub" -ForegroundColor Green
} else {
    Write-Host "  [ERROR] Push failed" -ForegroundColor Red
}

Write-Host "=== Done ===" -ForegroundColor Cyan
