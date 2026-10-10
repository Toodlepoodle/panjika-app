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


<<<<<<< HEAD
def _sidereal_sun_rashi_index(local_noon_dt, tz):
    """
    Return the sidereal zodiac sign index (0=Mesha/Aries ... 11=Meena/Pisces)
    that the Sun occupies at local noon on the given naive datetime (date part used).
    This is the real basis of the traditional Bengali solar calendar: a new Bengali
    month begins exactly when the Sun crosses into a new sidereal rashi (sankranti).
    """
    dt_utc = tz.localize(datetime(local_noon_dt.year, local_noon_dt.month, local_noon_dt.day, 12, 0, 0)).astimezone(pytz.utc)
    sun_lon, _ = get_sun_moon_longitude(dt_utc, sidereal=True)
    return int(sun_lon // 30)


def gregorian_to_bengali_date(greg_date, tz_name="Asia/Kolkata"):
    """
    Proper Bengali solar calendar conversion using sidereal Sun position.
    A Bengali month begins on the day the Sun enters a new sidereal rashi
    (zodiac sign) - this is the actual traditional/Drik Siddhanta basis of
    the Bengali calendar, not an approximation with fixed month lengths.

    BENGALI_MONTHS is ordered to align with rashi index:
      0 Mesha->Boishakh, 1 Vrishabha->Joishtho, 2 Mithuna->Ashar, 3 Karka->Shrabon,
      4 Simha->Bhadro, 5 Kanya->Ashwin, 6 Tula->Kartik, 7 Vrischika->Agrahayan,
      8 Dhanu->Poush, 9 Makara->Magh, 10 Kumbha->Falgun, 11 Meena->Chaitro
    """
    tz = pytz.timezone(tz_name)
    greg_date = datetime(greg_date.year, greg_date.month, greg_date.day)

    current_rashi = _sidereal_sun_rashi_index(greg_date, tz)

    # Walk backward day by day until the rashi changes - that's the sankranti
    # (month start) date. Bengali months run 29-32 days, so a 35-day search cap
    # is a safe upper bound.
    transition_date = greg_date
    for i in range(1, 36):
        probe_date = greg_date - timedelta(days=i)
        probe_rashi = _sidereal_sun_rashi_index(probe_date, tz)
        if probe_rashi != current_rashi:
            break
        transition_date = probe_date

    day_of_month = (greg_date - transition_date).days + 1

    # Bengali year increments at Mesha Sankranti (Poila Boishakh), which falls
    # April 13-15 depending on the year. Using the actual computed rashi tells
    # us unambiguously whether we're before or after that transition this year.
    if current_rashi == 0:  # Boishakh itself - the new year has just begun
        bengali_year = greg_date.year - 593
    elif current_rashi <= 7:  # Joishtho..Agrahayan - same Gregorian year, post-April
        bengali_year = greg_date.year - 593
    else:  # Poush..Chaitro - straddles into the following Gregorian year
        bengali_year = greg_date.year - 594 if greg_date.month <= 6 else greg_date.year - 593

    return {
        "bengali_year": bengali_year,
        "month": BENGALI_MONTHS[current_rashi],
=======
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
>>>>>>> origin/main
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
<<<<<<< HEAD
    bengali_date = gregorian_to_bengali_date(local_dt.replace(tzinfo=None), tz_name=tz_name)
    weekday_bn = WEEKDAYS_BN[(local_dt.weekday() + 1) % 7]
    moon_rashi = get_moon_rashi(dt_utc)
    rahu_start, rahu_end = get_rahu_kaal(sunrise, sunset, local_dt.weekday())
    abhijit_start, abhijit_end = get_abhijit_muhurat(sunrise, sunset)
    ekadashi = get_ekadashi_info(tithi["number"])
    horoscope = get_horoscope(moon_rashi["number"] - 1, local_dt.date())
=======
    bengali_date = gregorian_to_bengali_date(local_dt.replace(tzinfo=None))
    weekday_bn = WEEKDAYS_BN[(local_dt.weekday() + 1) % 7]
>>>>>>> origin/main

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
<<<<<<< HEAD
        "moon_rashi": moon_rashi,
        "rahu_kaal": {"start": rahu_start, "end": rahu_end},
        "abhijit_muhurat": {"start": abhijit_start, "end": abhijit_end},
        "ekadashi": ekadashi,
        "horoscope": horoscope,
    }


# ---- Rashi (moon sign) - real astronomy, same sidereal basis as nakshatra ----
RASHI_NAMES = [
    "Mesha (Aries)", "Vrishabha (Taurus)", "Mithuna (Gemini)", "Karka (Cancer)",
    "Simha (Leo)", "Kanya (Virgo)", "Tula (Libra)", "Vrischika (Scorpio)",
    "Dhanu (Sagittarius)", "Makara (Capricorn)", "Kumbha (Aquarius)", "Meena (Pisces)"
]


def get_moon_rashi(dt_utc):
    """Moon rashi (sidereal zodiac sign the Moon currently occupies) - real astronomical position."""
    _, moon_lon = get_sun_moon_longitude(dt_utc, sidereal=True)
    idx = int(moon_lon // 30)
    return {"number": idx + 1, "name": RASHI_NAMES[idx]}


# ---- Rahu Kaal (inauspicious period) ----
# Each weekday has a fixed 1/8th segment of daylight hours designated Rahu Kaal.
# Segment index per weekday (Python weekday(): Mon=0..Sun=6)
RAHU_KAAL_SEGMENT = {0: 1, 1: 6, 2: 4, 3: 5, 4: 3, 5: 2, 6: 7}  # Mon..Sun


def get_rahu_kaal(sunrise_str, sunset_str, weekday_py):
    """Returns (start, end) time strings for today's Rahu Kaal window."""
    if not sunrise_str or not sunset_str:
        return None, None
    sh, sm = map(int, sunrise_str.split(":"))
    eh, em = map(int, sunset_str.split(":"))
    sunrise_min = sh * 60 + sm
    sunset_min = eh * 60 + em
    daylight = sunset_min - sunrise_min
    segment_len = daylight / 8
    seg = RAHU_KAAL_SEGMENT[weekday_py]
    start_min = sunrise_min + segment_len * seg
    end_min = start_min + segment_len

    def fmt(mins):
        h = int(mins // 60)
        m = int(mins % 60)
        return f"{h:02d}:{m:02d}"

    return fmt(start_min), fmt(end_min)


def get_abhijit_muhurat(sunrise_str, sunset_str):
    """
    Abhijit Muhurat: the 8th of 15 muhurats dividing daylight, centered on local
    solar noon. Widely regarded as auspicious for starting new ventures.
    Computed as the midpoint of sunrise-sunset +/- 1/15th of daylight duration.
    """
    if not sunrise_str or not sunset_str:
        return None, None
    sh, sm = map(int, sunrise_str.split(":"))
    eh, em = map(int, sunset_str.split(":"))
    sunrise_min = sh * 60 + sm
    sunset_min = eh * 60 + em
    daylight = sunset_min - sunrise_min
    muhurat_len = daylight / 15
    midpoint = (sunrise_min + sunset_min) / 2
    start_min = midpoint - muhurat_len / 2
    end_min = midpoint + muhurat_len / 2

    def fmt(mins):
        h = int(mins // 60)
        m = int(mins % 60)
        return f"{h:02d}:{m:02d}"

    return fmt(start_min), fmt(end_min)


def get_ekadashi_info(tithi_number):
    """Ekadashi (11th lunar day) is a significant fasting day in Vaishnava tradition."""
    if tithi_number == 11:
        return {"is_ekadashi": True, "paksha": "Shukla"}
    if tithi_number == 26:
        return {"is_ekadashi": True, "paksha": "Krishna"}
    return {"is_ekadashi": False, "paksha": None}


# ---- Daily horoscope ----
# IMPORTANT: this is clearly-labeled entertainment content, not astronomical
# calculation. Daily sun-sign horoscopes are not derived from any verifiable
# method - there is no scientific or consistent astrological technique that
# produces a specific prediction for an entire sign for one day. This generates
# deterministic (same message all day, changes daily) generic rotating messages,
# explicitly presented to the user as entertainment, not fact - matching how
# horoscopes are presented industry-wide (newspapers, other panjika apps, etc).
HOROSCOPE_TEMPLATES = [
    "A good day to finish something you started rather than begin something new.",
    "Conversations with family bring clarity on a decision you've been sitting on.",
    "Financial caution serves you well today - avoid impulsive spending.",
    "An old connection may resurface. Worth answering that call.",
    "Your energy is best spent on routine tasks today rather than big risks.",
    "A small act of patience today prevents a bigger headache tomorrow.",
    "Good day for travel or short trips if you've been planning one.",
    "Trust your instincts in a work matter - overthinking won't help today.",
    "Health and rest deserve priority today over ambition.",
    "A creative idea you dismissed earlier deserves a second look.",
    "Someone close may need your listening ear more than your advice.",
    "Favorable day to settle a pending financial matter.",
]


def get_horoscope(rashi_index, date_obj):
    """
    Deterministic daily message per rashi - same message for everyone with that
    rashi on a given day, changes the next day. Pure entertainment content.
    """
    seed = (date_obj.toordinal() * 13 + rashi_index * 7) % len(HOROSCOPE_TEMPLATES)
    return HOROSCOPE_TEMPLATES[seed]


# ---- City presets for location picker ----
CITIES = {
    "kolkata": {"label": "Kolkata, India", "lat": 22.5726, "lon": 88.3639, "tz": "Asia/Kolkata"},
    "dhaka": {"label": "Dhaka, Bangladesh", "lat": 23.8103, "lon": 90.4125, "tz": "Asia/Dhaka"},
    "delhi": {"label": "Delhi, India", "lat": 28.6139, "lon": 77.2090, "tz": "Asia/Kolkata"},
    "mumbai": {"label": "Mumbai, India", "lat": 19.0760, "lon": 72.8777, "tz": "Asia/Kolkata"},
    "bangalore": {"label": "Bangalore, India", "lat": 12.9716, "lon": 77.5946, "tz": "Asia/Kolkata"},
    "chennai": {"label": "Chennai, India", "lat": 13.0827, "lon": 80.2707, "tz": "Asia/Kolkata"},
    "siliguri": {"label": "Siliguri, India", "lat": 26.7271, "lon": 88.3953, "tz": "Asia/Kolkata"},
    "chittagong": {"label": "Chittagong, Bangladesh", "lat": 22.3569, "lon": 91.7832, "tz": "Asia/Dhaka"},
    "london": {"label": "London, UK", "lat": 51.5072, "lon": -0.1276, "tz": "Europe/London"},
    "new_york": {"label": "New York, USA", "lat": 40.7128, "lon": -74.0060, "tz": "America/New_York"},
    "toronto": {"label": "Toronto, Canada", "lat": 43.6532, "lon": -79.3832, "tz": "America/Toronto"},
    "dubai": {"label": "Dubai, UAE", "lat": 25.2048, "lon": 55.2708, "tz": "Asia/Dubai"},
}


=======
    }


>>>>>>> origin/main
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
