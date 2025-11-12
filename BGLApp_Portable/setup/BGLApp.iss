; Inno Setup script for BGLApp Portable
#define MyAppName \"BGLApp Portable\"
#define MyAppVersion \"1.0.0\"
#define MyAppPublisher \"BGLApp\"
#define MyAppExe \"launcher\\run_portable.bat\"
#define SourceDir \"..\\dist\\BGLApp_Portable\"

[Setup]
AppId={{4C9C9D94-96F3-45B3-A5E9-0AE169B45B8D}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={pf}\\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..
OutputBaseFilename={#MyAppName}_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\\launcher\\icon.ico

[Languages]
Name: \"arabic\"; MessagesFile: \"compiler:Languages\\Arabic.isl\"
Name: \"english\"; MessagesFile: \"compiler:Default.isl\"

[Files]
Source: \"{#SourceDir}\\*\"; DestDir: \"{app}\"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: \"{autoprograms}\\{#MyAppName}\"; Filename: \"{app}\\{#MyAppExe}\"; WorkingDir: \"{app}\"
Name: \"{autodesktop}\\{#MyAppName}\"; Filename: \"{app}\\{#MyAppExe}\"; WorkingDir: \"{app}\"

[Run]
Filename: \"{app}\\{#MyAppExe}\"; Description: \"تشغيل التطبيق\"; Flags: nowait postinstall skipifsilent
