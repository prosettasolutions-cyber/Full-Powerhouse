$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$launcherPath = Join-Path $repoRoot "start-ritu-background.ps1"
$powershellPath = Join-Path $PSHOME "powershell.exe"
$shell = New-Object -ComObject WScript.Shell

$startupFolder = [Environment]::GetFolderPath("Startup")
$desktopFolder = [Environment]::GetFolderPath("Desktop")

$startupShortcut = $shell.CreateShortcut((Join-Path $startupFolder "Ritu AI Backend.lnk"))
$startupShortcut.TargetPath = $powershellPath
$startupShortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$launcherPath`" -Watch"
$startupShortcut.WorkingDirectory = $repoRoot
$startupShortcut.Description = "Starts and monitors the local Ritu AI backend"
$startupShortcut.IconLocation = "$env:SystemRoot\System32\shell32.dll,13"
$startupShortcut.Save()

$portalShortcut = $shell.CreateShortcut((Join-Path $desktopFolder "Ritu Portal.lnk"))
$portalShortcut.TargetPath = $powershellPath
$portalShortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$launcherPath`" -OpenPortal"
$portalShortcut.WorkingDirectory = $repoRoot
$portalShortcut.Description = "Starts Ritu when needed and opens the local portal"
$portalShortcut.IconLocation = "$env:SystemRoot\System32\shell32.dll,14"
$portalShortcut.Save()

Write-Output "STARTUP_SHORTCUT=$($startupShortcut.FullName)"
Write-Output "DESKTOP_SHORTCUT=$($portalShortcut.FullName)"
