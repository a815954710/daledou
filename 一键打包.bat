@echo off
cd /d "%~dp0"

uv run --with pyinstaller pyinstaller ^
  --clean ^
  --onefile ^
  --name daledou ^
  --paths . ^
  --hidden-import src.tasks.common ^
  --hidden-import src.tasks.noon ^
  --hidden-import src.tasks.evening ^
  --hidden-import src.tasks.register ^
  main.py
pause
