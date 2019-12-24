<#
--------------------------------
Invoke multi apps in one command
--------------------------------
Example: Invoke-Items 'ppt,excel'
#>
function Invoke-Items {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory = $true)]
        [string]$Apps
    )
    
    $Apps.Split(',') | Where-Object {$_.Trim() -ne ""} | ForEach-Object {
        Start-Process $_
    }
}