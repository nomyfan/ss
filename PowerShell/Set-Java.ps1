function Get-Java {
    $hasJava = Test-Path 'C:\Program Files\Java' -PathType Container
    $versions = Get-Item 'C:\Program Files\Java\*'
    if ($hasJava -and $versions.Length -gt 0) {
        $map = @{ }
        $versions | ForEach-Object {
            if ($_.Name -like 'jdk1.8*') {
                $map.Add('Java(8)', $_.FullName)
            }
            elseif ($_.Name -like 'jdk11.*') {
                $map.Add('Java(11)', $_.FullName)
            }
        }
        
        return $map
    }
    else {
        Write-Host 'Cannot find any version Java installed.'
        return @{ }
    }
}

function Set-Java {
    $javas = Get-Java

    if ($javas.Count -gt 0) {
        Write-Host 'Java installed:' -BackgroundColor Red
        $javas.Keys | ForEach-Object {
            Write-Host $_
        }
    
        if (0 -ne $env:JAVA_HOME.Length) {
            Write-Host
            Write-Host 'Current Java information: ' -BackgroundColor DarkGreen
            & ($env:JAVA_HOME + '\bin\java.exe') '-version'
        }
    
        Write-Host
        $choice = (Read-Host -Prompt ('Which version of Java do you want to switch on? ' + ($javas.Keys -join ' or ')))
    
        # Change JAVA_HOME env
        # Replace Java bin path in env:Path
        $java = $javas.Item('Java(' + $choice + ')')
        $env:JAVA_HOME = $java
        $env:Path = (($env:Path -split ';' | Where-Object { $_ -notlike '*Program Files\Java\jdk*' }) + ($java + '\bin')) -join ';'
    
        Write-Host 'Now Java information: ' -BackgroundColor DarkRed
        & ($env:JAVA_HOME + '\bin\java.exe') '-version'
    }
}

Set-Java