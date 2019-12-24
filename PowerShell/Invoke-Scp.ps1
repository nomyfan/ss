<#
-------------------------
Copy file between remote server and local machine using scp.
Write down your servers first, then feel free to copy file any time.
================
❗❗❗ATTENTION❗❗❗
================
Put the servers.json file into PATH or make the variable absolute path.
-------------------------
Example: Invoke-Scp -LocalPath ./ -Operation Fetch
Example: Invoke-Scp -LocalPath ./config.json -Operation Push
#>
# function Invoke-Scp {  
    Param (
        # [CmdletBinding()]
        [Parameter(Mandatory = $false)]
        [Alias("p")]
        [string]$LocalPath = ".",
        [Parameter(Mandatory = $true)]
        [ValidateSet("Fetch","Push")]
        [Alias("o")]
        [string]$Operation,
        [Parameter(Mandatory = $false)]
        [string]$ServersJsonPath = "servers.json"
    )
    $servers = @{}
    (Get-Content -Path $ServersJsonPath | ConvertFrom-Json).servers | ForEach-Object { $servers[$_.name] = $_ }

    if ($servers.Keys.Count -ne 0) {
        $serverName = Read-Host -Prompt (-Join "select target server (", $servers.Keys, ")")
        $defaultPath = -Join ("/home/",$servers.$serverName.user )
        $serverPath = Read-Host -Prompt (-Join ("input server path(default:",$defaultPath,")"))
    
        if ($serverPath -eq "") {
            $serverPath = $defaultPath
        }
    
        $server =  (-Join ($servers.$serverName.user,"@",$servers.$serverName.ip))
        $serverPath = (-Join ($server, ":", $serverPath))
    
        if ($Operation -eq "Push") {
            scp -P $servers.$serverName.port $LocalPath $serverPath
        }
        else {
            scp -P $servers.$serverName.port $serverPath $LocalPath
        }
    }
# }
