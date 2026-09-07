$c = Get-Content 'G:\Downloads\Documents\battle-damage-games-catalog.html' -Raw
$oA = [regex]::Matches($c, '<article ').Count
$cA = [regex]::Matches($c, '</article>').Count
$oS = [regex]::Matches($c, '<section ').Count
$cS = [regex]::Matches($c, '</section>').Count
$oS19 = [regex]::Matches($c, 'S19').Count
$oA33 = [regex]::Matches($c, 'A33').Count
$total71 = [regex]::Matches($c, '71 games').Count
Write-Host "article open: $oA close: $cA"
Write-Host "section open: $oS close: $cS"
Write-Host "S19 mentions: $oS19"
Write-Host "A33 mentions: $oA33"
Write-Host "71 games mentions: $total71"
Write-Host "Old 17 games count: $([regex]::Matches($c, '17 games').Count)"
Write-Host "Old 31 games count: $([regex]::Matches($c, '31 games').Count)"
Write-Host "Old 67 games count: $([regex]::Matches($c, '67 games').Count)"
