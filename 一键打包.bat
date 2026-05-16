pyinstaller ^
  --onefile ^
  --name daledou ^
  --paths src ^
  --hidden-import src.daledou.tasks.common ^
  --hidden-import src.daledou.tasks.one ^
  --hidden-import src.daledou.tasks.two ^
  --hidden-import src.daledou.tasks.other ^
  main.py
pause