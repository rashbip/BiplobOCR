; BiplobOCR Installer Script for Inno Setup
; A simple, self-contained installer that uses the bundled Python environment.

#define MyAppName "BiplobOCR"
#define MyAppVersion "3.3"
#define MyAppPublisher "Rashidul Hasan Biplob"
#define MyAppURL "https://github.com/rashbip/BiplobOCR"
#define MyAppExeName "BiplobOCR.vbs"

[Setup]
AppId={{BF3E9A5C-4D2E-4F1A-9B3C-8E7D6F5A4C3B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={userdocs}\{#MyAppName}
DefaultGroupName={#MyAppName}
LicenseFile=LICENSE.txt
OutputDir=output
OutputBaseFilename=BiplobOCR-Setup-{#MyAppVersion}
SetupIconFile=..\..\..\src\assets\icon.ico
UninstallDisplayIcon={app}\src\assets\icon.ico
Compression=lzma2/max
SolidCompression=yes
MinVersion=6.1sp1
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
WizardStyle=modern
DisableProgramGroupPage=yes
DisableWelcomePage=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Copy everything from project root, excluding noise
; Excludes: dev files, other platforms, temp, cache, tests, docs
Source: "..\..\..\*"; DestDir: "{app}"; Excludes: ".git*,.vscode,.agent,.idea,*.log,config.json,history.json,platforms\linux,platforms\macos,platforms\windows\installer\output\*,src\python\temp_extract,src\python\*.zip,src\tesseract\linux,src\tesseract\macos,tests,*.md,*.spec,biplob_ocr_old.py,test_*.py,**\__pycache__\*,**\*.pyc,**\*.pyo,**\*.pdb,**\*.lib"; Flags: ignoreversion recursesubdirs createallsubdirs


[Icons]
; Start Menu
Name: "{group}\{#MyAppName}"; Filename: "wscript.exe"; Parameters: """{app}\platforms\windows\BiplobOCR.vbs"""; WorkingDir: "{app}"; IconFilename: "{app}\src\assets\icon.ico"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"

; Desktop
Name: "{autodesktop}\{#MyAppName}"; Filename: "wscript.exe"; Parameters: """{app}\platforms\windows\BiplobOCR.vbs"""; WorkingDir: "{app}"; IconFilename: "{app}\src\assets\icon.ico"; Tasks: desktopicon

[Run]
; Launch after install
Filename: "wscript.exe"; Parameters: """{app}\platforms\windows\BiplobOCR.vbs"""; WorkingDir: "{app}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\src\__pycache__"
Type: filesandordirs; Name: "{app}\_biplob_temp"
Type: files; Name: "{app}\*.log"
Type: files; Name: "{app}\config.json"
Type: files; Name: "{app}\history.json"
