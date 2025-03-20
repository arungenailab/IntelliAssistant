@echo off
echo Setting up GitHub repository for IntelliAssistant...

REM Initialize Git repository if not already done
if not exist .git (
    echo Initializing Git repository...
    git init
) else (
    echo Git repository already initialized.
)

REM Ensure .gitignore is properly set up
if not exist .gitignore (
    echo Creating .gitignore file...
    echo # Python > .gitignore
    echo __pycache__/ >> .gitignore
    echo *.py[cod] >> .gitignore
    echo *$py.class >> .gitignore
    echo venv/ >> .gitignore
    echo *.env >> .gitignore
    echo config.py >> .gitignore
    echo # Node.js >> .gitignore
    echo node_modules/ >> .gitignore
    echo # IDE files >> .gitignore
    echo .idea/ >> .gitignore
    echo .vscode/ >> .gitignore
)

REM Make sure config.py is not tracked
echo Ensuring config.py is not tracked...
git rm --cached config.py 2>nul

REM Add all files
echo Adding files to Git...
git add .

REM Check for config.py in staged files
git diff --cached --name-only | findstr "config.py" >nul
if not errorlevel 1 (
    echo WARNING: config.py is still being tracked. Removing from staged files...
    git rm --cached config.py
)

REM Make initial commit
echo Making initial commit...
git commit -m "Initial commit of IntelliAssistant"

REM Instructions for setting up remote repository
echo.
echo Next steps:
echo 1. Create a new repository on GitHub (don't initialize with README, .gitignore, or license)
echo 2. Run the following commands to push to GitHub:
echo    git remote add origin https://github.com/yourusername/IntelliAssistant.git
echo    git branch -M main
echo    git push -u origin main
echo.
echo Replace 'yourusername' with your actual GitHub username.

pause 