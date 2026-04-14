Set WshShell = CreateObject("WScript.Shell")

' Get the directory where the script is located
strPath = "C:\Users\thora\.gemini\antigravity\scratch\jarvis"
WshShell.CurrentDirectory = strPath

' Start Server silently (0 = Hidden)
WshShell.Run "pythonw server.py", 0, False

' Wait 2 seconds for server to start
WScript.Sleep 2000

' Start Wake Word silently (0 = Hidden)
WshShell.Run "pythonw wakeword.py", 0, False

' Start IP Prime Frontend Server (Vite)
WshShell.CurrentDirectory = strPath & "\frontend"
WshShell.Run "cmd /c npm run dev", 0, False

' Wait 3 seconds for Vite server to start
WScript.Sleep 3000

' Start IP Prime Desktop App (Hidden Terminal)
WshShell.Run "cmd /c npm run desktop", 0, False
