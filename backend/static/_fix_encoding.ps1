$ErrorActionPreference = 'Stop'
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$gbk = [System.Text.Encoding]::GetEncoding('gb2312')

foreach ($f in @('admin.html', 'avatar-manage.html')) {
    $p = Join-Path 'd:\softwarecup\softwarecup\backend\static' $f
    $html = [System.IO.File]::ReadAllText($p, [System.Text.Encoding]::UTF8)
    $fixed = [System.Text.Encoding]::UTF8.GetString($gbk.GetBytes($html))
    [System.IO.File]::WriteAllText($p, $fixed, $utf8NoBom)
    Write-Host "fixed $f, len=$($fixed.Length)"
}
