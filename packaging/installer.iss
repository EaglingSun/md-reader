; Inno Setup script for md-reader.
; Per-user install (no admin), .md association, Start Menu, optional desktop icon.
; Compile via packaging\build.ps1 (preferred) or:
;   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" packaging\installer.iss

#define AppName        "md-reader"
#define AppVersion     "1.3.1"
#define AppPublisher   "EaglingSun"
#define AppExeName     "md-reader.exe"
#define AppId          "{{8F1F9B9E-1A2B-4C3D-9E8F-7A6B5C4D3E2F}"

[Setup]
AppId={#AppId}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppVerName={#AppName} {#AppVersion}
DefaultDirName={localappdata}\Programs\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
DisableDirPage=auto
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=..\dist\installer
OutputBaseFilename={#AppName}-setup-{#AppVersion}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
SetupIconFile=..\app\assets\icon.ico
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "korean";  MessagesFile: "compiler:Languages\Korean.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "associatemd"; Description: "Associate .md and .markdown files with {#AppName}"; GroupDescription: "File associations:";

[InstallDelete]
; Upgrade in place: re-running a newer installer over an existing install (same AppId)
; reuses {app}. Inno only overwrites files, so wipe the previous PyInstaller bundle
; first - otherwise DLLs/modules dropped in the new build would linger in _internal.
Type: filesandordirs; Name: "{app}\_internal"

[Files]
; PyInstaller produces dist/md-reader/* - we ingest the whole folder.
Source: "..\dist\md-reader\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\samples\sample.md"; DestDir: "{app}\samples"; Flags: ignoreversion
Source: "..\LICENSE"; DestDir: "{app}"; DestName: "LICENSE.txt"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{userdesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Registry]
; ProgID
Root: HKCU; Subkey: "Software\Classes\MdReader.MarkdownFile"; \
    ValueType: string; ValueName: ""; ValueData: "Markdown Document ({#AppName})"; \
    Flags: uninsdeletekey; Tasks: associatemd
Root: HKCU; Subkey: "Software\Classes\MdReader.MarkdownFile\DefaultIcon"; \
    ValueType: string; ValueName: ""; ValueData: "{app}\{#AppExeName},0"; \
    Flags: uninsdeletekey; Tasks: associatemd
Root: HKCU; Subkey: "Software\Classes\MdReader.MarkdownFile\shell\open\command"; \
    ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExeName}"" ""%1"""; \
    Flags: uninsdeletekey; Tasks: associatemd

; Application registration (controls "Open with" display name + icon)
Root: HKCU; Subkey: "Software\Classes\Applications\{#AppExeName}"; \
    ValueType: string; ValueName: "FriendlyAppName"; ValueData: "{#AppName}"; \
    Flags: uninsdeletevalue
Root: HKCU; Subkey: "Software\Classes\Applications\{#AppExeName}\DefaultIcon"; \
    ValueType: string; ValueName: ""; ValueData: "{app}\{#AppExeName},0"; \
    Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\Applications\{#AppExeName}\shell\open\command"; \
    ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExeName}"" ""%1"""; \
    Flags: uninsdeletekey

; Add ProgId to .md / .markdown OpenWithProgIds
Root: HKCU; Subkey: "Software\Classes\.md\OpenWithProgIds"; \
    ValueType: string; ValueName: "MdReader.MarkdownFile"; ValueData: ""; \
    Flags: uninsdeletevalue; Tasks: associatemd
Root: HKCU; Subkey: "Software\Classes\.markdown\OpenWithProgIds"; \
    ValueType: string; ValueName: "MdReader.MarkdownFile"; ValueData: ""; \
    Flags: uninsdeletevalue; Tasks: associatemd

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch {#AppName}"; \
    Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up any stray runtime files
Type: filesandordirs; Name: "{app}"
