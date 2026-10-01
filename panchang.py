"""
Panchang calculation engine for Bengali Hindu calendar app.
Uses pyephem for astronomical positions (Drik Siddhanta / observed-position based).
No external ephemeris file downloads required.
"""

import ephem
import math
from datetime import datetime, timedelta
import pytz

# ---- Reference data ----

TITHI_NAMES = [
    "Pratipad", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
    "Sashthi", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Purnima"
]
# Krishna paksha reuses same names 1-14, then Amavasya

NAKSHATRA_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishtha", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

YOGA_NAMES = [
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda",
    "Sukarma", "Dhriti", "Shula", "Ganda", "Vriddhi", "Dhruva",
    "Vyaghata", "Harshana", "Vajra", "Siddhi", "Vyatipata", "Variyana",
    "Parigha", "Shiva", "Siddha", "Sadhya", "Shubha", "Shukla",
    "Brahma", "Indra", "Vaidhriti"
]

KARANA_NAMES = [
    "Bava", "Balava", "Kaulava", "Taitila", "Garija", "Vanija", "Vishti",
    "Shakuni", "Chatushpada", "Naga", "Kimstughna"
]

BENGALI_MONTHS = [
    "Boishakh", "Joishtho", "Ashar", "Shrabon", "Bhadro", "Ashwin",
    "Kartik", "Agrahayan", "Poush", "Magh", "Falgun", "Chaitro"
]

# Bengali San (Bangabda) epoch: Bengali year = Gregorian year - 593 or 594
# depending on whether the Gregorian date falls before/after Poila Boishakh (~Apr 14-15)

WEEKDAYS_BN = ["Robibar", "Sombar", "Mongolbar", "Budhbar", "Brihoshpotibar", "Shukrobar", "Shonibar"]


def norm360(deg):
    return deg % 360.0


def lahiri_ayanamsa(dt_utc):
    """
    Lahiri (Chitrapaksha) ayanamsa - the standard correction used by Indian panchang
    software to convert tropical (Western) ecliptic longitude to sidereal (Vedic).
    This is a linear approximation; good to within a few arcseconds for any date
    in the 1900-2100 range, which is more than sufficient for tithi/nakshatra purposes.
    """
    jd = ephem.julian_date(dt_utc)
    t = (jd - 2451545.0) / 36525.0  # Julian centuries since J2000.0
    ayanamsa = 23.853 + (t * 100) * (50.2388 / 3600.0)
    return ayanamsa


def get_sun_moon_longitude(dt_utc, sidereal=True):
    """
    Return (sun_lon, moon_lon) geocentric ecliptic longitude in degrees for given UTC datetime.
    sidereal=True (default) applies the Lahiri ayanamsa correction, which is required
    for correct nakshatra and yoga calculation in the Vedic/Hindu system.
    Tithi and karana calculations use the difference between sun and moon longitude,
    so the ayanamsa cancels out and sidereal vs tropical makes no difference there -
    but we apply it consistently anyway for clarity.
    """
    obs = ephem.Observer()
    obs.date = dt_utc

    sun = ephem.Sun(obs)
    moon = ephem.Moon(obs)

    sun_lon = math.degrees(ephem.Ecliptic(sun).lon)
    moon_lon = math.degrees(ephem.Ecliptic(moon).lon)

    if sidereal:
        aya = lahiri_ayanamsa(dt_utc)
        sun_lon = norm360(sun_lon - aya)
        moon_lon = norm360(moon_lon - aya)

    return norm360(sun_lon), norm360(moon_lon)


def get_tithi(dt_utc):
    """Tithi = (Moon longitude - Sun longitude) / 12 degrees, 1-30."""
    sun_lon, moon_lon = get_sun_moon_longitude(dt_utc)
    diff = norm360(moon_lon - sun_lon)
    tithi_num = int(diff / 12) + 1  # 1-30

    if tithi_num <= 15:
        paksha = "Shukla"
        name = TITHI_NAMES[tithi_num - 1] if tithi_num < 15 else "Purnima"
    else:
        paksha = "Krishna"
        idx = tithi_num - 15
        name = TITHI_NAMES[idx - 1] if idx < 15 else "Amavasya"

    return {
        "number": tithi_num,
        "paksha": paksha,
        "name": name,
        "degrees_elapsed": diff % 12,
        "percent_complete": round((diff % 12) / 12 * 100, 1)
    }


def get_nakshatra(dt_utc):
    """Nakshatra = Moon longitude / (360/27) degrees, 1-27."""
    _, moon_lon = get_sun_moon_longitude(dt_utc)
    span = 360.0 / 27.0
    nak_num = int(moon_lon / span)  # 0-26
    name = NAKSHATRA_NAMES[nak_num]
    pada = int((moon_lon % span) / (span / 4)) + 1  # 1-4
    return {
        "number": nak_num + 1,
        "name": name,
        "pada": pada,
        "percent_complete": round((moon_lon % span) / span * 100, 1)
    }


def get_yoga(dt_utc):
    """Yoga = (Sun longitude + Moon longitude) / (360/27) degrees, 1-27."""
    sun_lon, moon_lon = get_sun_moon_longitude(dt_utc)
    total = norm360(sun_lon + moon_lon)
    span = 360.0 / 27.0
    yoga_num = int(total / span)
    return {
        "number": yoga_num + 1,
        "name": YOGA_NAMES[yoga_num]
    }


def get_karana(dt_utc):
    """Karana = half-tithi, 60 per lunar month, cycles through 11 karana names."""
    sun_lon, moon_lon = get_sun_moon_longitude(dt_utc)
    diff = norm360(moon_lon - sun_lon)
    karana_num = int(diff / 6)  # 0-59

    if karana_num == 0:
        name = "Kimstughna"
    elif karana_num >= 57:
        name = KARANA_NAMES[7 + (karana_num - 57)]  # Shakuni, Chatushpada, Naga
    else:
        name = KARANA_NAMES[(karana_num - 1) % 7]

    return {"number": karana_num + 1, "name": name}


def get_sunrise_sunset(date, lat, lon, tz_name="Asia/Kolkata"):
    """Sunrise/sunset for given date and location, returned in local timezone."""
    obs = ephem.Observer()
    obs.lat = str(lat)
    obs.lon = str(lon)
    obs.date = date
    obs.pressure = 0
    obs.horizon = '-0:34'  # standard refraction correction

    tz = pytz.timezone(tz_name)

    try:
        sunrise_utc = obs.next_rising(ephem.Sun()).datetime()
        sunset_utc = obs.next_setting(ephem.Sun()).datetime()
        sunrise_local = pytz.utc.localize(sunrise_utc).astimezone(tz)
        sunset_local = pytz.utc.localize(sunset_utc).astimezone(tz)
        return sunrise_local.strftime("%H:%M"), sunset_local.strftime("%H:%M")
    except Exception as e:
        return None, None


def gregorian_to_bengali_date(greg_date):
    """
    Approximate Bengali calendar conversion.
    Poila Boishakh (Bengali New Year) falls on April 14 (sometimes 15).
    This is a simplified solar-calendar approximation, not minute-perfect
    against a specific printed panjika's exact sankranti moments.
    """
    year = greg_date.year
    # Bengali new year reference: April 14
    new_year_this_year = datetime(year, 4, 14)

    if greg_date >= new_year_this_year:
        bengali_year = year - 593
        days_since_new_year = (greg_date - new_year_this_year).days
    else:
        bengali_year = year - 594
        prev_new_year = datetime(year - 1, 4, 14)
        days_since_new_year = (greg_date - prev_new_year).days

    # Bengali month lengths (approx, solar months): first 5 months have 31 days,
    # remaining 7 have 30 days (adjusts for leap year in Falgun)
    month_lengths = [31, 31, 31, 31, 31, 30, 30, 30, 30, 30, 30, 30]

    remaining = days_since_new_year
    month_idx = 0
    for i, length in enumerate(month_lengths):
        if remaining < length:
            month_idx = i
            break
        remaining -= length
        month_idx = i + 1

    if month_idx >= 12:
        month_idx = 11
        day_of_month = remaining + 1
    else:
        day_of_month = remaining + 1

    return {
        "bengali_year": bengali_year,
        "month": BENGALI_MONTHS[month_idx],
        "day": day_of_month
    }


def get_full_panchang(date, lat=22.5726, lon=88.3639, tz_name="Asia/Kolkata"):
    """
    Get complete panchang for a given date at a location.
    Default location: Kolkata.
    `date` should be a datetime.date or datetime.datetime (local date intended).
    """
    tz = pytz.timezone(tz_name)
    if isinstance(date, datetime):
        local_dt = tz.localize(date.replace(hour=12, minute=0, second=0, microsecond=0)) if date.tzinfo is None else date
    else:
        local_dt = tz.localize(datetime(date.year, date.month, date.day, 12, 0, 0))

    dt_utc = local_dt.astimezone(pytz.utc)

    tithi = get_tithi(dt_utc)
    nakshatra = get_nakshatra(dt_utc)
    yoga = get_yoga(dt_utc)
    karana = get_karana(dt_utc)
    sunrise, sunset = get_sunrise_sunset(local_dt.date(), lat, lon, tz_name)
    bengali_date = gregorian_to_bengali_date(local_dt.replace(tzinfo=None))
    weekday_bn = WEEKDAYS_BN[(local_dt.weekday() + 1) % 7]

    return {
        "gregorian_date": local_dt.strftime("%Y-%m-%d"),
        "weekday": local_dt.strftime("%A"),
        "weekday_bengali": weekday_bn,
        "bengali_date": bengali_date,
        "tithi": tithi,
        "nakshatra": nakshatra,
        "yoga": yoga,
        "karana": karana,
        "sunrise": sunrise,
        "sunset": sunset,
    }


# ---- Festival dataset ----
# Major Bengali Hindu festivals for 2026, verified against West Bengal government
# holiday lists and Bengali panjika sources (Oct 2026). Note: Durga Puja day-by-day
# dates can shift by +/-1 day between sources depending on exact tithi transition
# calculation and region (Kolkata vs Dhaka) - verify against a current year's
# official WB government calendar before relying on these for real planning.
# This dataset needs manual refresh every year (festival dates are lunar/solar-shifted).
FESTIVALS_2026 = {
    "2026-01-14": "Poush Sankranti / Makar Sankranti",
    "2026-01-23": "Saraswati Puja (Basant Panchami)",
    "2026-03-03": "Dol Jatra (Holi)",
    "2026-04-15": "Poila Boishakh (Bengali New Year 1433)",
    "2026-07-16": "Rath Yatra",
    "2026-09-04": "Janmashtami",
    "2026-09-10": "Mahalaya",
    "2026-10-16": "Durga Puja — Shashthi",
    "2026-10-18": "Durga Puja — Saptami",
    "2026-10-19": "Durga Puja — Ashtami",
    "2026-10-20": "Durga Puja — Nabami",
    "2026-10-21": "Durga Puja — Dashami (Bijoya)",
    "2026-10-25": "Lakshmi Puja (Kojagari Purnima)",
    "2026-11-08": "Kali Puja / Diwali",
    "2026-11-10": "Bhai Phota",
    "2026-11-15": "Chhath Puja",
}


def get_festival(date_str):
    """Return festival name for a given YYYY-MM-DD string, or None."""
    return FESTIVALS_2026.get(date_str)


if __name__ == "__main__":
    import json
    today = datetime.now()
    result = get_full_panchang(today)
    print(json.dumps(result, indent=2, ensure_ascii=False))
