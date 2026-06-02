; ============================================================
;  KlickTime installer  (compile with Inno Setup -> KlickTimeSetup.exe)
;  Prerequisite: build dist\KlickTime.exe first (run build_KlickTime.bat)
; ============================================================

#define AppName     "KlickTime"
#define AppVersion  "1.0.0"
#define Publisher   "Klickevents Infosolutions Pvt Ltd"
#define ServerUrl   "https://tt.klickevents.in"

[Setup]
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#Publisher}
AppPublisherURL=https://klickevents.in
DefaultDirName={localappdata}\KlickTime
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputBaseFilename=KlickTimeSetup
OutputDir=.
SetupIconFile=ke.ico
UninstallDisplayIcon={app}\KlickTime.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Files]
Source: "dist\KlickTime.exe"; DestDir: "{app}"; Flags: ignoreversion

[Tasks]
Name: "autostart";  Description: "Start KlickTime automatically when I sign in to Windows"; Flags: checkedonce
Name: "sharedmode"; Description: "This computer is shared by multiple employees (shift mode)"; Flags: unchecked
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked

[Icons]
Name: "{autostartmenu}\Programs\KlickTime"; Filename: "{app}\KlickTime.exe"
Name: "{userdesktop}\KlickTime"; Filename: "{app}\KlickTime.exe"; Tasks: desktopicon

[Registry]
; Auto-start for the signed-in user (no admin rights needed)
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; \
    ValueType: string; ValueName: "KlickTime"; ValueData: """{app}\KlickTime.exe"""; \
    Tasks: autostart; Flags: uninsdeletevalue

[Run]
Filename: "{app}\KlickTime.exe"; Description: "Launch KlickTime now"; \
    Flags: nowait postinstall skipifsilent

[Code]
{ Write config.json after install, choosing mode from the checkbox. }
procedure CurStepChanged(CurStep: TSetupStep);
var
  Mode, Content: string;
begin
  if CurStep = ssPostInstall then
  begin
    if WizardIsTaskSelected('sharedmode') then
      Mode := 'shared'
    else
      Mode := 'dedicated';
    Content := '{' + #13#10 +
               '  "server_url": "{#ServerUrl}",' + #13#10 +
               '  "mode": "' + Mode + '"' + #13#10 +
               '}';
    SaveStringToFile(ExpandConstant('{app}\config.json'), Content, False);
  end;
end;
