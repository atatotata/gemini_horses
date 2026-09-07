[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[System.Text.Encoding]::RegisterProvider([System.Text.CodePagesEncodingProvider]::Instance)

function ReadText($p) {
  $bytes = [System.IO.File]::ReadAllBytes($p)
  try {
    [System.Text.Encoding]::GetEncoding('utf-8', [System.Text.EncoderFallback]::ExceptionFallback, [System.Text.DecoderFallback]::ExceptionFallback).GetString($bytes)
  } catch {
    [System.Text.Encoding]::GetEncoding(932).GetString($bytes)
  }
}

function Scan($d) {
  $name = Split-Path $d -Leaf
  "===== $name ====="
  $top = Get-ChildItem -LiteralPath $d -Force | Select-Object -First 80
  $top | ForEach-Object { "{0} {1}" -f $(if ($_.PSIsContainer) {'[D]'} else {'[F]'}), $_.Name }

  $exes = Get-ChildItem -LiteralPath $d -File -Filter *.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Name
  if ($exes) { "EXE: " + ($exes -join ', ') }

  $mk = @('www\index.html','Game.rpgproject','Game.rgss3a','RPG_RT.exe','UnityPlayer.dll','renpy\__init__.py','tyrano\index.html','Startup.tjs','index.html','Game.ini','data\System.json','package.json','app.info','Game.exe')
  $found = @()
  foreach ($m in $mk) { if (Test-Path -LiteralPath (Join-Path $d $m)) { $found += $m } }
  $dataDir = Get-ChildItem -LiteralPath $d -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -match '_Data$' } | Select-Object -ExpandProperty Name
  if ($dataDir) { $found += (($dataDir | ForEach-Object { "$_ (_Data)" }) -join ';') }
  $pck = Get-ChildItem -LiteralPath $d -File -Filter *.pck -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Name
  if ($pck) { $found += 'pck: ' + ($pck -join ';') }
  if ($found) { "MARKERS: " + ($found -join ' | ') }

  foreach ($rel in @('Game.ini','package.json','app.info','data\System.json','www\package.json','Game.rpgproject','options.rpy')) {
    $p = Join-Path $d $rel
    if (Test-Path -LiteralPath $p) {
      try {
        $c = ReadText $p
        $snippet = $c.Substring(0, [Math]::Min(350, $c.Length)) -replace "`r?`n", ' | '
        ">> $rel : $snippet"
      } catch { ">> $rel : (read error)" }
    }
  }

  $rm = Get-ChildItem -LiteralPath $d -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -match '(?i)(readme|説明|取り扱|マニュアル|manual|注意|help|ver|更新|変更)' -and $_.Extension -match '\.(txt|md|rtf)$' } | Select-Object -First 3
  foreach ($f in $rm) {
    try {
      $c = ReadText $f.FullName
      $snippet = $c -replace "`r?`n", ' | '
      if ($snippet.Length -gt 380) { $snippet = $snippet.Substring(0, 380) }
      ">> README [$($f.Name)] : $snippet"
    } catch {}
  }
  ""
}

$cutoff = [datetime]"2026/08/20 00:00:00"
$targets = Get-ChildItem -LiteralPath "G:\Downloads\Games" -Directory | Where-Object { $_.CreationTime -ge $cutoff -or $_.Name -match '淫欲' }
"TARGET COUNT: $($targets.Count)"
$targets | Sort-Object CreationTime | ForEach-Object { Scan $_.FullName }