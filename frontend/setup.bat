@echo off
REM Frontend Setup Script for ModularChatBot (Windows)

echo 🚀 Setting up ModularChatBot Frontend...

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js is not installed. Please install Node.js 18+ first.
    pause
    exit /b 1
)

REM Check Node.js version
for /f "tokens=1,2,3 delims=." %%a in ('node --version') do set NODE_VERSION=%%a
set NODE_VERSION=%NODE_VERSION:~1%
if %NODE_VERSION% LSS 18 (
    echo ❌ Node.js version 18+ is required. Current version: 
    node --version
    pause
    exit /b 1
)

echo ✅ Node.js version: 
node --version

REM Install dependencies
echo 📦 Installing dependencies...
npm install

if %errorlevel% neq 0 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)

REM Create environment file if it doesn't exist
if not exist .env.local (
    echo 📝 Creating .env.local file...
    (
        echo # Frontend Environment Variables
        echo NEXT_PUBLIC_API_URL=http://localhost:8000
        echo.
        echo # Development settings
        echo NODE_ENV=development
    ) > .env.local
    echo ✅ Created .env.local file
) else (
    echo ✅ .env.local file already exists
)

REM Check if backend is running
echo 🔍 Checking backend connection...
curl -s http://localhost:8000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Backend is running on http://localhost:8000
) else (
    echo ⚠️  Backend is not running on http://localhost:8000
    echo    Make sure to start the backend first:
    echo    cd ..\backend ^&^& python -m uvicorn app.main:app --reload
)

echo.
echo 🎉 Frontend setup complete!
echo.
echo To start the development server:
echo   npm run dev
echo.
echo To build for production:
echo   npm run build
echo   npm start
echo.
echo The frontend will be available at: http://localhost:3000
pause
