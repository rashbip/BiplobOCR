' BiplobOCR Silent Launcher
' Runs Python without showing console window

Set WshShell = CreateObject("WScript.Shell")
strPath = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = strPath
WshShell.Run "pythonw """ & strPath & "\run.py""", 0, False
