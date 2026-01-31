#!/usr/bin/env pwsh
#===============================================================================
# FeatherTrace Windows Deployment Script
#===============================================================================

$ProgressPreference = "SilentlyContinue"

$PROJECT_ROOT = Split-Path -Parent $PSScriptRoot
$GITEE_MIRROR = "https://gitee.com/jiangyuyi/feather-trace.git"
$GITHUB_ORIGIN = "https://github.com/jiangyuyi/feather-trace.git"
$PIP_MIRROR = "https://pypi.tuna.tsinghua.edu.cn/simple"

$COLORS = @{
    RED     = "Red"
    GREEN   = "Green"
    YELLOW  = "Yellow"
    CYAN    = "Cyan"
    WHITE   = "White"
    GRAY    = "Gray"
}

function Test-Command {
    param([string]$Name)
    try {
        Get-Command $Name -ErrorAction Stop | Out-Null
        return $true
    } catch { return $false }
}

function Ensure-Directory {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function Read-Input {
    param([string]$Prompt, [string]$Default)
    if ($Default) {
        $result = Read-Host "$Prompt [$Default]"
        if ([string]::IsNullOrWhiteSpace($result)) { return $Default }
        return $result.Trim()
    }
    return (Read-Host $Prompt).Trim()
}

function Read-YesNo {
    param([string]$Prompt, [string]$Default = "y")
    while ($true) {
        $suffix = if ($Default -eq "y") { "[Y/n]" } else { "[y/N]" }
        $answer = Read-Host "$Prompt $suffix"
        if ([string]::IsNullOrWhiteSpace($answer)) { $answer = $Default }
        $answer = $answer.ToLower()
        if ($answer -eq "y" -or $answer -eq "yes") { return $true }
        if ($answer -eq "n" -or $answer -eq "no") { return $false }
    }
}

function Pause-Host {
    Write-Host "Press Enter to continue..." -ForegroundColor Gray
    Read-Host
}

function Log-Info   { Write-Host "[INFO]   $($args[0])" -ForegroundColor $COLORS.GREEN }
function Log-Warn   { Write-Host "[WARN]   $($args[0])" -ForegroundColor $COLORS.YELLOW }
function Log-Error  { Write-Host "[ERROR]  $($args[0])" -ForegroundColor $COLORS.RED }
function Log-Step   { Write-Host "[STEP]   $($args[0])" -ForegroundColor $COLORS.CYAN }
function Log-Success{ Write-Host "[OK]     $($args[0])" -ForegroundColor $COLORS.GREEN }

function Test-Git {
    if (Test-Command "git") {
        Log-Info "Git installed: $(git --version)"
        return $true
    }
    Log-Warn "Git not found"
    return $false
}

function Test-Python {
    foreach ($cmd in @("python3", "python")) {
        if (Test-Command $cmd) {
            try {
                $version = & $cmd --version 2>&1 | Out-String
                if ($version -match "Python (\d+)\.(\d+)") {
                    $major = [int]$Matches[1]
                    $minor = [int]$Matches[2]
                    if ($major -eq 3 -and $minor -ge 8) {
                        Log-Info "Python installed: $version".Trim()
                        $script:PYTHON_CMD = $cmd
                        return $true
                    }
                }
            } catch { }
        }
    }
    Log-Warn "Python 3.8+ not found"
    return $false
}

function Test-ExifTool {
    if (Test-Command "exiftool") {
        Log-Info "ExifTool installed: $(exiftool -ver)"
        return $true
    }
    Log-Warn "ExifTool not found"
    return $false
}

function Test-GPU {
    if (Test-Command "nvidia-smi") {
        try {
            $gpu = nvidia-smi --query-gpu=name --format=csv,noheader 2>&1 | Select-Object -First 1
            if ($gpu) {
                Log-Info "GPU detected: $gpu"
                $script:HAS_GPU = $true
                return $true
            }
        } catch { }
    }
    Log-Warn "No NVIDIA GPU detected, will use CPU"
    $script:HAS_GPU = $false
    return $false
}

function Install-Git {
    Log-Step "Installing Git..."
    if (Test-Command "winget") {
        Log-Info "Using winget..."
        winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) { Log-Success "Git installed"; return $true }
    }
    if (Test-Command "scoop") {
        Log-Info "Using scoop..."
        scoop install git 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) { Log-Success "Git installed"; return $true }
    }
    if (Test-Command "choco") {
        Log-Info "Using choco..."
        choco install git -y 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) { Log-Success "Git installed"; return $true }
    }
    Log-Error "Cannot install Git automatically. Download: https://git-scm.com/download/win"
    return $false
}

function Install-Python {
    Log-Step "Installing Python 3.11..."
    if (Test-Command "winget") {
        winget install --id Python.Python.3.11 -e --source winget --accept-package-agreements --accept-source-agreements 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) { Log-Success "Python installed (restart terminal)"; return $true }
    }
    if (Test-Command "scoop") {
        scoop install python311 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) { Log-Success "Python installed"; return $true }
    }
    if (Test-Command "choco") {
        choco install python311 -y 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) { Log-Success "Python installed"; return $true }
    }
    Log-Error "Cannot install Python automatically. Download: https://www.python.org/downloads/"
    return $false
}

function Install-ExifTool {
    Log-Step "Installing ExifTool..."
    if (Test-Command "winget") {
        winget install --id PhilHarvey.ExifTool -e --source winget --accept-package-agreements --accept-source-agreements 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) { Log-Success "ExifTool installed"; return $true }
    }
    if (Test-Command "scoop") {
        scoop install exiftool 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) { Log-Success "ExifTool installed"; return $true }
    }
    if (Test-Command "choco") {
        choco install exiftool -y 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) { Log-Success "ExifTool installed"; return $true }
    }
    Log-Error "Cannot install ExifTool automatically. Download: https://exiftool.org/"
    return $false
}

function Install-AllDependencies {
    Log-Step "Installing system dependencies..."
    $failed = $false
    if (-not (Test-Git)) {
        if (Read-YesNo "Install Git?") { if (-not (Install-Git)) { $failed = $true } } else { $failed = $true }
    }
    if (-not (Test-Python)) {
        if (Read-YesNo "Install Python?") { if (-not (Install-Python)) { $failed = $true } } else { $failed = $true }
    }
    if (-not (Test-ExifTool)) {
        if (Read-YesNo "Install ExifTool?") { if (-not (Install-ExifTool)) { $failed = $true } }
    }
    if (-not $failed) { Log-Success "All dependencies installed"; return $true }
    Log-Warn "Some dependencies failed to install"
    return $false
}

function Get-Project {
    Log-Step "Getting project..."

    # 检查是否是 git 仓库
    if (Test-Path "$PROJECT_ROOT\.git") {
        Log-Info "Git repository found"

        # 获取当前远程 URL
        $remoteUrl = git -C $PROJECT_ROOT remote get-url origin 2>$null

        # 如果是 GitHub，直接切换到 Gitee（不测试连通性，避免超时）
        if ($remoteUrl -and $remoteUrl.Contains("github.com")) {
            Log-Info "Switching remote to Gitee mirror..."
            git -C $PROJECT_ROOT remote set-url origin $GITEE_MIRROR 2>&1 | Out-Null
        }

        Log-Info "Updating project..."
        $pullResult = git -C $PROJECT_ROOT pull origin master 2>&1 | Out-String
        if ($LASTEXITCODE -eq 0) {
            Log-Success "Project updated"
            return $true
        }
        else {
            Log-Warn "Update failed, using existing files"
            return $true
        }
    }

    # 检查是否有项目文件
    if (Test-Path "$PROJECT_ROOT\settings.yaml") {
        Log-Success "Project files found"
        return $true
    }

    # 检查目录是否非空（排除脚本文件）
    $items = Get-ChildItem -Path $PROJECT_ROOT -Force | Where-Object {
        $_.Name -ne ".git" -and $_.Name -ne "deploy.ps1" -and
        $_.Name -ne "Deploy.bat" -and $_.Name -ne "deploy.sh"
    }
    if ($items) {
        Log-Warn "Directory not empty, using existing files"
        return $true
    }

    # 优先从 Gitee 克隆（国内访问快）
    Log-Info "Cloning from Gitee..."
    $null = git clone --depth 1 $GITEE_MIRROR $PROJECT_ROOT 2>&1
    if ($LASTEXITCODE -eq 0 -or (Test-Path "$PROJECT_ROOT\settings.yaml")) {
        Log-Success "Cloned from Gitee"
        return $true
    }

    # Gitee 失败则尝试 GitHub
    Log-Info "Trying GitHub..."
    $null = git clone --depth 1 $GITHUB_ORIGIN $PROJECT_ROOT 2>&1
    if ($LASTEXITCODE -eq 0) {
        Log-Success "Cloned from GitHub"
        return $true
    }

    Log-Error "Clone failed"
    return $false
}

function Install-PythonDependencies {
    Log-Step "Installing Python dependencies..."

    if (-not (Test-Python)) { Log-Error "Python not found"; return $false }
    $venvPath = "$PROJECT_ROOT\venv"

    # 创建虚拟环境
    if (-not (Test-Path "$venvPath\Scripts\python.exe")) {
        Log-Info "Creating virtual environment..."
        $createResult = python -m venv $venvPath
        if ($LASTEXITCODE -ne 0) {
            Log-Error "Failed to create virtual environment"
            return $false
        }
    }

    $pythonVenv = "$venvPath\Scripts\python.exe"

    # 配置 pip 镜像
    Log-Info "Configuring pip mirror..."
    & $pythonVenv -m pip config set global.index-url $PIP_MIRROR 2>&1 | Out-Null

    # 升级 pip
    Log-Info "Upgrading pip..."
    & $pythonVenv -m pip install --upgrade pip 2>&1 | Out-Null

    # 安装依赖
    Log-Info "Installing requirements.txt..."
    & $pythonVenv -m pip install -r "$PROJECT_ROOT\requirements.txt" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Log-Success "Python dependencies installed"
        return $true
    }

    # 失败重试
    Log-Warn "First attempt failed, retrying..."
    & $pythonVenv -m pip install -r "$PROJECT_ROOT\requirements.txt" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Log-Success "Python dependencies installed (retry)"
        return $true
    }

    Log-Error "Failed to install Python dependencies"
    return $false
}

function Invoke-ConfigWizard {
    Log-Step "Configuring project..."
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  Configuration Wizard" -ForegroundColor White
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""

    Write-Host "  1/3 Photo source directory" -ForegroundColor Cyan
    Write-Host "  Enter the directory containing your bird photos" -ForegroundColor Gray
    Write-Host "  Format: Year/yyyymmdd_Location/*.jpg" -ForegroundColor Gray
    Write-Host ""
    $sourceDir = Read-Input "Photo directory" "$env:USERPROFILE\Pictures"
    if (-not (Test-Path $sourceDir)) {
        if (Read-YesNo "Directory does not exist, create it?") { Ensure-Directory -Path $sourceDir; Log-Success "Created: $sourceDir" }
    }

    Write-Host ""
    Write-Host "  2/3 Output directory" -ForegroundColor Cyan
    $outputDir = Read-Input "Output directory" "$PROJECT_ROOT\data\processed"
    Ensure-Directory -Path $outputDir

    Write-Host ""
    Write-Host "  3/3 Processing device" -ForegroundColor Cyan
    Test-GPU
    if ($script:HAS_GPU) {
        Write-Host "  GPU detected, CUDA recommended" -ForegroundColor Green
        $device = Read-Input "Device (auto/cuda/cpu)" "auto"
    } else {
        Write-Host "  No GPU detected, will use CPU" -ForegroundColor Yellow
        $device = "cpu"
    }

    Write-Host ""
    Log-Step "Generating config files..."

    $configPath = "$PROJECT_ROOT\config\settings.yaml"
    Ensure-Directory -Path (Split-Path $configPath)

    $lines = @()
    $lines += "# FeatherTrace config"
    $lines += "# Generated by deploy script"
    $lines += ""
    $lines += "paths:"
    $lines += "  allowed_roots:"
    $lines += "    - ""$($sourceDir.Replace('\', '/'))"""
    $lines += "  references_path: ""data/references"""
    $lines += "  sources:"
    $lines += "    - path: ""$($sourceDir.Replace('\', '/'))"""
    $lines += "      recursive: true"
    $lines += "      enabled: true"
    $lines += "  output:"
    $lines += "    root_dir: ""$($outputDir.Replace('\', '/'))"""
    $lines += "    structure_template: ""{source_structure}/{filename}_{species_cn}_{confidence}"""
    $lines += "    write_back_to_source: false"
    $lines += "  db_path: ""data/db/feathertrace.db"""
    $lines += "  ioc_list_path: ""data/references/Multiling IOC 15.1_d.xlsx"""
    $lines += "  model_cache_dir: ""data/models"""
    $lines += "processing:"
    $lines += "  device: ""$device"""
    $lines += "  yolo_model: ""yolov8n.pt"""
    $lines += "  confidence_threshold: 0.5"
    $lines += "  blur_threshold: 40.0"
    $lines += "  target_size: 640"
    $lines += "  crop_padding: 200"
    $lines += "recognition:"
    $lines += "  mode: ""local"""
    $lines += "  region_filter: ""auto"""
    $lines += "  top_k: 5"
    $lines += "  alternatives_threshold: 70"
    $lines += "  low_confidence_threshold: 60"
    $lines += "  local:"
    $lines += "    model_type: ""bioclip-2"""
    $lines += "    batch_size: 512"
    $lines += "    inference_batch_size: 16"
    $lines += "web:"
    $lines += "  host: ""0.0.0.0"""
    $lines += "  port: 8000"

    $lines | Out-File -FilePath $configPath -Encoding UTF8
    Log-Success "Config generated: $configPath"

    $secretsPath = "$PROJECT_ROOT\config\secrets.yaml"
    if (-not (Test-Path $secretsPath)) {
        @"
# FeatherTrace secrets
hf_api_key: ""
dongniao_api_key: ""
"@ | Out-File -FilePath $secretsPath -Encoding UTF8
        Log-Success "Secrets generated: $secretsPath"
    }

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  Configuration Summary" -ForegroundColor White
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  Source: $sourceDir" -ForegroundColor White
    Write-Host "  Output: $outputDir" -ForegroundColor White
    Write-Host "  Device: $device" -ForegroundColor White
    Write-Host "----------------------------------------" -ForegroundColor Cyan
    Write-Host "  Done!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    return $true
}

function Start-WebServer {
    Log-Step "Starting Web server..."
    $venvPython = "$PROJECT_ROOT\venv\Scripts\python.exe"
    $webScript = "$PROJECT_ROOT\src\web\app.py"

    if (-not (Test-Path $venvPython)) {
        Log-Error "Virtual environment not found!"
        Log-Info "Please run [1] Start Deployment first"
        Write-Host ""
        Write-Host "Press Enter to continue..." -ForegroundColor Gray
        Read-Host
        return $false
    }

    if (-not (Test-Path $webScript)) {
        Log-Error "Web script not found: $webScript"
        Write-Host ""
        Write-Host "Press Enter to continue..." -ForegroundColor Gray
        Read-Host
        return $false
    }

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  Starting Web server..." -ForegroundColor Green
    Write-Host "  URL: http://localhost:8000" -ForegroundColor White
    Write-Host "  Press Ctrl+C to stop" -ForegroundColor Gray
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""

    # 启动服务
    & $venvPython $webScript
    $exitCode = $LASTEXITCODE

    # 服务退出
    Write-Host ""
    Log-Warn "Web server stopped (exit code: $exitCode)"
    Write-Host ""
    Write-Host "Press Enter to return to menu..." -ForegroundColor Gray
    Read-Host
    return $true
}

function Show-Menu {
    Clear-Host
    Write-Host ""
    Write-Host "  ========================================  " -ForegroundColor Cyan
    Write-Host "  FeatherTrace Deployment" -ForegroundColor Cyan -NoNewline
    Write-Host "  AI Bird Photo Management" -ForegroundColor Gray
    Write-Host "  ========================================  " -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  [1] Start Deployment" -ForegroundColor White
    Write-Host "  [2] Configuration" -ForegroundColor White
    Write-Host "  [3] Update Project" -ForegroundColor White
    Write-Host "  [4] Start Service" -ForegroundColor White
    Write-Host "  [5] Help" -ForegroundColor White
    Write-Host "  [6] Exit" -ForegroundColor White
    Write-Host ""
    Write-Host "  ========================================  " -ForegroundColor Cyan
}

function Invoke-Main {
    $script:PYTHON_CMD = $null
    $script:HAS_GPU = $false
    while ($true) {
        Show-Menu
        $choice = Read-Host "Enter option (1-6)"
        Write-Host ""
        switch ($choice) {
            "1" {
                Write-Host "========================================" -ForegroundColor Cyan
                Write-Host "  Deployment" -ForegroundColor Green
                Write-Host "========================================" -ForegroundColor Cyan
                Write-Host ""
                Install-AllDependencies
                Get-Project
                Install-PythonDependencies
                Invoke-ConfigWizard
                Write-Host ""
                Log-Success "Deployment complete!"
                Write-Host ""
                Write-Host "  Next: Select [4] to start service, open http://localhost:8000" -ForegroundColor Gray
                Write-Host ""
                Pause-Host
            }
            "2" { Invoke-ConfigWizard; Pause-Host }
            "3" { Get-Project; Pause-Host }
            "4" { Start-WebServer }
            "5" {
                Clear-Host
                Write-Host ""
                Write-Host "  Help" -ForegroundColor Cyan
                Write-Host ""
                Write-Host "  Features:" -ForegroundColor White
                Write-Host "    - YOLOv8 bird detection" -ForegroundColor Gray
                Write-Host "    - BioCLIP species recognition" -ForegroundColor Gray
                Write-Host "    - EXIF metadata injection" -ForegroundColor Gray
                Write-Host "    - Web interface management" -ForegroundColor Gray
                Write-Host ""
                Write-Host "  Quick Start:" -ForegroundColor White
                Write-Host "    1. Select [1] Start Deployment" -ForegroundColor Gray
                Write-Host "    2. Configure photo directory" -ForegroundColor Gray
                Write-Host "    3. Select [4] Start Service" -ForegroundColor Gray
                Write-Host ""
                Write-Host "  Format: Year/yyyymmdd_Location/*.jpg" -ForegroundColor Gray
                Write-Host ""
                Write-Host "  GitHub: https://github.com/jiangyuyi/feather-trace" -ForegroundColor Gray
                Write-Host ""
                Pause-Host
            }
            "6" { Write-Host ""; Write-Host "  Goodbye!"; Write-Host ""; exit 0 }
            default { Log-Error "Invalid option"; Start-Sleep -Seconds 1 }
        }
    }
}

try { Invoke-Main } catch {
    Log-Error "Error: $_"
    Write-Host ""
    Write-Host "Press Enter to exit..." -ForegroundColor Gray
    Read-Host
    exit 1
}
