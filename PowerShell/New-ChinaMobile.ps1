param (
    [Parameter(Mandatory = $false)]
    [uint32]$Total,
    [Parameter(Mandatory = $false)]
    [uint32]$Unicom,
    [Parameter(Mandatory = $false)]
    [uint32]$Telecom,
    [Parameter(Mandatory = $false)]
    [uint32]$Mobile
)

$providerJson = '{"telecom":["133","149","153","162","173","177","180","181","189","190","191","193","199"],"unicom":["130","131","132","145","155","156","166","175","176","185","186","196"],"mobile":["135","136","137","138","139","147","150","151","152","157","158","159","172","178","182","183","184","187","188","195","197","198"]}'

$providers = (ConvertFrom-Json -InputObject $providerJson).psobject.properties

if (($Unicom + $Telecom + $Mobile) -eq 0) {
    if($Total -eq 0) {
        Write-Error -Message "Please specify how many mobile numbers do you want to generate using -Total"
        return
    }
    $Unicom = $Total / 3
    $Telecom = $Total / 3
    $Mobile = $Total - $Unicom - $Telecom
} else {
    $Total = $Unicom + $Telecom + $Mobile
}

$result = @(
    @{
        "Name"    = "Unicom"
        "Total"   = $Unicom
        "Numbers" = @()
    },
    @{
        "Name"    = "Telecom"
        "Total"   = $Telecom
        "Numbers" = @()
    },
    @{
        "Name"    = "Mobile"
        "Total"   = $Mobile
        "Numbers" = @()
    }
)

$result | ForEach-Object {
    $prefixes = $providers[$_.Name].Value
    for ($i = 0; $i -lt $_.Total; $i = $i + 1) {
        $idx = Get-Random -Minimum 0 -Maximum $prefixes.Length
        $prefix = $prefixes[$idx].ToString()
        $secondPart = "{0:d4}" -f (Get-Random -Minimum 0 -Maximum 10000)
        $thirdPart = "{0:d4}" -f (Get-Random -Minimum 0 -Maximum 10000)
        $tel = $prefix + $secondPart + $thirdPart
        $_.Numbers += $tel
    }
}

[PSCustomObject]$result