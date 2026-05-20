Set WshShell = CreateObject("WScript.Shell")
appDir = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\"))

' Kill old server on port 8080
WshShell.Run "cmd /c for /f ""tokens=5"" %a in ('netstat -aon ^| find "":8080"" ^| find ""LISTENING""') do taskkill /f /pid %a", 0, True

' Start Flask silently
WshShell.Run "cmd /c cd /d """ & appDir & """ && python app.py", 0, False

' Wait 6 seconds for server to start
WScript.Sleep 6000

' Open browser
WshShell.Run "http://localhost:8080"
