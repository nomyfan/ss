<#
-------------------------
Build nerd fonts in parallel(Windows only now).
-------------------------
Example: .\Build-NerdFont.ps1 -In 'D:\fonts\a' -Out 'C:\fonts\a\dist'
#>

Param(
  [Parameter(Mandatory = $true)]
  [string] $In,
  [Parameter(Mandatory = $true)]
  [string] $Out
)

function Get-NumberOfLogicalProcessors {
  # Work on Windows only
  return (Get-CimInstance Win32_ComputerSystem).NumberOfLogicalProcessors
}

# Test on Windows with nerdfonts/patcher(f33f76ae16225574c8b42cb50878bd30bf91547186b659c1a08ce7a98e3fbfa1)
Get-ChildItem $In -File | ForEach-Object -Parallel {
  $fullName = $_.FullName
  $name = $_.Name
  Start-Process -PassThru -Wait -FilePath 'docker' -ArgumentList 'run', '--rm', '-v', """${fullName}"":""/in/${name}""", '-v', """${using:Out}"":/out", 'nerdfonts/patcher', '--complete', '--careful', '--makegroups'
} -ThrottleLimit (Get-NumberOfLogicalProcessors)