# Only for an ephemeral GitHub Actions Windows runner, never a user's installed app.
param([Parameter(Mandatory=$true)][string]$Artifacts)
$ErrorActionPreference = 'Stop'
if ($env:GITHUB_ACTIONS -ne 'true') { throw 'Installer lifecycle test is restricted to ephemeral GitHub Actions runners.' }
$Target = Join-Path $env:RUNNER_TEMP 'FaceMatchInstallerQA'
if (Test-Path $Target) { throw 'Installer test target already exists.' }
$Setup = Join-Path $Artifacts 'FaceMatch-Setup-Windows-x64.exe'
$Install = Start-Process -FilePath $Setup -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/SP-',"/DIR=`"$Target`"") -Wait -PassThru
if ($Install.ExitCode -ne 0) { throw "Installer failed: $($Install.ExitCode)" }
$Report = Join-Path $Artifacts 'installed-smoke.json'
$App = Join-Path $Target 'FaceMatch.exe'
$Run = Start-Process -FilePath $App -ArgumentList @('--smoke-test',"`"$Report`"") -Wait -PassThru
if ($Run.ExitCode -ne 0 -or -not (Test-Path $Report)) { throw 'Installed executable smoke check failed.' }
$MarkerDir = Join-Path $env:LOCALAPPDATA 'FaceMatch'
New-Item -ItemType Directory -Path $MarkerDir -Force | Out-Null
$Marker = Join-Path $MarkerDir 'installer-preservation-marker.txt'
if (Test-Path $Marker) { throw 'Preservation marker already exists.' }
Set-Content -Path $Marker -Value 'disposable CI preservation fixture'
$Uninstaller = Join-Path $Target 'unins000.exe'
$Uninstall = Start-Process -FilePath $Uninstaller -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART') -Wait -PassThru
if ($Uninstall.ExitCode -ne 0 -or -not (Test-Path $Marker)) { throw 'Uninstall failed or removed user-data fixture.' }
@{ installation='passed';installed_backend='passed';uninstall_keeps_user_data='passed';interactive_gui='not tested' } | ConvertTo-Json | Set-Content (Join-Path $Artifacts 'installer-check.json')
