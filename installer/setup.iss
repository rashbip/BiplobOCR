; BiplobOCR Installer Script for Inno Setup
; Requires Inno Setup 6.0 or later
; Download from: https://jrsoftware.org/isinfo.php

#define MyAppName "BiplobOCR"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "BiplobOCR Team"
#define MyAppURL "https://github.com/rashbip/BiplobOCR"
#define MyAppExeName "run.py"
#define MyAppMainScript "src\main.py"

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
AppId={{BF3E9A5C-4D2E-4F1A-9B3C-8E7D6F5A4C3B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
; License file
LicenseFile=LICENSE.txt
; Output
OutputDir=output
OutputBaseFilename=BiplobOCR-Setup-{#MyAppVersion}
; Icon
SetupIconFile=..\src\assets\icon.ico
UninstallDisplayIcon={app}\src\assets\icon.ico
; Compression
Compression=lzma2/max
SolidCompression=yes
; Windows version
MinVersion=6.1sp1
; Architecture
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
; Privileges
PrivilegesRequired=admin
; UI
WizardStyle=modern
DisableProgramGroupPage=yes
DisableWelcomePage=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startmenu"; Description: "Create Start Menu shortcut"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce
Name: "quicklaunch"; Description: "Create Quick Launch shortcut"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Main application files
Source: "..\src\*"; DestDir: "{app}\src"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\run.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\requirements.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion isreadme

; Python installer helper
Source: "python_installer.py"; DestDir: "{app}\installer"; Flags: ignoreversion

; Exclude cache and temp files
Source: "..\src\*"; DestDir: "{app}\src"; Excludes: "__pycache__,*.pyc,*.pyo,*.log,*_temp,config.json,history.json"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Start Menu
Name: "{group}\{#MyAppName}"; Filename: "pythonw.exe"; Parameters: """{app}\{#MyAppExeName}"""; WorkingDir: "{app}"; IconFilename: "{app}\src\assets\icon.ico"; Tasks: startmenu
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"; Tasks: startmenu

; Desktop
Name: "{autodesktop}\{#MyAppName}"; Filename: "pythonw.exe"; Parameters: """{app}\{#MyAppExeName}"""; WorkingDir: "{app}"; IconFilename: "{app}\src\assets\icon.ico"; Tasks: desktopicon

; Quick Launch
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "pythonw.exe"; Parameters: """{app}\{#MyAppExeName}"""; WorkingDir: "{app}"; IconFilename: "{app}\src\assets\icon.ico"; Tasks: quicklaunch

[Run]
; Run Python installer wizard
Filename: "python"; Parameters: """{app}\installer\python_installer.py"""; StatusMsg: "Setting up Python environment..."; Flags: runhidden waituntilterminated

; Option to launch after install
Filename: "pythonw.exe"; Parameters: """{app}\{#MyAppExeName}"""; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up temp files, cache, and configs on uninstall
Type: filesandordirs; Name: "{app}\src\__pycache__"
Type: filesandordirs; Name: "{app}\src\core\__pycache__"
Type: filesandordirs; Name: "{app}\src\gui\__pycache__"
Type: filesandordirs; Name: "{app}\_biplob_temp"
Type: files; Name: "{app}\*.log"
Type: files; Name: "{app}\config.json"
Type: files; Name: "{app}\history.json"

[Code]
var
  PythonCheckPage: TOutputMsgWizardPage;
  PythonFound: Boolean;

function CheckPythonInstalled(): Boolean;
var
  ResultCode: Integer;
begin
  Result := False;
  
  // Try python command
  if Exec('python', '--version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
  begin
    if ResultCode = 0 then
    begin
      Result := True;
      Exit;
    end;
  end;
  
  // Try python3 command
  if Exec('python3', '--version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
  begin
    if ResultCode = 0 then
    begin
      Result := True;
      Exit;
    end;
  end;
  
  // Try py launcher
  if Exec('py', '--version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
  begin
    if ResultCode = 0 then
    begin
      Result := True;
      Exit;
    end;
  end;
end;

function InitializeSetup(): Boolean;
begin
  Result := True;
  PythonFound := CheckPythonInstalled();
end;

procedure InitializeWizard();
begin
  // Create a page to show Python status  
  if PythonFound then
  begin
    PythonCheckPage := CreateOutputMsgPage(wpWelcome,
      'Python Environment Check',
      'Python Found!',
      'Python is already installed on your system.' + #13#10 + 
      'The installer will verify and install required packages.');
  end
  else
  begin
    PythonCheckPage := CreateOutputMsgPage(wpWelcome,
      'Python Environment Check',
      'Python Not Found',
      'Python was not detected on your system.' + #13#10 +
      'After installation completes, you will be guided through Python setup.');
  end;
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  Result := '';
  NeedsRestart := False;
  
  // Additional pre-installation checks can go here
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Post-installation tasks
    // The Python installer will run via [Run] section
  end;
end;

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := False;
  
  // Custom page skipping logic can go here
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  // Custom page change handling
  if CurPageID = PythonCheckPage.ID then
  begin
    // Refresh Python check when reaching this page
    PythonFound := CheckPythonInstalled();
  end;
end;
