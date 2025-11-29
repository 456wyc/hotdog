@echo off
chcp 65001 > nul
echo 正在启动热键冲突检测器...
echo.

REM 检查虚拟环境是否存在
if exist ".venv\Scripts\activate.bat" (
    echo 使用虚拟环境...
    call .venv\Scripts\activate.bat
    python main.py
) else (
    echo 使用全局Python环境...
    python main.py
)

echo.
echo 程序已退出
pause