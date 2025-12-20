' BiplobOCR Silent Launcher
' Runs Python without showing console window

Set WshShell = CreateObject("WScript.Shell")
strPath = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
strRoot = CreateObject("Scripting.FileSystemObject").GetParentFolderName(CreateObject("Scripting.FileSystemObject").GetParentFolderName(strPath))
WshShell.CurrentDirectory = strRoot
WshShell.Run "python """ & strRoot & "\run.py""", 0, False
