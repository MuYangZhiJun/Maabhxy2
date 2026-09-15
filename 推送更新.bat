@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo   提交并推送到 GitHub（失败会自动重试）
echo ============================================
echo.
python "tools\push.py" %*
echo.
echo 按任意键关闭...
pause >nul
