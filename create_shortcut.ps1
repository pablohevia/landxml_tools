$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("C:\Users\Pablo\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Mis programas\LandXML Tools.lnk")
$Shortcut.TargetPath = "e:\GitHub\landxml_tools\LandXML Tools.bat"
$Shortcut.WindowStyle = 7
$Shortcut.IconLocation = "C:\Users\Pablo\.conda\envs\geo_interp\python.exe,0"
$Shortcut.Description = "LandXML Tools"
$Shortcut.WorkingDirectory = "e:\GitHub\landxml_tools"
$Shortcut.Save()
