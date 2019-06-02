<#
---------------------------------
Get string or file hash value
---------------------------------
Example1: .\Get-Hash.ps1 -Content "Hello"
Example2: .\Get-Hash.ps1 -Content "Hello" -Algorithm MD5
Example3: .\Get-Hash.ps1 -FilePath .\Get-Base64.ps1
Example4: echo "Hello" | Get-Hash -Algorithm MD5
#>
# Function Get-Hash {
    Param (
        [Parameter(Mandatory = $false, ValueFromPipeline)]
        [Alias("c")]
        [string] $Content,
        [Parameter(Mandatory = $false)]
        [string] $FilePath,
        [Parameter(Mandatory = $false)]
        [ValidateSet("SHA1", "SHA256", "SHA384" , "SHA512", "MACTripleDES", "MD5", "RIPEMD160")]
        [string] $Algorithm = "SHA256"
    ) # end param

    if ("" -ne $Content) {
        $stream = New-Object System.IO.MemoryStream
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($Content)
        $stream.Write($bytes, 0, $bytes.Length)
        Get-FileHash -InputStream $stream -Algorithm $Algorithm | Format-List
        $stream.Close()
    }
    elseif ("" -ne $FilePath) {
        Get-FileHash -Path $FilePath -Algorithm $Algorithm | Format-List
    }
    else {
        Write-Host ("Please provide content or filepath.")
    }
# }