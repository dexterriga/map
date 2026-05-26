Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\DEXTER\Desktop\party_map_daugavpils_bot"
WshShell.Run "cmd.exe /c venv\Scripts\activate.bat && python -m bot.main", 0, False
