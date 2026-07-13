; SubSync Fork — Inno Setup installer script
; Build: iscc resources\installer.iss  (from the repo root)

[Setup]
AppName=SubSync
AppVersion=0.19.4
AppPublisher=SubSync Fork
AppCopyright=GNU GPL v3.0
LicenseFile=..\LICENSE
DefaultDirName={autopf}\subsync
DefaultGroupName=SubSync
OutputBaseFilename=subsync-0.19.4-setup
OutputDir=..\dist
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayName=SubSync (Fork)

[Files]
Source: "..\dist\subsync\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\SubSync";          Filename: "{app}\subsync.exe";       WorkingDir: "{app}"
Name: "{group}\SubSync (headless)"; Filename: "{app}\subsync-cmd.exe";  WorkingDir: "{app}"
Name: "{group}\Uninstall";         Filename: "{uninstallexe}"
Name: "{commondesktop}\SubSync";    Filename: "{app}\subsync.exe";       WorkingDir: "{app}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"
