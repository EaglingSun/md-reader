; Inno Setup script for AI_docs reader (formerly md-reader).
; Per-user install (no admin), .md association, "Open with" entries for code/data files,
; Start Menu, optional desktop icon.
; Compile via packaging\build.ps1 (preferred) or:
;   "%LocalAppData%\Programs\Inno Setup 6\ISCC.exe" packaging\installer.iss
;
; Names: AppName is what users see; AppFileName is the space-free name for files.
; Version / name must match app/main.py (APP_VERSION / APP_NAME) — tests/test_packaging.py checks.

#define AppName        "AI_docs reader"
#define AppFileName    "ai-docs-reader"
#define AppVersion     "1.4.1"
#define AppPublisher   "EaglingSun"
#define AppExeName     "ai-docs-reader.exe"
; Same AppId as md-reader v1.x — a new AppId would install side by side instead of upgrading.
#define AppId          "{{8F1F9B9E-1A2B-4C3D-9E8F-7A6B5C4D3E2F}"
; md-reader v1.0 ~ v1.3.1 names, cleaned up or re-pointed on upgrade.
#define OldAppName     "md-reader"
#define OldExeName     "md-reader.exe"
; ProgID key names stay (only their display text changes) so existing associations keep working.
#define ProgIdMarkdown "MdReader.MarkdownFile"
#define ProgIdText     "MdReader.TextFile"

[Setup]
AppId={#AppId}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppVerName={#AppName} {#AppVersion}
; Upgrades keep the previous folder (UsePreviousAppDir default) — md-reader installs stay in ...\Programs\md-reader.
DefaultDirName={localappdata}\Programs\{#AppFileName}
DefaultGroupName={#AppName}
; Don't reuse the old "md-reader" Start Menu folder; [InstallDelete] removes it.
UsePreviousGroup=no
DisableProgramGroupPage=yes
DisableDirPage=auto
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=..\dist\installer
OutputBaseFilename={#AppFileName}-setup-{#AppVersion}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
SetupIconFile=..\app\assets\icon.ico
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName}
; Tell Explorer to refresh association caches after install/uninstall.
ChangesAssociations=yes

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
; md-reader v1.x leftovers: old exe (its _internal is gone above), Start Menu folder, desktop icon.
Type: files; Name: "{app}\{#OldExeName}"
Type: filesandordirs; Name: "{autoprograms}\{#OldAppName}"
Type: files; Name: "{userdesktop}\{#OldAppName}.lnk"

[Files]
; PyInstaller produces dist/ai-docs-reader/* - we ingest the whole folder.
Source: "..\dist\{#AppFileName}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\samples\sample.md"; DestDir: "{app}\samples"; Flags: ignoreversion
Source: "..\LICENSE"; DestDir: "{app}"; DestName: "LICENSE.txt"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{userdesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Registry]
; --- .md / .markdown (installer task "associatemd") ---
Root: HKCU; Subkey: "Software\Classes\{#ProgIdMarkdown}"; \
    ValueType: string; ValueName: ""; ValueData: "Markdown Document ({#AppName})"; \
    Flags: uninsdeletekey; Tasks: associatemd
Root: HKCU; Subkey: "Software\Classes\{#ProgIdMarkdown}\DefaultIcon"; \
    ValueType: string; ValueName: ""; ValueData: "{app}\{#AppExeName},0"; \
    Flags: uninsdeletekey; Tasks: associatemd
Root: HKCU; Subkey: "Software\Classes\{#ProgIdMarkdown}\shell\open\command"; \
    ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExeName}"" ""%1"""; \
    Flags: uninsdeletekey; Tasks: associatemd
Root: HKCU; Subkey: "Software\Classes\.md\OpenWithProgids"; \
    ValueType: string; ValueName: "{#ProgIdMarkdown}"; ValueData: ""; \
    Flags: uninsdeletevalue; Tasks: associatemd
Root: HKCU; Subkey: "Software\Classes\.markdown\OpenWithProgids"; \
    ValueType: string; ValueName: "{#ProgIdMarkdown}"; ValueData: ""; \
    Flags: uninsdeletevalue; Tasks: associatemd

; --- Code / data files: listed in "Open with" only. The default app is never changed
;     (a .py double-click still runs Python). Extension list = app/main.py CODE_FENCE_LANGS.
Root: HKCU; Subkey: "Software\Classes\{#ProgIdText}"; \
    ValueType: string; ValueName: ""; ValueData: "Text Document ({#AppName})"; \
    Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\{#ProgIdText}\DefaultIcon"; \
    ValueType: string; ValueName: ""; ValueData: "{app}\{#AppExeName},0"; \
    Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\{#ProgIdText}\shell\open\command"; \
    ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExeName}"" ""%1"""; \
    Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\.py\OpenWithProgids"; ValueType: string; ValueName: "{#ProgIdText}"; ValueData: ""; Flags: uninsdeletevalue
Root: HKCU; Subkey: "Software\Classes\.c\OpenWithProgids"; ValueType: string; ValueName: "{#ProgIdText}"; ValueData: ""; Flags: uninsdeletevalue
Root: HKCU; Subkey: "Software\Classes\.h\OpenWithProgids"; ValueType: string; ValueName: "{#ProgIdText}"; ValueData: ""; Flags: uninsdeletevalue
Root: HKCU; Subkey: "Software\Classes\.patch\OpenWithProgids"; ValueType: string; ValueName: "{#ProgIdText}"; ValueData: ""; Flags: uninsdeletevalue
Root: HKCU; Subkey: "Software\Classes\.diff\OpenWithProgids"; ValueType: string; ValueName: "{#ProgIdText}"; ValueData: ""; Flags: uninsdeletevalue
Root: HKCU; Subkey: "Software\Classes\.json\OpenWithProgids"; ValueType: string; ValueName: "{#ProgIdText}"; ValueData: ""; Flags: uninsdeletevalue
Root: HKCU; Subkey: "Software\Classes\.yml\OpenWithProgids"; ValueType: string; ValueName: "{#ProgIdText}"; ValueData: ""; Flags: uninsdeletevalue
Root: HKCU; Subkey: "Software\Classes\.yaml\OpenWithProgids"; ValueType: string; ValueName: "{#ProgIdText}"; ValueData: ""; Flags: uninsdeletevalue
Root: HKCU; Subkey: "Software\Classes\.txt\OpenWithProgids"; ValueType: string; ValueName: "{#ProgIdText}"; ValueData: ""; Flags: uninsdeletevalue
Root: HKCU; Subkey: "Software\Classes\.ps1\OpenWithProgids"; ValueType: string; ValueName: "{#ProgIdText}"; ValueData: ""; Flags: uninsdeletevalue
Root: HKCU; Subkey: "Software\Classes\.sh\OpenWithProgids"; ValueType: string; ValueName: "{#ProgIdText}"; ValueData: ""; Flags: uninsdeletevalue
Root: HKCU; Subkey: "Software\Classes\.js\OpenWithProgids"; ValueType: string; ValueName: "{#ProgIdText}"; ValueData: ""; Flags: uninsdeletevalue
Root: HKCU; Subkey: "Software\Classes\.toml\OpenWithProgids"; ValueType: string; ValueName: "{#ProgIdText}"; ValueData: ""; Flags: uninsdeletevalue
Root: HKCU; Subkey: "Software\Classes\.ini\OpenWithProgids"; ValueType: string; ValueName: "{#ProgIdText}"; ValueData: ""; Flags: uninsdeletevalue
Root: HKCU; Subkey: "Software\Classes\.log\OpenWithProgids"; ValueType: string; ValueName: "{#ProgIdText}"; ValueData: ""; Flags: uninsdeletevalue

; --- Application registration (controls "Open with" display name + icon) ---
Root: HKCU; Subkey: "Software\Classes\Applications\{#AppExeName}"; \
    ValueType: string; ValueName: "FriendlyAppName"; ValueData: "{#AppName}"; \
    Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\Applications\{#AppExeName}\DefaultIcon"; \
    ValueType: string; ValueName: ""; ValueData: "{app}\{#AppExeName},0"; \
    Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\Applications\{#AppExeName}\shell\open\command"; \
    ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExeName}"" ""%1"""; \
    Flags: uninsdeletekey

; --- md-reader v1.x: Applications\md-reader.exe may be some extension's default app
;     (UserChoice, e.g. .txt). Deleting it would break that double-click, so re-point it at
;     the new exe and hide it from "Open with" (no duplicate entry). Only when it already existed.
Root: HKCU; Subkey: "Software\Classes\Applications\{#OldExeName}"; \
    ValueType: string; ValueName: "FriendlyAppName"; ValueData: "{#AppName}"; \
    Flags: deletekey uninsdeletekey; Check: HadOldExeKey
Root: HKCU; Subkey: "Software\Classes\Applications\{#OldExeName}"; \
    ValueType: string; ValueName: "NoOpenWith"; ValueData: ""; \
    Flags: uninsdeletekey; Check: HadOldExeKey
Root: HKCU; Subkey: "Software\Classes\Applications\{#OldExeName}\DefaultIcon"; \
    ValueType: string; ValueName: ""; ValueData: "{app}\{#AppExeName},0"; \
    Flags: uninsdeletekey; Check: HadOldExeKey
Root: HKCU; Subkey: "Software\Classes\Applications\{#OldExeName}\shell\open\command"; \
    ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExeName}"" ""%1"""; \
    Flags: uninsdeletekey; Check: HadOldExeKey

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch {#AppName}"; \
    Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up any stray runtime files
Type: filesandordirs; Name: "{app}"

[Code]
var
  OldExeKeyExisted: Boolean;

function InitializeSetup(): Boolean;
begin
  { Decide once, before any [Registry] entry runs (the first one recreates the key). }
  OldExeKeyExisted := RegKeyExists(HKEY_CURRENT_USER, 'Software\Classes\Applications\{#OldExeName}');
  Result := True;
end;

function HadOldExeKey(): Boolean;
begin
  Result := OldExeKeyExisted;
end;
