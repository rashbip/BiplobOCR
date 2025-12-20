' BiplobOCR Silent Launcher
' Runs Python without showing console window

Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

strPath = fso.GetParentFolderName(WScript.ScriptFullName)
strRoot = fso.GetParentFolderName(fso.GetParentFolderName(strPath))
WshShell.CurrentDirectory = strRoot

bundledPython = strRoot & "\src\python\windows\pythonw.exe"

If fso.FileExists(bundledPython) Then
    WshShell.Run """" & bundledPython & """ """ & strRoot & "\run.py""", 0, False
Else
    WshShell.Run "pythonw """ & strRoot & "\run.py""", 0, False
End If
