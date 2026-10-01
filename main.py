"""
FastAPI backend for Bengali Panjika app.
Run with: uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from datetime import datetime, timedelta
import calendar as pycalendar

from panchang import get_full_panchang, gregorian_to_bengali_date, get_festival

app = FastAPI(title="Panjika API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Default location: Kolkata
DEFAULT_LAT = 22.5726
DEFAULT_LON = 88.3639
DEFAULT_TZ = "Asia/Kolkata"


@app.get("/api/panchang")
def api_panchang(
    date: str = Query(default=None, description="YYYY-MM-DD, defaults to today"),
    lat: float = Query(default=DEFAULT_LAT),
    lon: float = Query(default=DEFAULT_LON),
    tz: str = Query(default=DEFAULT_TZ),
):
    """Get full panchang for a single date."""
    if date:
        d = datetime.strptime(date, "%Y-%m-%d")
    else:
        d = datetime.now()
    result = get_full_panchang(d, lat=lat, lon=lon, tz_name=tz)
    result["festival"] = get_festival(result["gregorian_date"])
    return result


@app.get("/api/month")
def api_month(
    year: int = Query(...),
    month: int = Query(..., ge=1, le=12),
    lat: float = Query(default=DEFAULT_LAT),
    lon: float = Query(default=DEFAULT_LON),
    tz: str = Query(default=DEFAULT_TZ),
):
    """Get a lightweight panchang summary (tithi + bengali date only) for every day in a Gregorian month."""
    days_in_month = pycalendar.monthrange(year, month)[1]
    results = []
    for day in range(1, days_in_month + 1):
        d = datetime(year, month, day)
        full = get_full_panchang(d, lat=lat, lon=lon, tz_name=tz)
        results.append({
            "date": full["gregorian_date"],
            "weekday": full["weekday"],
            "tithi": full["tithi"]["name"],
            "paksha": full["tithi"]["paksha"],
            "bengali_day": full["bengali_date"]["day"],
            "bengali_month": full["bengali_date"]["month"],
            "bengali_year": full["bengali_date"]["bengali_year"],
            "festival": get_festival(full["gregorian_date"]),
        })
    return {"year": year, "month": month, "days": results}


# Serve the frontend
app.mount("/", StaticFiles(directory="static", html=True), name="static")
