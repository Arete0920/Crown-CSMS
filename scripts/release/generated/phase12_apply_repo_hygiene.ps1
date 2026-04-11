param(
    [switch]$ApplyRemoteDeletes,
    [switch]$ApplyLocalDeletes
)

$ErrorActionPreference = "Stop"

$remoteCommands = @(

)

$localCommands = @(

)

if ($ApplyRemoteDeletes) {
    foreach ($cmd in $remoteCommands) {
        cmd /c $cmd
    }
}

if ($ApplyLocalDeletes) {
    foreach ($cmd in $localCommands) {
        cmd /c $cmd
    }
}
