; Build with scripts/build_windows.ps1. Requires Inno Setup 6.6 or newer.
#ifndef SourceDir
  #error SourceDir must point to the frozen application directory.
#endif
#ifndef AssetsDir
  #error AssetsDir must point to generated installer assets.
#endif
#ifndef OutputDir
  #error OutputDir is required.
#endif
#ifndef AppVersion
  #error AppVersion is required.
#endif

[Setup]
AppId={{EA2DF9C6-5DC1-4CC3-913B-DB87DB5D0B5E}
AppName=DICOMVision
AppVersion={#AppVersion}
AppPublisher=Jun Liu
VersionInfoVersion={#AppVersion}
DefaultDirName={localappdata}\Programs\DICOMVision
DefaultGroupName=DICOMVision
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
WizardStyle=modern dynamic
DisableWelcomePage=no
DisableDirPage=no
DisableProgramGroupPage=yes
SetupIconFile={#AssetsDir}\app.ico
WizardSmallImageFile={#AssetsDir}\wizard-logo.png
UninstallDisplayIcon={app}\DICOMVision.exe
InfoBeforeFile=install-notes.txt
OutputDir={#OutputDir}
OutputBaseFilename=DICOMVision-{#AppVersion}-windows-x64-setup
Compression=lzma2
SolidCompression=yes
CloseApplications=yes
RestartApplications=no
ShowLanguageDialog=auto

[Languages]
Name: "en"; MessagesFile: "compiler:Default.isl"
Name: "zh"; MessagesFile: "compiler:Default.isl,ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:DesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\DICOMVision"; Filename: "{app}\DICOMVision.exe"
Name: "{autodesktop}\DICOMVision"; Filename: "{app}\DICOMVision.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\DICOMVision.exe"; Description: "{cm:LaunchApp}"; Flags: nowait postinstall skipifsilent

[CustomMessages]
en.DesktopIcon=Create a desktop shortcut
zh.DesktopIcon=创建桌面快捷方式
en.AdditionalIcons=Shortcuts:
zh.AdditionalIcons=快捷方式：
en.LaunchApp=Launch DICOMVision
zh.LaunchApp=启动 DICOMVision

; No wildcard uninstall cleanup: never remove user DICOM files, logs or settings.
