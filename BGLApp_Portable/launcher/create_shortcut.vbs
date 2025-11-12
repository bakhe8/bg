' BGLApp Portable - Create Desktop Shortcut
Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")
Set EnvVars = WshShell.Environment("PROCESS")
silentMode = LCase(EnvVars("BGLAPP_SHORTCUT_SILENT")) = "1"

currentDir = Replace(WScript.ScriptFullName, WScript.ScriptName, "")
desktopPath = WshShell.SpecialFolders("Desktop")
Set shortcut = WshShell.CreateShortcut(desktopPath & "\BGLApp Portable.lnk")
shortcut.TargetPath = currentDir & "run_portable.bat"
shortcut.WorkingDirectory = currentDir
shortcut.IconLocation = currentDir & "icon.ico"
shortcut.Description = "BGLApp Portable - نظام خطابات الضمان البنكية"
shortcut.WindowStyle = 7
shortcut.Save

If silentMode Then
    WScript.Quit
End If

result = MsgBox("✅ تم إنشاء أيقونة BGLApp Portable على سطح المكتب بنجاح!" & vbCrLf & vbCrLf & _
    "يمكنك الآن تشغيل التطبيق بنقرة واحدة من الأيقونة الجديدة." & vbCrLf & vbCrLf & _
    "هل تريد تشغيل التطبيق الآن؟", vbYesNo + vbInformation, "BGLApp Portable")
If result = vbYes Then
    WshShell.Run Chr(34) & currentDir & "run_portable.bat" & Chr(34), 0, False
End If
