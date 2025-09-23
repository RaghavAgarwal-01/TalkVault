@echo off
echo 🚀 Setting up Talk Vault backend...

REM Create virtual environment
python -m venv venv
call venv\Scripts\activate.bat

REM Install dependencies
pip install -r api\requirements.txt

REM Download spaCy model
python -m spacy download en_core_web_sm

REM Create environment file
copy api\.env.example api\.env

REM Create uploads directory
mkdir api\uploads 2>nul

echo ✅ Backend setup complete!
echo.
echo Next steps:
echo 1. Activate virtual environment: venv\Scripts\activate.bat
echo 2. Update api\.env with your configurations
echo 3. Run the server: cd api ^&^& python -m uvicorn app.main:app --reload
echo.
echo Backend will be available at: http://localhost:8000
echo API documentation: http://localhost:8000/docs
