<#
-------------------------
Copy file between remote server and local machine using scp.
Write down your servers first, then feel free to copy file any time.
-------------------------
Example: CC -LocalPath ./ -Operation Fetch
Example: CC -LocalPath ./config.json -Operation Push
#>
# function CC {  
    Param (
        # [CmdletBinding()]
        [Parameter(Mandatory = $true)][string]$LocalPath,
        [Parameter(Mandatory = $true)][ValidateSet("Fetch","Push")][string]$Operation
    )
    $servers = @{
        server1 = @{
            port = 2333
            user = "username"
            ip = "127.0.0.1"
        }
        server2 = @{
            port = 5555
            user = "username"
            ip = "127.0.0.1"
        }
    }

    $serverName = Read-Host -Prompt (-Join "select target server (", $servers.Keys, ")")
    $defaultPath = -Join ("/home/",$servers[$serverName]["user"] )
    $serverPath = Read-Host -Prompt (-Join ("input server path(default:",$defaultPath,")"))

    if ($serverPath -eq "") {
        $serverPath = $defaultPath
    }

    $server =  (-Join ($servers[$serverName]["user"],"@",$servers[$serverName]["ip"]))
    $serverPath = (-Join ($server, ":", $serverPath))

    if ($Operation -eq "Push") {
        scp -P $servers[$serverName]["port"] $LocalPath $serverPath
    }
    else {
        scp -P $servers[$serverName]["port"] $serverPath $LocalPath
    }
# }
