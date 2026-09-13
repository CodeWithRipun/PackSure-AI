# PackCheck AI
SIH26034
Smart Packaging Compliance Verification

## Run on Windows
```powershell
cd "C:\Users\RipunJoy\Documents\SIH Project\PackSure_AI_Project"
py -m venv venv
.\venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
Copy-Item .env.example .env
py -m uvicorn app.main:app --reload
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8080
