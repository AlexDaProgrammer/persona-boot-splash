' Cycles the splash mode: Auto, Dark Hour, Persona 5, Normal.
Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")
root = fso.GetParentFolderName(fso.GetParentFolderName(WScript.ScriptFullName))
py = shell.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\Programs\Thonny\pythonw.exe"
If Not fso.FileExists(py) Then py = "pythonw"
shell.Run """" & py & """ """ & root & "\src\toggle_mode.pyw""", 0, False
