<#
-------------------------
Base64 encode/decode
-------------------------
Example: echo 'bm9teWZhbg==' | .\Get-Base64.ps1 -m d
#>
#Function Get-Base64 {
    Param(
        [Parameter(Mandatory = $true, ValueFromPipeline)]
        [Alias("t")]
        [string] $Text,
        [Parameter(Mandatory = $false)]
        [Alias("m")]
        [ValidateSet("d","e")]
        [string] $Mode
    ) # end param

    if($Mode -eq "d"){
        Write-Host ([System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($Text)))
    }else{
        Write-Host ([Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($Text)))
    }   
#}