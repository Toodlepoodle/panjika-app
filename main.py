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

<<<<<<< HEAD
from panchang import get_full_panchang, gregorian_to_bengali_date, get_festival, CITIES, get_horoscope, RASHI_NAMES
=======
from panchang import get_full_panchang, gregorian_to_bengali_date, get_festival
>>>>>>> origin/main

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


<<<<<<< HEAD
@app.get("/api/horoscope")
def api_horoscope(
    rashi: int = Query(..., ge=0, le=11, description="Rashi index 0=Mesha..11=Meena"),
    date: str = Query(default=None, description="YYYY-MM-DD, defaults to today"),
):
    """Deterministic daily entertainment horoscope message for a chosen rashi."""
    if date:
        d = datetime.strptime(date, "%Y-%m-%d").date()
    else:
        d = datetime.now().date()
    return {
        "rashi": RASHI_NAMES[rashi],
        "date": d.isoformat(),
        "message": get_horoscope(rashi, d)
    }


@app.get("/api/cities")
def api_cities():
    """List of preset cities for the location picker."""
    return {"cities": [{"id": k, **v} for k, v in CITIES.items()]}


@app.get("/api/panchang")
def api_panchang(
    date: str = Query(default=None, description="YYYY-MM-DD, defaults to today"),
    city: str = Query(default=None, description="City id from /api/cities, overrides lat/lon/tz"),
=======
@app.get("/api/panchang")
def api_panchang(
    date: str = Query(default=None, description="YYYY-MM-DD, defaults to today"),
>>>>>>> origin/main
    lat: float = Query(default=DEFAULT_LAT),
    lon: float = Query(default=DEFAULT_LON),
    tz: str = Query(default=DEFAULT_TZ),
):
    """Get full panchang for a single date."""
<<<<<<< HEAD
    if city and city in CITIES:
        c = CITIES[city]
        lat, lon, tz = c["lat"], c["lon"], c["tz"]

=======
>>>>>>> origin/main
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
<<<<<<< HEAD
    city: str = Query(default=None),
=======
>>>>>>> origin/main
    lat: float = Query(default=DEFAULT_LAT),
    lon: float = Query(default=DEFAULT_LON),
    tz: str = Query(default=DEFAULT_TZ),
):
    """Get a lightweight panchang summary (tithi + bengali date only) for every day in a Gregorian month."""
<<<<<<< HEAD
    if city and city in CITIES:
        c = CITIES[city]
        lat, lon, tz = c["lat"], c["lon"], c["tz"]
=======
>>>>>>> origin/main
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


<<<<<<< HEAD


# Search terms that people commonly use in Bengali or English.
SEARCH_ALIASES = {
    "শুভ দিন": ["shubho din", "shuvo din", "auspicious", "good day", "favourable day", "favorable day", "শুভ দিন", "শুভ সময়", "shubho", "বিয়ে", "বিবাহ", "গৃহপ্রবেশ", "নতুন কাজ"],
    "একাদশী": ["ekadashi", "ekadashi", "একাদশী"],
    "পূর্ণিমা": ["purnima", "full moon", "পূর্ণিমা"],
    "অমাবস্যা": ["amavasya", "new moon", "অমাবস্যা"],
    "দুর্গাপূজা": ["durga puja", "durga", "দুর্গাপূজা", "দুর্গা পুজো"],
    "কালীপূজা": ["kali puja", "diwali", "কালীপূজা", "দীপাবলি"],
    "সরস্বতী পূজা": ["saraswati puja", "saraswati", "সরস্বতী পূজা", "সরস্বতী পুজো"],
    "দোলযাত্রা": ["dol jatra", "holi", "দোল", "দোলযাত্রা", "হোলি"],
    "রথযাত্রা": ["rath yatra", "রথযাত্রা"],
    "জন্মাষ্টমী": ["janmashtami", "জন্মাষ্টমী"],
    "লক্ষ্মী পূজা": ["lakshmi puja", "লক্ষ্মী পূজা", "কোজাগরী"],
}

# These tithis are only broad, traditional auspicious-day search candidates;
# this is not a purpose-specific muhurta calculation (e.g. marriage dates).
GENERALLY_FAVOURABLE_TITHIS = {"Dwitiya", "Tritiya", "Panchami", "Saptami", "Dashami", "Ekadashi", "Trayodashi", "Purnima"}
BN_TITHI = {"Pratipad":"প্রতিপদ", "Dwitiya":"দ্বিতীয়া", "Tritiya":"তৃতীয়া", "Chaturthi":"চতুর্থী", "Panchami":"পঞ্চমী", "Sashthi":"ষষ্ঠী", "Saptami":"সপ্তমী", "Ashtami":"অষ্টমী", "Navami":"নবমী", "Dashami":"দশমী", "Ekadashi":"একাদশী", "Dwadashi":"দ্বাদশী", "Trayodashi":"ত্রয়োদশী", "Chaturdashi":"চতুর্দশী", "Purnima":"পূর্ণিমা", "Amavasya":"অমাবস্যা"}
BN_WEEKDAY = {"Sunday":"রবিবার", "Monday":"সোমবার", "Tuesday":"মঙ্গলবার", "Wednesday":"বুধবার", "Thursday":"বৃহস্পতিবার", "Friday":"শুক্রবার", "Saturday":"শনিবার"}
BN_NAKSHATRA = {"Ashwini":"অশ্বিনী", "Bharani":"ভরণী", "Krittika":"কৃত্তিকা", "Rohini":"রোহিণী", "Mrigashira":"মৃগশিরা", "Ardra":"আর্দ্রা", "Punarvasu":"পুনর্বসু", "Pushya":"পুষ্যা", "Ashlesha":"অশ্লেষা", "Magha":"মঘা", "Purva Phalguni":"পূর্ব ফাল্গুনী", "Uttara Phalguni":"উত্তর ফাল্গুনী", "Hasta":"হস্তা", "Chitra":"চিত্রা", "Swati":"স্বাতী", "Vishakha":"বিশাখা", "Anuradha":"অনুরাধা", "Jyeshtha":"জ্যেষ্ঠা", "Mula":"মূলা", "Purva Ashadha":"পূর্বাষাঢ়া", "Uttara Ashadha":"উত্তরাষাঢ়া", "Shravana":"শ্রবণা", "Dhanishtha":"ধনিষ্ঠা", "Shatabhisha":"শতভিষা", "Purva Bhadrapada":"পূর্বভাদ্রপদ", "Uttara Bhadrapada":"উত্তরভাদ্রপদ", "Revati":"রেবতী"}

@app.get("/api/search-days")
def api_search_days(
    q: str = Query(..., min_length=1, max_length=100),
    days: int = Query(default=365, ge=1, le=730),
    start: str = Query(default=None, description="Start date YYYY-MM-DD; defaults to today"),
    city: str = Query(default="kolkata"),
):
    """Search upcoming dates by tithi, nakshatra, weekday, festival, Bengali date, or broad auspicious-tithi candidates."""
    from datetime import date as date_type
    query = " ".join(q.lower().strip().split())
    start_date = datetime.strptime(start, "%Y-%m-%d").date() if start else datetime.now().date()
    city_data = CITIES.get(city, CITIES.get("kolkata"))
    aliases = []
    is_auspicious_search = any(term in query for term in [
        "শুভ দিন", "শুভ সময়", "shubho", "shuvo", "auspicious", "good day",
        "favourable day", "favorable day", "বিয়ে", "বিবাহ", "বিয়ের", "বিয়ের",
        "marriage", "wedding", "গৃহপ্রবেশ", "নতুন কাজ", "শুভ কাজ"
    ])
    for canonical, variants in SEARCH_ALIASES.items():
        if query == canonical.lower() or any(v in query for v in variants):
            aliases.extend(variants)
            aliases.append(canonical)
    terms = {query, *[x.lower() for x in aliases]}
    results = []
    for offset in range(days):
        d = start_date + timedelta(days=offset)
        full = get_full_panchang(datetime(d.year, d.month, d.day), lat=city_data["lat"], lon=city_data["lon"], tz_name=city_data["tz"])
        tithi = full["tithi"]["name"]
        weekday = full["weekday"]
        nakshatra = full["nakshatra"]["name"]
        yoga = full["yoga"]["name"]
        festival = get_festival(d.isoformat()) or ""
        bn_date = full["bengali_date"]
        searchable = " | ".join([
            d.isoformat(), weekday, BN_WEEKDAY.get(weekday, ""), tithi, BN_TITHI.get(tithi, ""),
            full["tithi"].get("paksha", ""), nakshatra, BN_NAKSHATRA.get(nakshatra, ""), yoga,
            festival, bn_date["month"], str(bn_date["day"]), str(bn_date["bengali_year"]),
            "ekadashi" if tithi == "Ekadashi" else "", "পূর্ণিমা" if tithi == "Purnima" else "",
            "অমাবস্যা" if tithi == "Amavasya" else ""
        ]).lower()
        matched = False
        reason = ""
        if is_auspicious_search:
            matched = tithi in GENERALLY_FAVOURABLE_TITHIS
            if matched:
                reason = f"সাধারণভাবে শুভ বলে বিবেচিত তিথি: {BN_TITHI.get(tithi, tithi)}"
        else:
            matched_terms = [term for term in terms if term and term in searchable]
            matched = bool(matched_terms)
            if matched:
                if festival and any(term in festival.lower() for term in matched_terms):
                    reason = festival
                elif tithi.lower() in matched_terms or BN_TITHI.get(tithi, "").lower() in matched_terms:
                    reason = f"তিথি: {BN_TITHI.get(tithi, tithi)}"
                elif nakshatra.lower() in matched_terms or BN_NAKSHATRA.get(nakshatra, "").lower() in matched_terms:
                    reason = f"নক্ষত্র: {BN_NAKSHATRA.get(nakshatra, nakshatra)}"
                else:
                    reason = "অনুসন্ধানের সঙ্গে মিলে যাওয়া পঞ্জিকার তথ্য"
        if matched:
            results.append({
                "date": d.isoformat(), "weekday": weekday, "weekday_bn": BN_WEEKDAY.get(weekday, full.get("weekday_bengali", weekday)),
                "tithi": tithi, "tithi_bn": BN_TITHI.get(tithi, tithi), "paksha": full["tithi"].get("paksha", ""),
                "nakshatra": nakshatra, "nakshatra_bn": BN_NAKSHATRA.get(nakshatra, nakshatra),
                "bengali_day": bn_date["day"], "bengali_month": bn_date["month"], "bengali_year": bn_date["bengali_year"],
                "festival": festival, "reason": reason, "auspicious_candidate": is_auspicious_search
            })
    return {"query": q, "start": start_date.isoformat(), "days_scanned": days, "count": len(results), "results": results,
            "mode": "auspicious_candidates" if is_auspicious_search else "text_search"}


=======
>>>>>>> origin/main
# Serve the frontend
app.mount("/", StaticFiles(directory="static", html=True), name="static")
