# Registers the splash to start the moment you sign in, skipping Windows' startup-app delay.
# Run "Remove sign-in splash.cmd" to undo.
param([switch]$Remove)
$name = "Boot Splash"
if ($Remove) {
    Unregister-ScheduledTask -TaskName $name -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "Removed the sign-in splash task."
    exit 0
}
$src    = Join-Path (Split-Path $PSScriptRoot -Parent) "src"
$python = Join-Path $env:LOCALAPPDATA "Programs\Thonny\pythonw.exe"
if (-not (Test-Path $python)) { $python = (Get-Command pythonw -ErrorAction Stop).Source }
$user   = "$env:USERDOMAIN\$env:USERNAME"
$action    = New-ScheduledTaskAction -Execute $python -Argument "`"$src\boot_animation.pyw`"" -WorkingDirectory $src
$trigger   = New-ScheduledTaskTrigger -AtLogOn -User $user
$settings  = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
             -ExecutionTimeLimit (New-TimeSpan -Minutes 1) -Priority 4 -MultipleInstances IgnoreNew
$principal = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName $name -Action $action -Trigger $trigger -Settings $settings `
    -Principal $principal -Force -ErrorAction Stop | Out-Null
Write-Host "Done. The splash will now start as soon as you sign in."
