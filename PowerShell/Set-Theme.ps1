<#
PSVersion: 5.1
----------------------------------------------------------------
This script is used to set system theme and app theme to Light or Dark.
We can use it along with Task Scheduler to toggle theme automatically.
----------------------------------------------------------------
#>

[CmdletBinding()]
param (
  [Parameter(Mandatory = $false)]
  [ValidateSet("Light", "Dark")]
  [string]
  $SystemTheme = "Light",
  [Parameter(Mandatory = $false)]
  [ValidateSet("Light", "Dark")]
  [string]
  $AppTheme = "Light"
)

$systemThemeValue = 1
$appThemeValue = 1

if ("Dark" -eq $SystemTheme) {
  $systemThemeValue = 0
}
if ("Dark" -eq $AppTheme) {
  $appThemeValue = 0
}

New-ItemProperty -Path "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize" -Name "SystemUsesLightTheme" -Value $systemThemeValue -PropertyType Dword -Force
New-ItemProperty -Path "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize" -Name "AppsUseLightTheme" -Value $appThemeValue -PropertyType Dword -Force
