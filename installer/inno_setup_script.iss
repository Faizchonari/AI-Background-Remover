; Inno Setup 6 Script for AI Background Remover
; Builds standard Windows Installer (.exe) for Windows 11 64-bit

#define MyAppName "AI Background Remover"
#define MyAppVersion "1.1.0"
#define MyAppPublisher "LocalAI"
#define MyAppURL "https://github.com/Faizchonari/AI-Background-Remover"
#define MyAppExeName "AI Background Remover.exe"

[Setup]
AppId={{E68A9A48-7E9E-4DC7-8854-A619FDFB6291}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=..\LICENSE
OutputDir=..\release
OutputBaseFilename=AI-Background-Remover-Setup
SetupIconFile=..\assets\app_icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Dirs]
; Required application folders; model_storage preserves downloaded models across updates & uninstall
Name: "{app}\model_storage"; Flags: uninsneveruninstall
Name: "{app}\output"
Name: "{app}\input"
Name: "{app}\config"
Name: "{app}\logs"

[Files]
; Application binaries and runtime from PyInstaller dist
Source: "..\dist\AI-Background-Remover\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Default configuration (only copy if not already existing so user settings persist across updates)
Source: "..\config\*"; DestDir: "{app}\config"; Flags: onlyifdoesntexist recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\app_icon.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\app_icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
