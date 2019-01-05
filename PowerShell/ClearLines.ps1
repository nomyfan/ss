<#
PSVersion: 5.1
----------------------------------------------------------------------------------
This script is used to clear the Nth lines before a line starts with special words.
I use it to clear the comment in the code files.
----------------------------------------------------------------------------------
Example: .\ClearLines.ps1 -Diretory C:\Users\Nomyfan\Desktop -Include *.cs -StartsWith 'using', 'namespace'
#>
param
(
    [Parameter(Mandatory = $true)][string]$Diretory,
    [Parameter(Mandatory = $true)][string[]]$Include,
    [Parameter(Mandatory = $true)][string[]]$StartsWith,
    [Parameter()][string[]]$Exclude
)

$dir = $Diretory + "\*"
$files = Get-ChildItem -Path $dir -Include $Include -Exclude $Exclude -Recurse

foreach ($file in $files) {
    $r = 0
    $cnt = Get-Content $file.FullName
    foreach ($line in $cnt) {
        $found = $false
        foreach ($st in $StartsWith) {
            if ($line.StartsWith($StartsWith)) {
                $found = $true
                break
            }
        }
        if ($found -eq $true) {
            break
        } 
        $r = $r + 1
    }
    [System.Collections.ArrayList]$al = $cnt
    $al.RemoveRange(0, $r)
    $al > $file.FullName
}