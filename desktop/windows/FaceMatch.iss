#ifndef BundleDir
  #error BundleDir is required
#endif
#ifndef OutputDir
  #error OutputDir is required
#endif
#ifndef WebViewBootstrapper
  #error WebViewBootstrapper is required
#endif
[Setup]
AppId={{EF41FA82-7627-4789-934B-A2D4C862725B}
AppName=FaceMatch
AppVersion=1.2.0
AppPublisher=FaceMatch Academic Prototype
DefaultDirName={localappdata}\Programs\FaceMatch
DefaultGroupName=FaceMatch
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.22000
OutputDir={#OutputDir}
OutputBaseFilename=FaceMatch-Setup-Windows-x64
Compression=lzma2
SolidCompression=yes
UninstallDisplayIcon={app}\FaceMatch.exe
SetupIconFile={#BundleDir}\..\..\FaceMatch.ico
WizardStyle=modern

[Messages]
WelcomeLabel2=This installs FaceMatch for your Windows account. Photos and records remain local. Internet is needed for missing WebView2 components and first-use model downloads. The application is an academic prototype, not proof of identity.

[Tasks]
Name: desktopicon; Description: "Create a Desktop shortcut"; GroupDescription: "Shortcuts:"; Flags: unchecked

[Files]
Source: "{#BundleDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#WebViewBootstrapper}"; DestDir: "{tmp}"; Flags: deleteafterinstall

[Icons]
Name: "{autoprograms}\FaceMatch"; Filename: "{app}\FaceMatch.exe"
Name: "{autodesktop}\FaceMatch"; Filename: "{app}\FaceMatch.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\FaceMatch.exe"; Description: "Open FaceMatch"; Flags: nowait postinstall skipifsilent

[Code]
function HasWebView2: Boolean;
var Version: String;
begin
  Result := (RegQueryStringValue(HKLM32, 'SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', Version) and (Version <> '') and (Version <> '0.0.0.0'));
  if not Result then
    Result := (RegQueryStringValue(HKCU, 'Software\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', Version) and (Version <> '') and (Version <> '0.0.0.0'));
end;

function HasVisualCRuntime: Boolean;
var Installed: Cardinal;
begin
  Result := RegQueryDWordValue(HKLM64, 'SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64', 'Installed', Installed) and (Installed = 1) and FileExists(ExpandConstant('{sys}\vcruntime140_1.dll'));
end;

function InitializeSetup: Boolean;
var Code: Integer;
begin
  Result := HasVisualCRuntime;
  if not Result then
  begin
    if MsgBox('FaceMatch needs the Microsoft Visual C++ x64 runtime for its recognition engine. Install the latest x64 runtime from Microsoft, then run FaceMatch Setup again. Open the official Microsoft instructions now?', mbInformation, MB_YESNO) = IDYES then
      ShellExec('open', 'https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist', '', '', SW_SHOWNORMAL, ewNoWait, Code);
  end;
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var Code: Integer;
begin
  Result := '';
  if not HasWebView2 then
  begin
    ExtractTemporaryFile('MicrosoftEdgeWebview2Setup.exe');
    if not Exec(ExpandConstant('{tmp}\MicrosoftEdgeWebview2Setup.exe'), '/silent /install', '', SW_HIDE, ewWaitUntilTerminated, Code) then
      Result := 'Microsoft WebView2 could not start. Check your internet connection and try again.'
    else if not HasWebView2 then
      Result := 'Microsoft WebView2 is required. Install it from Microsoft, then run FaceMatch Setup again.';
  end;
end;

; Intentionally no UninstallDelete rule for %LOCALAPPDATA%\FaceMatch.
; Removing the program must not silently delete enrolled photos or records.
