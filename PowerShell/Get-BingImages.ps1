<#
PSVersion: 7.1.3
--------------------------------
Download latest images from Bing
--------------------------------
Usage:
- Use -Index to specify staring index, default is 0
- Use -Count to specify how many images from -Index to download, default is 8(it seems to be the maximum number)
- Use -SaveTo to specify where the images save to, default is current directory
#>

[CmdletBinding()]
param (
  [Parameter()]
  [uint]
  $Index,
  [Parameter()]
  [uint]
  $Count,
  [Parameter()]
  [string]
  $SaveTo
)

if($Count -eq 0) {
  $Count = 8
}

if([System.String]::IsNullOrEmpty($SaveTo)) {
  $SaveTo = './'
}

if(!(Test-Path -Path $SaveTo)) {
  Write-Error ("$SaveTo doesn't exit")
  return
}

function ExtractInfo {
  param (
    [Parameter(Mandatory)]
    [string]
    $Url
  )

  $uri = [System.Uri]("https://cn.bing.com$Url")
  $parsedQuery = [System.Web.HttpUtility]::ParseQueryString($uri.Query)

  return [PSCustomObject]@{
    FileName = $parsedQuery['id']
    Uri = $uri
  }
}

$uri = "https://cn.bing.com/HPImageArchive.aspx?format=js&idx=$Index&n=$Count&mkt=zh-CN"
$response = Invoke-WebRequest -Uri $uri

($response.Content | ConvertFrom-Json).images | ForEach-Object {(ExtractInfo -Url $_.url)} | ForEach-Object -Parallel {
  Invoke-WebRequest -Uri $_.Uri -OutFile ("{0}{1}" -f $SaveTo,$_.FileName)
}
