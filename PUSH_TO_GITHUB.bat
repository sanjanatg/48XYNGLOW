@echo off
title GitHub Push Helper
echo ========================================
echo      GitHub Push Helper
echo ========================================
echo.
echo This script will push your code to GitHub repository: sanjanatg/48XYNGLOW
echo.

REM Set up environment
set REPO_URL=https://github.com/sanjanatg/48XYNGLOW.git
set BASE_DIR=%~dp0
cd /d %BASE_DIR%

REM Create a .gitignore file
echo Creating .gitignore file...
(
echo # Byte-compiled / optimized / DLL files
echo __pycache__/
echo *.py[cod]
echo *$py.class
echo .env
echo venv/
echo logs/
echo *.log
echo temp_*
echo run_*.bat
echo # except our main scripts
echo !run.py
echo !START_*.bat
) > .gitignore

REM Check if git is installed
where git >NUL 2>&1
if %ERRORLEVEL% NEQ 0 (
  echo ERROR: Git is not installed or not in PATH.
  echo Please install Git from https://git-scm.com/downloads
  pause
  exit /b 1
)

echo ========================================
echo    EXECUTING GIT COMMANDS
echo ========================================

REM Initialize Git repository if not already initialized
if not exist ".git" (
  echo Step 1: Initializing Git repository...
  git init
) else (
  echo Step 1: Git repository already initialized.
)

REM Add all files
echo.
echo Step 2: Adding files to Git...
git add .

REM Commit changes
echo.
echo Step 3: Committing changes...
git commit -m "Add Find My Fund application with improved startup scripts"

REM Set the remote URL
echo.
echo Step 4: Setting remote URL...
git remote remove origin 2>NUL
git remote add origin %REPO_URL%

REM Push to GitHub
echo.
echo Step 5: Pushing to GitHub...
git push -u origin main

echo.
echo ========================================
echo    PUSH OPERATION COMPLETED
echo ========================================
echo.
echo If you encountered any authentication errors:
echo 1. Make sure you're logged in to GitHub
echo 2. You might need to use a Personal Access Token instead of password
echo 3. Try running 'git push -u origin main' manually
echo.
pause 