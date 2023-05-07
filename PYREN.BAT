@echo off
echo Run's app ...
for /f %%i in ('python -c "import sys; print(sys.executable)"') do set FULL_PATH_PYTHON3=%%i
%FULL_PATH_PYTHON3% main.py
pause
