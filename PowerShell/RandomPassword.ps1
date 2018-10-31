<#
PSVersion: 5.1
---------------------------------------------------------------------
This script is used to generate a random password with a given length.
---------------------------------------------------------------------
#>

param (
    [Parameter(Mandatory = $true)]
    [uint16]
    $Length
)

$Length = if ($Length -lt 10) {10} else {$Length}
$rnd = New-Object System.Random
$password = @()

foreach ($i in 1..$Length) {
    $password += [char]($rnd.Next(33, 127))
}

Write-Host -NoNewline 'Output: '
Write-Host ($password -join '') -BackgroundColor Black -ForegroundColor Green