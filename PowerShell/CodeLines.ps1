<#
PSVersion: 5.1
---------------------------------------------------------------------------
This script is simply used to measure how many code(Lines) you had written.
---------------------------------------------------------------------------
Example: ./CodeLines.ps1 -Diretory C:\Users\Nomyfan\Desktop -Include *.ps1 -Exclude DHCP.ps1
#>

param
(
    [Parameter(Mandatory = $true)][string[]]$Diretory,
    [Parameter(Mandatory = $true)][string[]]$Include,
    [Parameter()][string[]]$Exclude
)
$count = 0
$lines = 0

foreach ($dir in $Diretory) {
    $dir = $dir + "\*"
    $files = Get-ChildItem -Path $dir -Recurse -Include $Include -Exclude $Exclude

    foreach ($file in $files) {
        $count += 1
        $lines += (Get-Content -Path $file.FullName | Measure-Object -Line).Lines
    }
}

Write-Host('----------------------------')
Write-Host('Files: ' + [string]$count)
Write-Host('Lines: ' + [string]$lines)
Write-Host('----------------------------')