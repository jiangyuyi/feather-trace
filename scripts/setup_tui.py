#!/usr/bin/env python3
"""
FeatherTrace TUI 环境设置脚本

此脚本用于安装 TUI 界面所需的 Python 依赖。
用于部署脚本的交互式界面。
"""

import os
import sys
import subprocess
import shutil

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TUI_REQUIREMENTS = os.path.join(PROJECT_ROOT, "scripts", "requirements_tui.txt")
VENV_DIR = os.path.join(PROJECT_ROOT, "venv")


def check_python():
    """检查 Python 是否可用"""
    try:
        result = subprocess.run(
            ["python3", "--version"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"Python 已安装: {result.stdout.strip()}")
            return "python3"
    except FileNotFoundError:
        pass

    try:
        result = subprocess.run(
            ["python", "--version"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"Python 已安装: {result.stdout.strip()}")
            return "python"
    except FileNotFoundError:
        pass

    return None


def check_tui_deps():
    """检查 TUI 依赖是否已安装"""
    required = ["rich", "questionary"]
    missing = []

    for pkg in required:
        try:
            __import__(pkg.replace("-", "_"))
        except ImportError:
            missing.append(pkg)

    return missing


def create_venv():
    """创建虚拟环境"""
    print("\n[INFO] 创建 Python 虚拟环境...")

    if os.name == "nt":
        venv_python = os.path.join(VENV_DIR, "Scripts", "python.exe")
        pip_cmd = [os.path.join(VENV_DIR, "Scripts", "pip.exe")]
    else:
        venv_python = os.path.join(VENV_DIR, "bin", "python")
        pip_cmd = [os.path.join(VENV_DIR, "bin", "pip")

    if os.path.exists(venv_python):
        print("[INFO] 虚拟环境已存在")
        return pip_cmd

    # 创建虚拟环境
    python_cmd = check_python()
    if not python_cmd:
        print("[ERROR] Python 未安装，无法创建虚拟环境")
        return None

    result = subprocess.run([python_cmd, "-m", "venv", VENV_DIR])
    if result.returncode != 0:
        print("[ERROR] 创建虚拟环境失败")
        return None

    print("[OK] 虚拟环境创建成功")
    return pip_cmd


def install_deps(pip_cmd):
    """安装 TUI 依赖"""
    print("\n[INFO] 安装 TUI 依赖...")

    # 升级 pip
    result = subprocess.run(pip_cmd + ["install", "--upgrade", "pip"])
    if result.returncode != 0:
        print("[WARN] pip 升级失败，继续安装...")

    # 安装依赖
    if os.path.exists(TUI_REQUIREMENTS):
        result = subprocess.run(pip_cmd + ["install", "-r", TUI_REQUIREMENTS])
    else:
        # 安装必需依赖
        result = subprocess.run(pip_cmd + ["install", "rich>=13.0.0", "questionary>=2.0.0"])

    if result.returncode == 0:
        print("[OK] TUI 依赖安装成功")
        return True
    else:
        print("[ERROR] TUI 依赖安装失败")
        return False


def run_tui():
    """运行 TUI 界面"""
    print("\n[INFO] 启动 TUI 界面...")

    if os.name == "nt":
        python_cmd = os.path.join(VENV_DIR, "Scripts", "python.exe")
    else:
        python_cmd = os.path.join(VENV_DIR, "bin", "python")

    if not os.path.exists(python_cmd):
        print("[ERROR] 虚拟环境不存在，请先运行 setup_tui.py")
        return False

    # 运行主脚本
    tui_script = os.path.join(PROJECT_ROOT, "scripts", "tui_main.py")

    result = subprocess.run([python_cmd, tui_script])
    return result.returncode == 0


def main():
    """主函数"""
    print("=" * 50)
    print("  🪶 FeatherTrace TUI 环境设置")
    print("=" * 50)

    # 检查 Python
    python_cmd = check_python()
    if not python_cmd:
        print("\n[ERROR] Python 未安装!")
        print("请先安装 Python 3.8+: https://www.python.org/downloads/")
        sys.exit(1)

    # 检查依赖
    missing = check_tui_deps()

    if missing:
        print(f"\n[INFO] 缺少依赖: {', '.join(missing)}")

        # 询问是否安装
        if len(missing) <= 2:
            response = input("是否自动安装? [Y/n]: ").strip().lower()
            if response not in ["n", "no"]:
                # 创建虚拟环境
                pip_cmd = create_venv()
                if pip_cmd:
                    install_deps(pip_cmd)
                    missing = check_tui_deps()

        if missing:
            print(f"\n[WARN] 以下依赖未安装: {', '.join(missing)}")
            print("TUI 界面可能无法运行，但基础功能不受影响")
    else:
        print("\n[OK] TUI 依赖已安装")

    # 询问是否运行 TUI
    print("\n" + "=" * 50)
    response = input("是否启动 TUI 界面? [Y/n]: ").strip().lower()

    if response not in ["n", "no"]:
        if not missing:
            run_tui()
        else:
            # 尝试运行
            if not run_tui():
                print("[ERROR] TUI 启动失败")

    print("\n[INFO] 设置完成!")
    print("后续可以运行 scripts/deploy.sh (Linux/Mac) 或 scripts/deploy.ps1 (Windows PowerShell)")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[INFO] 用户取消")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] 发生错误: {e}")
        sys.exit(1)
