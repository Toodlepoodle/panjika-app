# Panjika App — Local Setup

## Requirements
- Python 3.9+ installed on your machine

## Run it

1. Open a terminal in this folder
2. Install dependencies:
   pip install -r requirements.txt
3. Start the server:
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
4. Open your browser to:
   http://localhost:8000

That's it — you should see today's panchang (tithi, nakshatra, Bengali date, sunrise/sunset).

## Project structure
- panchang.py   -> core calculation engine (tithi/nakshatra/yoga/karana/Bengali date)
- main.py       -> FastAPI backend serving /api/panchang and /api/month
- static/       -> frontend (HTML/CSS/JS, installable as a PWA)

## Next step: packaging as an Android app
Once you're happy with how this looks and behaves:
1. Deploy this backend somewhere public (Render, Railway, PythonAnywhere, etc. all have free tiers)
2. Point static/index.html's API calls at your deployed backend URL instead of localhost
3. Install Bubblewrap: npm i -g @bubblewrap/cli
4. Run: bubblewrap init --manifest=https://yourdomain.com/manifest.json
5. Run: bubblewrap build
   -> this generates app-release.aab, ready for Play Console upload
