<#
PSVersion: 5.1
----------------------------------------------------------------
This script is used to pull cached spotlight pictures to desktop.
----------------------------------------------------------------
#>

$dir = $HOME + `
    '\AppData\Local\Packages\Microsoft.Windows.ContentDeliveryManager_cw5n1h2txyewy\LocalState\Assets'
$desdir = $HOME + '\Desktop\spotlight'
$index = 1

# Create direction
Remove-Item -Path $desdir -Recurse -ErrorAction Ignore
New-Item -Path $desdir -ItemType Directory -Force

# Copy
Copy-Item ($dir + '\*') $desdir

# Change files' name
Get-ChildItem $desdir | ForEach-Object {Rename-Item $_.FullName -NewName ('P{0:d3}.jpg' -f $index); $index++}
