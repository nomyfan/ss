<#
-------------------------
Build nerd fonts in parallel.
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
  if ($IsWindows) {
    return (Get-CimInstance Win32_ComputerSystem).NumberOfLogicalProcessors
  }
  elseif ($IsMacOS) {
    return [uint](sysctl -n hw.ncpu)
  }
  elseif ($IsLinux) {
    return [uint](nproc)
  }
  else {
    throw 'Unknown OS'
  }
}

Get-ChildItem $In -File | ForEach-Object -Parallel {
  $fullName = $_.FullName
  $name = $_.Name
  Start-Process -PassThru -Wait -FilePath 'docker' -ArgumentList 'run', '--rm', '-v', """${fullName}"":""/in/${name}""", '-v', """${using:Out}"":/out", 'nerdfonts/patcher:4.14.3', '--complete', '--careful', '--makegroups', '1', '--quiet'
} -ThrottleLimit (Get-NumberOfLogicalProcessors)
