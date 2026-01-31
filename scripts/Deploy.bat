@echo off
REM===============================================================================
REM FeatherTrace 一键部署 - Windows 双击运行
REM===============================================================================

setlocal

REM 获取脚本所在目录
set "SCRIPT_DIR=%~dp0"
set "PS_SCRIPT=%SCRIPT_DIR%deploy.ps1"

REM 去除路径末尾的 \
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

echo [INFO] 检查 PowerShell...
echo.

REM 优先使用 PowerShell 7 (pwsh)
where pwsh >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [INFO] 找到 PowerShell 7
    pwsh -ExecutionPolicy Bypass -File "%PS_SCRIPT%" %*
    exit /b %ERRORLEVEL%
)

REM 备用 Windows PowerShell
where powershell >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [INFO] 找到 Windows PowerShell
    powershell -ExecutionPolicy Bypass -File "%PS_SCRIPT%" %*
    exit /b %ERRORLEVEL%
)

REM 未找到 PowerShell
echo [ERROR] 未找到 PowerShell！
echo.
echo 请安装 PowerShell：
echo   - 方法1: winget install Microsoft.PowerShell
echo   - 方法2: https://github.com/PowerShell/PowerShell/releases
echo.
echo 或使用 Git Bash 运行: bash "%SCRIPT_DIR%\deploy.sh"
echo.
pause
exit /b 1
endlocal
