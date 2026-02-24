param(
    [string]$PythonExe = "python",
    [string]$AppPath = ""
)

if ([string]::IsNullOrWhiteSpace($AppPath)) {
    $AppPath = Join-Path (Split-Path -Parent $PSScriptRoot) "transcriber_app\transcribe_gui.py"
}

$resolvedApp = (Resolve-Path $AppPath).Path
$command = '"' + $PythonExe + '" "' + $resolvedApp + '" --file "%1"'

$baseKey = "Registry::HKEY_CURRENT_USER\Software\Classes\*\shell\TranscribeWithLocalWhisper"
New-Item -Path $baseKey -Force | Out-Null
Set-ItemProperty -Path $baseKey -Name "MUIVerb" -Value "Transcribe audio to text"
Set-ItemProperty -Path $baseKey -Name "Icon" -Value "imageres.dll,-5302"

$commandKey = Join-Path $baseKey "command"
New-Item -Path $commandKey -Force | Out-Null
Set-ItemProperty -Path $commandKey -Name "(default)" -Value $command

Write-Host "Installed context menu command: $command"
