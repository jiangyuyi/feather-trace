#!/bin/bash
#===============================================================================
# WingScribe 一键部署脚本 - Linux/macOS/WSL
#===============================================================================

# 立即退出管道失败
set -o pipefail

# 确保在项目根目录运行
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$(dirname "${SCRIPT_DIR}")" && pwd)"

# 检测是否支持颜色
detect_color_support() {
    # 如果用户明确要求禁用颜色
    if [ -n "$NO_COLOR" ] || [ "$TERM" = "dumb" ]; then
        return 1
    fi

    # 检查终端类型
    case "$TERM" in
        xterm*|xterm-color|linux|screen|screen-256color|vt100|ansi|cygwin|msys)
            return 0
            ;;
    esac

    # 检查是否在交互式终端中运行
    if [ -t 1 ]; then
        return 0
    fi

    return 1
}

# 启用或禁用颜色
if detect_color_support; then
    # 颜色定义
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    CYAN='\033[0;36m'
    WHITE='\033[1;37m'
    GRAY='\033[0;90m'
    NC='\033[0m'
else
    # 禁用颜色
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    CYAN=''
    WHITE=''
    GRAY=''
    NC=''
fi

# 配置变量
GITEE_MIRROR="https://gitee.com/jiangyuyi/wingscribe.git"
GITHUB_ORIGIN="https://github.com/jiangyuyi/wingscribe.git"
PIP_MIRROR="https://pypi.tuna.tsinghua.edu.cn/simple"
HF_MIRROR="https://hf-mirror.com"
PROXY=""
PYTHON_CMD=""
HAS_GPU=false
DEVICE="auto"

#===============================================================================
# 工具函数
#===============================================================================

log_info()   { printf "${GREEN}[INFO]${NC} %s\n" "$1"; }
log_warn()   { printf "${YELLOW}[WARN]${NC} %s\n" "$1"; }
log_error()  { printf "${RED}[ERROR]${NC} %s\n" "$1" >&2; }
log_step()   { printf "${CYAN}[STEP]${NC} %s\n" "$1"; }
log_success(){ printf "${GREEN}[OK]${NC} %s\n" "$1"; }

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

get_os_type() {
    case "$(uname -s)" in
        Linux*)     echo "linux";;
        Darwin*)    echo "macos";;
        CYGWIN*|MINGW*|MSYS*) echo "windows";;
        *)          echo "unknown";;
    esac
}

is_windows() { [ "$(get_os_type)" = "windows" ]; }
is_macos()   { [ "$(get_os_type)" = "macos" ]; }
is_linux()   { [ "$(get_os_type)" = "linux" ]; }

pause() {
    printf "${GRAY}按 Enter 继续...${NC}\n"
    read -r
}

ask_input() {
    local prompt="$1"
    local default="${2:-}"
    local result

    if [ -n "$default" ]; then
        printf "${CYAN}%s${NC} [%s]: " "$prompt" "$default"
        read -r result
        echo "${result:-$default}"
    else
        printf "${CYAN}%s${NC}: " "$prompt"
        read -r result
        echo "$result"
    fi
}

ask_yes_no() {
    local prompt="$1"
    local default="${2:-y}"

    while true; do
        local answer
        local suffix
        if [ "$default" = "y" ]; then
            suffix="[Y/n]"
        else
            suffix="[y/N]"
        fi
        printf "${CYAN}%s ${suffix}: " "$prompt"
        read -r answer

        answer=$(echo "$answer" | tr '[:upper:]' '[:lower:]' | tr -d '[:space:]')
        [ -z "$answer" ] && answer="$default"

        case "$answer" in
            y|yes) return 0 ;;
            n|no)  return 1 ;;
        esac
    done
}

#===============================================================================
# 检测函数
#===============================================================================

test_git() {
    if command_exists git; then
        local version=$(git --version | grep -oE '[0-9]+\.[0-9]+' | head -1)
        log_info "Git installed: $version"
        return 0
    fi
    log_warn "Git not found"
    return 1
}

test_python() {
    for cmd in python3 python; do
        if command_exists "$cmd"; then
            local version=$($cmd --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
            local major=$($cmd -c "import sys; print(sys.version_info.major)" 2>/dev/null)
            local minor=$($cmd -c "import sys; print(sys.version_info.minor)" 2>/dev/null)

            if [ "$major" = "3" ] && [ "$minor" -ge 8 ]; then
                log_info "Python installed: $version ($cmd)"
                PYTHON_CMD="$cmd"
                return 0
            fi
        fi
    done
    log_warn "Python 3.8+ not found"
    return 1
}

test_exiftool() {
    if command_exists exiftool; then
        local version=$(exiftool -ver 2>/dev/null)
        log_info "ExifTool installed: $version"
        return 0
    fi
    log_warn "ExifTool not found"
    return 1
}

test_gpu() {
    if command_exists nvidia-smi; then
        local gpu=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1)
        if [ -n "$gpu" ]; then
            log_info "GPU detected: $gpu"
            HAS_GPU=true
            return 0
        fi
    fi
    log_warn "No NVIDIA GPU detected, will use CPU"
    HAS_GPU=false
    return 1
}

test_cuda() {
    local cuda_version=""
    local cudnn_version=""
    local driver_version=""

    # 检测驱动
    if command_exists nvidia-smi; then
        driver_version=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader 2>/dev/null | head -1 | tr -d ' ')
        log_info "NVIDIA Driver: $driver_version"
    fi

    # 检测 CUDA (nvcc)
    if command_exists nvcc; then
        cuda_version=$(nvcc --version 2>/dev/null | grep "release" | awk '{print $5}' | tr -d ',' | head -1)
        log_info "CUDA Toolkit: $cuda_version"
    else
        log_warn "CUDA Toolkit (nvcc) not found"
    fi

    # 检测 cuDNN
    local cudnn_paths=(
        "/usr/local/cuda/lib64/libcudnn*"
        "/usr/lib/x86_64-linux-gnu/libcudnn*"
        "/opt/cuda/lib64/libcudnn*"
    )

    for path in "${cudnn_paths[@]}"; do
        if ls $path 1>/dev/null 2>&1; then
            cudnn_version="Installed"
            log_info "cuDNN found"
            break
        fi
    done

    if [ -n "$cuda_version" ]; then
        return 0
    fi
    return 1
}

get_cuda_info() {
    if test_cuda 2>/dev/null; then
        echo "CUDA ready (Driver: $driver_version)"
    else
        echo "Not installed (CPU mode recommended)"
    fi
}

#===============================================================================
# 安装函数
#===============================================================================

install_git() {
    log_step "Installing Git..."
    if is_windows && command_exists winget; then
        winget install --id Git.Git -e --source winget 2>&1 | grep -E "(installed|error)" || true
    elif is_macos && command_exists brew; then
        brew install git
    elif command_exists apt-get; then
        sudo apt-get update && sudo apt-get install -y git
    elif command_exists yum; then
        sudo yum install -y git
    elif command_exists dnf; then
        sudo dnf install -y git
    else
        log_error "Cannot install Git automatically"
        log_info "Download: https://git-scm.com/downloads"
        return 1
    fi
    test_git
}

install_python() {
    log_step "Installing Python 3.11..."
    if is_windows && command_exists winget; then
        winget install --id Python.Python.3.11 -e --source winget 2>&1 | grep -E "(installed|error)" || true
    elif is_macos && command_exists brew; then
        brew install python@3.11
    elif command_exists apt-get; then
        sudo apt-get update && sudo apt-get install -y python3.11 python3-pip python3-venv
    elif command_exists yum; then
        sudo yum install -y python3.11
    elif command_exists dnf; then
        sudo dnf install -y python3.11
    else
        log_error "Cannot install Python automatically"
        log_info "Download: https://www.python.org/downloads/"
        return 1
    fi
}

install_exiftool() {
    log_step "Installing ExifTool..."
    if is_macos && command_exists brew; then
        brew install exiftool
    elif command_exists apt-get; then
        sudo apt-get update && sudo apt-get install -y exiftool
    elif command_exists yum; then
        sudo yum install -y perl-Image-ExifTool
    elif command_exists dnf; then
        sudo dnf install -y perl-Image-ExifTool
    else
        log_error "Cannot install ExifTool automatically"
        log_info "Download: https://exiftool.org/"
        return 1
    fi
    test_exiftool
}

install_python_deps() {
    log_step "Installing Python dependencies..."

    if [ -z "$PYTHON_CMD" ]; then
        log_error "Python not found"
        return 1
    fi

    local venv_path="${PROJECT_ROOT}/venv"
    local pip_cmd="$PYTHON_CMD -m pip"

    # 创建虚拟环境
    if [ ! -d "$venv_path" ]; then
        log_info "Creating virtual environment..."
        $PYTHON_CMD -m venv "$venv_path"
    fi

    # 确定 pip 命令
    if is_windows; then
        pip_cmd="${venv_path}/Scripts/pip"
    else
        pip_cmd="${venv_path}/bin/pip"
    fi

    # 配置 pip 镜像
    log_info "Configuring pip mirror..."
    $pip_cmd config set global.index-url "$PIP_MIRROR" 2>/dev/null || true

    # 升级 pip
    log_info "Upgrading pip..."
    $pip_cmd install --upgrade pip 2>&1 | grep -v "Requirement already" || true

    # 安装依赖
    local requirements="${PROJECT_ROOT}/requirements.txt"
    if [ -f "$requirements" ]; then
        log_info "Installing requirements..."
        $pip_cmd install -r "$requirements" 2>&1 | grep -v "Requirement already" || true
        log_success "Python dependencies installed"
    else
        log_warn "requirements.txt not found"
    fi
}

#===============================================================================
# CUDA 安装
#===============================================================================

show_cuda_download_links() {
    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}  ${WHITE}CUDA Download Links${NC}                        ${CYAN}"
    echo -e "${CYAN}========================================${NC}"
    echo ""
    echo -e "  ${GREEN}1. CUDA Toolkit 12.1 (Required)${NC}"
    echo -e "     https://developer.nvidia.com/cuda-downloads"
    echo -e "     Select: Linux > x86_64 > 12 > runfile (local)"
    echo ""
    echo -e "  ${GREEN}2. cuDNN 8.9 (Required for PyTorch)${NC}"
    echo -e "     https://developer.nvidia.com/rdp/cudnn-download"
    echo -e "     Select: cuDNN v8.9.x for CUDA 12.x > Linux"
    echo ""
    echo -e "  ${WHITE}Installation steps:${NC}"
    echo -e "     1. Run CUDA Toolkit installer"
    echo -e "     2. Extract cuDNN to /usr/local/cuda"
    echo -e "     3. Add to ~/.bashrc: export PATH=/usr/local/cuda/bin:\$PATH"
    echo -e "     4. Restart terminal"
    echo ""

    if ask_yes_no "Open CUDA download page?" "n"; then
        if command_exists xdg-open; then
            xdg-open "https://developer.nvidia.com/cuda-downloads" 2>/dev/null &
        fi
    fi
}

install_cuda() {
    log_step "Checking CUDA environment..."

    test_gpu
    if [ "$HAS_GPU" = "false" ]; then
        log_warn "No NVIDIA GPU detected"
        return 1
    fi

    if test_cuda; then
        log_success "CUDA environment ready"
        return 0
    fi

    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}  ${WHITE}CUDA Installation Required${NC}                   ${CYAN}"
    echo -e "${CYAN}========================================${NC}"
    echo ""
    echo -e "  GPU detected but CUDA/cuDNN not installed."
    echo -e "  FeatherTrace requires CUDA for GPU acceleration."
    echo ""
    echo -e "  ${GREEN}Option 1:${NC} Show download links"
    echo -e "  ${YELLOW}Option 2:${NC} Continue with CPU (slower)"
    echo ""

    local choice=$(ask_input "Select option" "1")
    echo ""

    case "$choice" in
        1)
            show_cuda_download_links
            ;;
        2)
            log_warn "Continuing with CPU mode"
            return 1
            ;;
        *)
            log_error "Invalid choice"
            return 1
            ;;
    esac
}

#===============================================================================
# 项目获取
#===============================================================================

get_project() {
    log_step "Getting project..."

    # 检查是否是 git 仓库
    if [ -d "${PROJECT_ROOT}/.git" ]; then
        log_info "Git repository found"

        # 获取当前远程 URL
        local remoteUrl=$(git -C "$PROJECT_ROOT" remote get-url origin 2>/dev/null)

        # 如果是 GitHub，切换到 Gitee
        local isGithub=false
        if [ -n "$remoteUrl" ] && [[ "$remoteUrl" == *"github.com"* ]]; then
            log_info "Using Gitee mirror for fast update..."
            git -C "$PROJECT_ROOT" remote set-url origin "$GITEE_MIRROR" 2>/dev/null
            isGithub=true
        fi

        log_info "Updating project..."
        git -C "$PROJECT_ROOT" pull origin master 2>/dev/null
        local pullStatus=$?

        # 如果原先是 GitHub，改回去
        if [ "$isGithub" = true ]; then
            log_info "Restoring remote to GitHub..."
            git -C "$PROJECT_ROOT" remote set-url origin "$GITHUB_ORIGIN" 2>/dev/null
        fi

        if [ $pullStatus -eq 0 ]; then
            log_success "Project updated"
            return 0
        else
            log_warn "Update failed, using existing files"
            return 0
        fi
    fi

    # 检查是否有项目文件
    if [ -f "${PROJECT_ROOT}/settings.yaml" ]; then
        log_success "Project files found"
        return 0
    fi

    # 检查目录是否非空
    local items=$(ls -A "$PROJECT_ROOT" 2>/dev/null | grep -v ".git" | grep -v "deploy.sh" | grep -v "deploy.ps1")
    if [ -n "$items" ]; then
        log_warn "Directory not empty, using existing files"
        return 0
    fi

    # 从 Gitee 克隆
    log_info "Cloning from Gitee..."
    if git clone --depth 1 "$GITEE_MIRROR" "$PROJECT_ROOT" 2>/dev/null; then
        log_success "Cloned from Gitee"
        
        # 自动改回 GitHub
        log_info "Setting remote to GitHub..."
        git -C "$PROJECT_ROOT" remote set-url origin "$GITHUB_ORIGIN" 2>/dev/null
        
        return 0
    fi

    # 从 GitHub 克隆
    log_info "Trying GitHub..."
    if git clone --depth 1 "$GITHUB_ORIGIN" "$PROJECT_ROOT" 2>/dev/null; then
        log_success "Cloned from GitHub"
        return 0
    fi

    log_error "Clone failed"
    return 1
}

#===============================================================================
# 配置向导
#===============================================================================

invoke_config_wizard() {
    log_step "Configuring project..."
    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}  ${WHITE}Configuration Wizard${NC}                         ${CYAN}"
    echo -e "${CYAN}========================================${NC}"
    echo ""

    # 1. 照片源目录
    echo -e "  ${CYAN}1/3 Photo source directory${NC}"
    echo -e "  ${GRAY}Enter the directory containing your bird photos${NC}"
    echo -e "  ${GRAY}Format: Year/yyyymmdd_Location/*.jpg${NC}"
    echo ""

    local default_source_dir="$HOME/Pictures"
    if is_macos; then
        default_source_dir="$HOME/Pictures"
    elif is_linux; then
        default_source_dir="$HOME/图片"
    fi

    local source_dir=$(ask_input "Photo directory" "$default_source_dir")
    if [ ! -d "$source_dir" ]; then
        if ask_yes_no "Directory does not exist, create it?"; then
            mkdir -p "$source_dir" 2>/dev/null
            log_success "Created: $source_dir"
        fi
    fi

    echo ""

    # 2. 输出目录
    echo -e "  ${CYAN}2/3 Output directory${NC}"
    local output_dir=$(ask_input "Output directory" "${PROJECT_ROOT}/data/processed")
    mkdir -p "$output_dir" 2>/dev/null

    echo ""

    # 3. 处理设备
    echo -e "  ${CYAN}3/3 Processing device${NC}"
    test_gpu

    if [ "$HAS_GPU" = "true" ]; then
        echo -e "  ${GREEN}GPU detected, CUDA recommended${NC}"
        echo -e "  $(get_cuda_info)"
        echo ""
        echo -e "  ${WHITE}Options:${NC}"
        echo "    1. auto   - Auto detect (recommended)"
        echo "    2. cuda   - Use GPU (requires CUDA)"
        echo "    3. cpu    - Use CPU (slower)"
        echo ""

        local choice=$(ask_input "Device" "1")
        case "$choice" in
            1) DEVICE="auto" ;;
            2)
                DEVICE="cuda"
                install_cuda || DEVICE="cpu"
                ;;
            3) DEVICE="cpu" ;;
            *) DEVICE="auto" ;;
        esac
    else
        echo -e "  ${YELLOW}No GPU detected, will use CPU${NC}"
        DEVICE="cpu"
    fi

    echo ""
    log_step "Generating config files..."

    # 生成 settings.yaml
    local config_path="${PROJECT_ROOT}/config/settings.yaml"
    mkdir -p "$(dirname "$config_path")"

    cat > "$config_path" << EOF
# FeatherTrace config
# Generated by deploy script

paths:
  allowed_roots:
    - "${source_dir//\\/\\\\}"
  references_path: "data/references"
  sources:
    - path: "${source_dir//\\/\\\\}"
      recursive: true
      enabled: true
  output:
    root_dir: "${output_dir//\\/\\\\}"
    structure_template: "{source_structure}/{filename}_{species_cn}_{confidence}"
    write_back_to_source: false
  db_path: "data/db/wingscribe.db"
  ioc_list_path: "data/references/Multiling IOC 15.1_d.xlsx"
  model_cache_dir: "data/models"
processing:
  device: "$DEVICE"
  yolo_model: "yolov8n.pt"
  confidence_threshold: 0.5
  blur_threshold: 40.0
  target_size: 640
  crop_padding: 200
recognition:
  mode: "local"
  region_filter: "auto"
  top_k: 5
  alternatives_threshold: 70
  low_confidence_threshold: 60
  local:
    model_type: "bioclip-2"
    batch_size: 512
    inference_batch_size: 16
web:
  host: "0.0.0.0"
  port: 8000
EOF

    log_success "Config generated: $config_path"

    # 生成 secrets.yaml
    local secrets_path="${PROJECT_ROOT}/config/secrets.yaml"
    if [ ! -f "$secrets_path" ]; then
        cat > "$secrets_path" << 'EOF'
# FeatherTrace secrets
hf_api_key: ""
dongniao_api_key: ""
EOF
        log_success "Secrets generated: $secrets_path"
    fi

    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}  ${WHITE}Configuration Summary${NC}                        ${CYAN}"
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}  Source:  ${WHITE}$source_dir${NC}"
    echo -e "${CYAN}  Output:  ${WHITE}$output_dir${NC}"
    echo -e "${CYAN}  Device:  ${WHITE}$DEVICE${NC}"
    echo -e "${CYAN}========================================${NC}"
}

#===============================================================================
# Web 服务
#===============================================================================

start_web_server() {
    log_step "Starting Web server..."

    local venv_python=""
    if is_windows; then
        venv_python="${PROJECT_ROOT}/venv/Scripts/python.exe"
    else
        venv_python="${PROJECT_ROOT}/venv/bin/python"
    fi

    if [ ! -f "$venv_python" ]; then
        log_error "Virtual environment not found!"
        log_info "Please run '$0 install' first"
        return 1
    fi

    local web_script="${PROJECT_ROOT}/src/web/app.py"
    if [ ! -f "$web_script" ]; then
        log_error "Web script not found: $web_script"
        return 1
    fi

    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}  ${GREEN}Starting Web server...${NC}                        ${CYAN}"
    echo -e "${CYAN}  URL: ${WHITE}http://localhost:8000${NC}                    ${CYAN}"
    echo -e "${CYAN}  Press ${WHITE}Ctrl+C${NC} to stop                          ${CYAN}"
    echo -e "${CYAN}========================================${NC}"
    echo ""

    cd "$PROJECT_ROOT"
    "$venv_python" "$web_script"
}

#===============================================================================
# Docker Deployment
#===============================================================================

test_docker() {
    if command_exists docker; then
        local version=$(docker --version 2>/dev/null)
        log_info "Docker installed: $version"
        return 0
    fi
    log_warn "Docker not found"
    return 1
}

install_docker() {
    log_step "Installing Docker..."
    if is_linux; then
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        sudo usermod -aG docker $USER
    elif is_macos && command_exists brew; then
        brew install --cask docker
    elif is_windows && command_exists winget; then
        winget install --id Docker.DockerDesktop -e --source winget
    else
        log_error "Cannot install Docker automatically"
        log_info "Download: https://www.docker.com/get-started"
        return 1
    fi
    test_docker
}

start_docker_local() {
    log_step "Starting Docker (local mode)..."

    if ! test_docker; then
        if ask_yes_no "Install Docker?"; then install_docker; fi
        return 1
    fi

    cd "$PROJECT_ROOT"

    # 检查是否有 GPU
    if test_gpu && command_exists nvidia-docker; then
        echo -e "${CYAN}  Using GPU profile${NC}"
        docker compose up -d wingscribe-gpu
    else
        echo -e "${CYAN}  Using CPU mode${NC}"
        docker compose up -d wingscribe
    fi

    echo ""
    echo -e "${GREEN}Web UI: http://localhost:8000${NC}"
    echo -e "${GREEN}Recognition API: http://localhost:8000/api/recognition${NC}"
}

start_docker_cpu() {
    log_step "Starting CPU recognition service..."

    if ! test_docker; then
        log_error "Docker not found"
        return 1
    fi

    cd "$PROJECT_ROOT"
    docker compose -f docker-compose.remote.yml up -d recognition-cpu

    echo ""
    echo -e "${GREEN}Recognition Service (CPU): http://localhost:8080${NC}"
}

start_docker_gpu() {
    log_step "Starting GPU recognition service..."

    if ! test_docker; then
        log_error "Docker not found"
        return 1
    fi

    if ! test_gpu; then
        log_error "No GPU detected"
        return 1
    fi

    cd "$PROJECT_ROOT"
    docker compose -f docker-compose.remote.yml up -d recognition-gpu

    echo ""
    echo -e "${GREEN}Recognition Service (GPU): http://localhost:8081${NC}"
}

start_docker_all() {
    log_step "Starting full Docker stack..."

    if ! test_docker; then
        log_error "Docker not found"
        return 1
    fi

    cd "$PROJECT_ROOT"
    docker compose -f docker-compose.yml -f docker-compose.remote.yml up -d

    echo ""
    echo -e "${GREEN}Web UI: http://localhost:8000${NC}"
    echo -e "${GREEN}Recognition API (CPU): http://localhost:8080${NC}"
    echo -e "${GREEN}Recognition API (GPU): http://localhost:8081${NC}"
    echo -e "${GREEN}Redis (queue): localhost:6379${NC}"
}

#===============================================================================
# Cloud Platform Configuration
#===============================================================================

configure_cloud() {
    log_step "Configuring cloud platforms..."
    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}  ${WHITE}Cloud Platform Configuration${NC}               ${CYAN}"
    echo -e "${CYAN}========================================${NC}"
    echo ""

    local secrets_path="${PROJECT_ROOT}/config/secrets.yaml"

    # 确保 secrets.yaml 存在
    if [ ! -f "$secrets_path" ]; then
        cat > "$secrets_path" << 'EOF'
# FeatherTrace secrets
# Cloud platform API keys

# Local recognition (optional)
local:
  enabled: true

# Cloud platforms
cloud:
  huggingface:
    api_token: ${HF_TOKEN}
    model_id: hf-hub:imageomics/bioclip

  modelscope:
    api_token: ${MODELSCOPE_TOKEN}
    model_id: damo/cv_resnet50_image-classification_birds

  aliyun:
    access_key_id: ${ALIYUN_ACCESS_KEY_ID}
    access_key_secret: ${ALIYUN_ACCESS_KEY_SECRET}

  baidu:
    api_key: ${BAIDU_API_KEY}
    secret_key: ${BAIDU_SECRET_KEY}

# API authentication
api_keys:
  - name: default
    key: ${FEATHERTRACE_API_KEY}
    rate_limit: 1000/day
    quota: 10000/month
EOF
        log_success "Created secrets template"
    fi

    echo -e "  ${WHITE}Cloud Platform API Keys${NC}"
    echo ""
    echo -e "  ${GREEN}HuggingFace:${NC}"
    echo -e "    Set HF_TOKEN environment variable or edit $secrets_path"
    echo -e "    Get token: https://huggingface.co/settings/tokens"
    echo ""
    echo -e "  ${GREEN}ModelScope:${NC}"
    echo -e "    Set MODELSCOPE_TOKEN environment variable or edit $secrets_path"
    echo -e "    Get token: https://modelscope.cn/my/settings/token"
    echo ""
    echo -e "  ${GREEN}Aliyun:${NC}"
    echo -e "    Configure access_key_id and access_key_secret in secrets.yaml"
    echo -e "    Get credentials: https://ram.console.aliyun.com/..."
    echo ""
    echo -e "  ${GREEN}Baidu:${NC}"
    echo -e "    Configure api_key and secret_key in secrets.yaml"
    echo -e "    Get credentials: https://ai.baidu.com/tech/imagerecognition"
    echo ""

    if ask_yes_no "Open configuration file for editing?" "n"; then
        if command_exists nano; then
            nano "$secrets_path"
        elif command_exists vim; then
            vim "$secrets_path"
        else
            log_info "Edit manually: $secrets_path"
        fi
    fi
}

list_cloud_platforms() {
    log_step "Available cloud platforms..."
    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}  ${WHITE}Cloud Platforms${NC}                             ${CYAN}"
    echo -e "${CYAN}========================================${NC}"
    echo ""
    echo -e "  ${GREEN}1. HuggingFace${NC}"
    echo -e "     Status: $([ -n "$HF_TOKEN" ] && echo "${GREEN}Configured${NC}" || echo "${YELLOW}Not configured${NC}")"
    echo -e "     Models: microsoft/BioCLIP, hf-hub:imageomics/bioclip"
    echo -e "     URL: https://huggingface.co/"
    echo ""
    echo -e "  ${GREEN}2. ModelScope (魔搭)${NC}"
    echo -e "     Status: $([ -n "$MODELSCOPE_TOKEN" ] && echo "${GREEN}Configured${NC}" || echo "${YELLOW}Not configured${NC}")"
    echo -e "     Models: damo/cv_resnet50_image-classification_birds"
    echo -e "     URL: https://modelscope.cn/"
    echo ""
    echo -e "  ${GREEN}3. Aliyun (阿里云)${NC}"
    echo -e "     Status: $([ -f "${PROJECT_ROOT}/config/secrets.yaml" ] && grep -q "access_key_id" "${PROJECT_ROOT}/config/secrets.yaml" && echo "${GREEN}Configured${NC}" || echo "${YELLOW}Not configured${NC}")"
    echo -e "     Service: 图像标签识别"
    echo -e "     URL: https://www.aliyun.com/product/imagerecog"
    echo ""
    echo -e "  ${GREEN}4. Baidu (百度云)${NC}"
    echo -e "     Status: $([ -f "${PROJECT_ROOT}/config/secrets.yaml" ] && grep -q "api_key" "${PROJECT_ROOT}/config/secrets.yaml" && echo "${GREEN}Configured${NC}" || echo "${YELLOW}Not configured${NC}")"
    echo -e "     Service: 图像识别"
    echo -e "     URL: https://ai.baidu.com/tech/imagerecognition"
    echo ""
}

#===============================================================================
# 使用说明
#===============================================================================

show_help() {
    cat << EOF
========================================
  FeatherTrace Deployment
========================================
  AI Bird Photo Management
========================================

Usage:
  $0 [command]

Commands:
  deploy           Full deployment (install + config)
  install          Install dependencies only
  config           Configuration wizard
  update           Update project
  cuda             Install CUDA (GPU support)
  web              Start Web server
  docker:local     Start with Docker (local)
  docker:cpu       Start CPU container only
  docker:gpu       Start GPU container (requires GPU)
  docker:all       Full Docker stack (local + recognition services)
  cloud:config     Configure cloud platform API keys
  cloud:list       List available cloud platforms
  help             Show this help

Examples:
  $0 deploy           # Full deployment
  $0 config           # Configure only
  $0 web              # Start Web service
  $0 cuda             # Install CUDA
  $0 docker:local     # Start with Docker
  $0 cloud:config     # Configure cloud platforms

Quick Start:
  1. Run: $0 deploy
  2. Configure photo directory
  3. Run: $0 web
  4. Open: http://localhost:8000

Cloud Platforms:
  - HuggingFace: Use HF_TOKEN environment variable
  - ModelScope: Use MODELSCOPE_TOKEN environment variable
  - Aliyun: Configure access_key_id/secret in secrets.yaml
  - Baidu: Configure api_key/secret_key in secrets.yaml

EOF
}

#===============================================================================
# 主入口
#===============================================================================

main() {
    cd "$PROJECT_ROOT"

    local command="${1:-help}"

    case "$command" in
        deploy|d)
            echo ""
            echo -e "${CYAN}========================================${NC}"
            echo -e "${CYAN}  ${GREEN}Deployment${NC}                                    ${CYAN}"
            echo -e "${CYAN}========================================${NC}"
            echo ""

            log_step "1/4 Checking environment..."
            test_git || true
            test_python || log_error "Python installation recommended"
            test_exiftool || log_warn "ExifTool not found"
            test_gpu

            log_step "2/4 Installing dependencies..."
            if ! command_exists git; then
                if ask_yes_no "Install Git?"; then install_git; fi
            fi
            if ! test_python; then
                if ask_yes_no "Install Python?"; then install_python; fi
            fi
            if ! command_exists exiftool; then
                if ask_yes_no "Install ExifTool?"; then install_exiftool; fi
            fi

            log_step "3/4 Installing Python dependencies..."
            install_python_deps

            log_step "4/4 Configuring project..."
            get_project
            invoke_config_wizard

            echo ""
            log_success "Deployment complete!"
            echo ""
            echo -e "${WHITE}Next steps:${NC}"
            echo "  1. Run: $0 web"
            echo "  2. Open: http://localhost:8000"
            echo ""
            ;;
        install|i)
            echo ""
            echo -e "${CYAN}========================================${NC}"
            echo -e "${CYAN}  ${WHITE}Install Dependencies${NC}                         ${CYAN}"
            echo -e "${CYAN}========================================${NC}"
            echo ""

            test_git || true
            test_python || true
            test_exiftool || true

            if ! command_exists git; then install_git || true; fi
            if ! test_python; then install_python || true; fi
            if ! command_exists exiftool; then install_exiftool || true; fi

            install_python_deps
            log_success "Dependencies installed"
            ;;
        config|c)
            invoke_config_wizard
            ;;
        update|u)
            echo ""
            echo -e "${CYAN}========================================${NC}"
            echo -e "${CYAN}  ${WHITE}Update Project${NC}                               ${CYAN}"
            echo -e "${CYAN}========================================${NC}"
            echo ""
            get_project
            ;;
        cuda)
            echo ""
            echo -e "${CYAN}========================================${NC}"
            echo -e "${CYAN}  ${GREEN}CUDA Installation${NC}                            ${CYAN}"
            echo -e "${CYAN}========================================${NC}"
            echo ""
            install_cuda
            ;;
        web|w)
            start_web_server
            ;;
        docker:local|dl)
            start_docker_local
            ;;
        docker:cpu|dc)
            start_docker_cpu
            ;;
        docker:gpu|dg)
            start_docker_gpu
            ;;
        docker:all|da)
            start_docker_all
            ;;
        cloud:config|cc)
            configure_cloud
            ;;
        cloud:list|cl)
            list_cloud_platforms
            ;;
        help|-h|--help|"")
            show_help
            ;;
        *)
            log_error "Unknown command: $command"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

main "$@"
