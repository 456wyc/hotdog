@echo off
chcp 65001 > nul
echo 热键冲突检测器 - 依赖安装脚本
echo ================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.6或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python版本检查:
python --version
echo.

REM 检查虚拟环境是否存在
if not exist ".venv" (
    echo 创建虚拟环境...
    python -m venv .venv
    echo 虚拟环境创建完成
) else (
    echo 虚拟环境已存在
)
echo.

REM 激活虚拟环境并安装依赖
echo 激活虚拟环境并安装依赖...
call .venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo 安装完成！现在可以运行程序了:
echo 1. 双击 "启动程序.bat"
echo 2. 或者在命令行输入: python main.py
echo.
pause