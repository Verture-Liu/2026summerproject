#ifndef AppSource
  #define AppSource "..\..\..\build\windows\app"
#endif
#ifndef OutputDir
  #define OutputDir "..\..\..\dist"
#endif

[Setup]
AppId={{C0ACAA8A-8912-4D59-81CA-24A363E584B8}
AppName=PaleoRigor
AppVersion=0.2.0-dev
AppPublisher=PaleoRigor research project
DefaultDirName={localappdata}\Programs\PaleoRigor
DefaultGroupName=PaleoRigor
OutputDir={#OutputDir}
OutputBaseFilename=PaleoRigor-Setup
Compression=lzma2/ultra64
SolidCompression=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
Uninstallable=yes
DisableProgramGroupPage=yes
WizardStyle=modern
LicenseFile={#AppSource}\backend\_internal\research_agent\tools\licenses\README.md

[Files]
Source: "{#AppSource}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\PaleoRigor"; Filename: "{app}\PaleoRigor.exe"
Name: "{autodesktop}\PaleoRigor"; Filename: "{app}\PaleoRigor.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Run]
Filename: "{app}\PaleoRigor.exe"; Description: "Launch PaleoRigor"; Flags: nowait postinstall skipifsilent
