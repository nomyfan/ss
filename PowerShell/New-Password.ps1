<#
PSVersion: 5.1
---------------------------------------------------------------------
This script is used to generate a random password with a given length.
---------------------------------------------------------------------
Example1: .\New-Password.ps1
Example2: .\New-Password.ps1 -Length 12
Example3: .\New-Password.ps1 -Length 12 -PunctuationType Custom -Punctuation '_','*','^','@'
#>

param (
    [Parameter(Mandatory = $false)]
    [uint16]
    $Length,
    [Parameter(Mandatory = $false)]
    [ValidateSet('All', 'Custom')]
    [string]
    $PunctuationType,
    [Parameter(Mandatory = $false)]
    [string[]]
    $Punctuation
)

$Length = if ($Length -lt 8) {8} else {$Length}
$rnd = New-Object System.Random
$password = @()

function Write-Password {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]
        $Pwd
    )
    Write-Host -NoNewline 'Output: '
    Write-Host ($Pwd -join '') -BackgroundColor Black -ForegroundColor Green
}

if ($PunctuationType.Length -eq 0 -or $PunctuationType.ToLower().Equals('all')) {
    1..$Length | ForEach-Object {
        $password += [char]($rnd.Next(33, 127))
    }  
    Write-Password -Pwd $password
}
else {
    # Upper case
    $rndMap = [char]'A'..[char]'Z'
    # Lower case
    $rndMap += [char]'a'..[char]'z'
    # Numeric
    $rndMap += [char]'0'..[char]'9'
    # Punctuation
    $Punctuation | ForEach-Object {
        if (([char]$_) -in 33..126 -and ([char]$_) -notin $rndMap) {
            $rndMap += $_
        }
    }

    1..$Length | ForEach-Object {
        $password += [char]($rndMap[$rnd.Next(0, $rndMap.Length)])
    }
    Write-Password -Pwd $password
}