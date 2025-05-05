$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\AMF Motorsports.lnk")
$Shortcut.TargetPath = "$PSScriptRoot\start_amf.bat"
$Shortcut.WorkingDirectory = "$PSScriptRoot"
$Shortcut.IconLocation = "$PSScriptRoot\app\static\img\icon.png"
$Shortcut.Save()
