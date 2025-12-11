; GetFileHash 安装程序脚本
; 使用 Inno Setup 编译

#define MyAppName "GetFileHash"
#define MyAppVersion "0.0.1"
#define MyAppPublisher "pengcunfu"
#define MyAppURL "https://github.com/pengcunfu/GetFileHash"
#define MyAppExeName "GetFileHash.exe"

[Setup]
; 应用程序基本信息
AppId={{8E2F5B3C-1A2B-4C5D-9E6F-7A8B9C0D1E2F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
AppCopyright=Copyright (C) 2025 {#MyAppPublisher}

; 默认安装目录
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}

; 安装程序设置
Compression=lzma2/max
SolidCompression=yes
OutputDir=..\installer
OutputBaseFilename=GetFileHash-Setup-{#MyAppVersion}
; SetupIconFile=..\resources\icon.png

; 现代化UI
WizardStyle=modern
; WizardImageFile=resources\installer-image.bmp
; WizardSmallImageFile=resources\installer-small.bmp
ShowLanguageDialog=yes

; 权限要求
PrivilegesRequired=admin

; 64位和32位支持
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; OnlyBelowVersion: 6.1; Flags: unchecked

[Files]
; 主程序文件
Source: "..\dist\main.dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; 依赖库文件（如果存在）
Source: "..\dist\main.dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; 开始菜单图标
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Comment: "哈希值计算工具"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"

; 桌面图标
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\{#MyAppExeName}"; Comment: "哈希值计算工具"

; 快速启动栏图标
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon; IconFilename: "{app}\{#MyAppExeName}"; Comment: "哈希值计算工具"

[Registry]
; 注册应用程序信息
Root: "HKLM"; Subkey: "Software\{#MyAppName}"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"
Root: "HKLM"; Subkey: "Software\{#MyAppName}"; ValueType: string; ValueName: "Version"; ValueData: "{#MyAppVersion}"
Root: "HKLM"; Subkey: "Software\{#MyAppName}"; ValueType: string; ValueName: "Publisher"; ValueData: "{#MyAppPublisher}"

[Run]
; 安装完成后运行程序
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; 卸载时删除用户数据目录（可选）
Type: filesandordirs; Name: "{userappdata}\{#MyAppName}"

[Code]
// 安装前检查
function InitializeSetup(): Boolean;
begin
  Result := True;
  // 可以在这里添加系统要求检查
end;

// 安装完成后显示消息
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // 可以在这里添加安装后配置
  end;
end;