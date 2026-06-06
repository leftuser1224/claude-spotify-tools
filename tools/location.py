"""Location-based tools: weather and local time"""

import json
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

# City name → IANA timezone mapping for common cities
_CITY_TIMEZONE_MAP = {
    # Japan
    "tokyo": "Asia/Tokyo", "東京": "Asia/Tokyo",
    "osaka": "Asia/Tokyo", "大阪": "Asia/Tokyo",
    "kyoto": "Asia/Tokyo", "京都": "Asia/Tokyo",
    "sapporo": "Asia/Tokyo", "札幌": "Asia/Tokyo",
    "fukuoka": "Asia/Tokyo", "福岡": "Asia/Tokyo",
    "kobe": "Asia/Tokyo", "神戸": "Asia/Tokyo",
    "nagoya": "Asia/Tokyo", "名古屋": "Asia/Tokyo",
    "yokohama": "Asia/Tokyo", "横浜": "Asia/Tokyo",
    # US
    "new york": "America/New_York", "new york city": "America/New_York",
    "los angeles": "America/Los_Angeles", "la": "America/Los_Angeles",
    "chicago": "America/Chicago",
    "houston": "America/Chicago",
    "london": "Europe/London",
    # Europe
    "paris": "Europe/Paris",
    "berlin": "Europe/Berlin",
    "madrid": "Europe/Madrid",
    "rome": "Europe/Rome",
    "amsterdam": "Europe/Amsterdam",
    "moscow": "Europe/Moscow",
    # Asia
    "beijing": "Asia/Shanghai", "北京": "Asia/Shanghai",
    "shanghai": "Asia/Shanghai", "上海": "Asia/Shanghai",
    "seoul": "Asia/Seoul", "ソウル": "Asia/Seoul",
    "singapore": "Asia/Singapore",
    "hong kong": "Asia/Hong_Kong", "hongkong": "Asia/Hong_Kong",
    "bangkok": "Asia/Bangkok",
    "jakarta": "Asia/Jakarta",
    "dubai": "Asia/Dubai",
    "mumbai": "Asia/Kolkata", "delhi": "Asia/Kolkata",
    # Oceania
    "sydney": "Australia/Sydney",
    "melbourne": "Australia/Melbourne",
    "auckland": "Pacific/Auckland",
    # Americas
    "toronto": "America/Toronto",
    "vancouver": "America/Vancouver",
    "sao paulo": "America/Sao_Paulo",
    "mexico city": "America/Mexico_City",
}


async def get_weather(location: str) -> dict:
    """指定した場所の現在の天気を取得する (wttr.in API)

    Args:
        location: 都市名 (例: 'Tokyo', 'New York', '東京')

    Returns:
        天気・気温・現地時刻を含む辞書
    """
    try:
        location_encoded = urllib.parse.quote(location, safe="+")
        url = f"https://wttr.in/{location_encoded}?format=j1"

        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; weather-tool/1.0)"},
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())

        current = data.get("current_condition", [{}])[0]

        weather_desc = current.get("weatherDesc", [{}])[0].get("value", "Unknown")
        temp_c = current.get("temp_C")

        local_time = current.get("localObsDateTime", "")
        if not local_time:
            local_time = current.get("observation_time", "Unknown")

        return {
            "location": location,
            "weather": weather_desc,
            "temp_c": temp_c,
            "local_time": local_time,
            "success": True,
        }
    except Exception as e:
        return {"location": location, "success": False, "error": str(e)}


async def get_time(location: str = "Tokyo") -> dict:
    """指定した場所の現在時刻を取得する

    都市名をIANAタイムゾーンに変換してシステムのタイムゾーンDBから取得する。
    IANA タイムゾーン名 (例: 'Asia/Tokyo') を直接渡すこともできる。

    Args:
        location: 都市名 または IANA タイムゾーン名 (例: 'Tokyo', 'New York', 'Asia/Tokyo').
                  デフォルト: 'Tokyo'

    Returns:
        datetime, timezone, utc_offset, day_of_week, location を含む辞書
    """
    # IANA タイムゾーン名が直接渡された場合はそのまま使う
    timezone = location if "/" in location else _CITY_TIMEZONE_MAP.get(location.lower())

    if timezone:
        try:
            tz = ZoneInfo(timezone)
            now = datetime.now(tz)
            return {
                "location": location,
                "timezone": timezone,
                "datetime": now.isoformat(),
                "utc_offset": now.strftime("%z"),
                "day_of_week": now.strftime("%A"),
                "success": True,
            }
        except ZoneInfoNotFoundError:
            return {
                "location": location,
                "success": False,
                "error": f"Unknown timezone: {timezone}",
            }

    return {
        "location": location,
        "success": False,
        "error": f"Unknown location: '{location}'. Try an IANA timezone name like 'Asia/Tokyo'.",
    }
