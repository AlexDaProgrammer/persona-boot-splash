' Plays the startup splash with no console window.
Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")
root = fso.GetParentFolderName(fso.GetParentFolderName(WScript.ScriptFullName))
py = shell.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\Programs\Thonny\pythonw.exe"
If Not fso.FileExists(py) Then py = "pythonw"
shell.Run """" & py & """ """ & root & "\src\boot_animation.pyw""", 0, False
