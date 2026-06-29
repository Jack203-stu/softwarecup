$ErrorActionPreference = 'Stop'

$adminNew = Get-Content 'd:\softwarecup\softwarecup\backend\static\_admin_light.txt' -Raw
$admPath  = 'd:\softwarecup\softwarecup\backend\static\admin.html'
$adm = Get-Content $admPath -Raw
$adm = [regex]::Replace($adm, '(?s)<style>.*?</style>', $adminNew)
Set-Content $admPath $adm -Encoding UTF8
Write-Host "admin.html OK, length=" (Get-Content $admPath -Raw).Length

$avaNew = Get-Content 'd:\softwarecup\softwarecup\backend\static\_avatar_light.txt' -Raw
$avaPath = 'd:\softwarecup\softwarecup\backend\static\avatar-manage.html'
$ava = Get-Content $avaPath -Raw
$ava = [regex]::Replace($ava, '(?s)<style>.*?</style>', $avaNew)
Set-Content $avaPath $ava -Encoding UTF8
Write-Host "avatar-manage.html OK, length=" (Get-Content $avaPath -Raw).Length
