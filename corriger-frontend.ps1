# Sauvegarde avant modification
$backup = "frontend\src_backup_$(Get-Date -Format 'yyyyMMdd-HHmmss')"
Copy-Item -Path "frontend\src" -Destination $backup -Recurse
Write-Host "Backup créé : $backup" -ForegroundColor Green

$fichiers = @(
  "frontend\src\visiteur\Home.jsx",
  "frontend\src\visiteur\OffreDetail.jsx",
  "frontend\src\admin\AdminOffres.jsx",
  "frontend\src\admin\OffreForm.jsx",
  "frontend\src\admin\AgentsLab.jsx"
)

foreach ($f in $fichiers) {
  if (-not (Test-Path $f)) { continue }
  $contenu = Get-Content $f -Raw -Encoding UTF8
  $avant   = $contenu
  
  # 1. /admin/offres → /offers
  $contenu = $contenu -replace '/admin/offres', '/offers'
  # 2. /offres → /offers (le "s" en trop à la fin)
  $contenu = $contenu -replace '"/offres"', '"/offers"'
  $contenu = $contenu -replace '/offres/', '/offers/'
  $contenu = $contenu -replace '/offres`', '/offers`'
  # 3. PUT → PATCH pour les offres (le backend expose PATCH)
  $contenu = $contenu -replace 'api\.put\(`/offers', 'api.patch(`/offers'
  $contenu = $contenu -replace 'api\.put\("/offers', 'api.patch("/offers'
  
  if ($contenu -ne $avant) {
    Set-Content -Path $f -Value $contenu -Encoding UTF8 -NoNewline
    Write-Host "✅ Corrigé : $f" -ForegroundColor Green
  } else {
    Write-Host "⏸️  Inchangé : $f" -ForegroundColor Yellow
  }
}

Write-Host "`nTerminé. Vérifie avec :" -ForegroundColor Cyan
Write-Host 'Get-ChildItem -Path .\frontend\src -Recurse -Include *.jsx | Select-String -Pattern "/offres|/admin/offres|api\.put"' -ForegroundColor Cyan