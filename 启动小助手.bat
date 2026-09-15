@echo off
cd /d "%~dp0"

echo ============================================
echo   崩坏学园2 小助手 —— 启动
echo ============================================
echo.

rem 用 set "VAR=值" 这种写法：不带引号进变量，用的时候才加引号。
rem 踩过：写成 set ADB="路径 带空格" 再在 for /f 里用，cmd 会把引号拆乱，
rem 报 'E:\MuMu' is not recognized as an internal or external command。
set "ADB=E:\MuMu Player 12\nx_main\adb.exe"
set "DEV=127.0.0.1:16384"

echo [1/2] 检查模拟器连接……
"%ADB%" connect %DEV% >nul 2>&1
"%ADB%" -s %DEV% shell echo ok >nul 2>&1
if errorlevel 1 (
    echo.
    echo   [x] 连不上模拟器 %DEV%
    echo       先把 MuMu Player 12 打开，再双击这个脚本
    echo.
    pause
    exit /b 1
)
echo       已连上 %DEV%

echo [2/2] 打开图形界面……
if not exist "gui\MFAAvalonia.exe" (
    echo.
    echo   [x] 找不到 gui\MFAAvalonia.exe，先构建一次：
    echo         python tools\install.py
    echo         python tools\get_gui.py
    echo.
    pause
    exit /b 1
)
start "" "gui\MFAAvalonia.exe"

echo.
echo 界面已打开：在里面勾任务，点「开始」。
echo 游戏没开也没关系，勾上「启动崩坏学园2」它会自己拉起来。
echo 想每天自动跑，看 README 里「怎么自启」那一节。
echo.
rem 别用 timeout：没有控制台的时候（比如输出被重定向）它会报
rem "Input redirection is not supported" 然后卡住。ping 等一秒更稳。
ping -n 6 127.0.0.1 >nul
