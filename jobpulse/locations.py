"""
Location and city utilities for BDJobs API.

Provides mapping between city names and IDs for location-based filtering.
"""

from typing import Dict, List, Optional

# Bangladesh cities and their API IDs
from typing import Dict, List

CITY_ID_MAP: List[Dict[str, str]] = [
    {"id": "1003", "name": "Dhaka Division"},
    {"id": "14", "name": "Dhaka"},
    {"id": "16", "name": "Faridpur"},
    {"id": "19", "name": "Gazipur"},
    {"id": "20", "name": "Gopalganj"},
    {"id": "29", "name": "Kishoreganj"},
    {"id": "34", "name": "Madaripur"},
    {"id": "36", "name": "Manikganj"},
    {"id": "39", "name": "Munshiganj"},
    {"id": "43", "name": "Narayanganj"},
    {"id": "44", "name": "Narsingdi"},
    {"id": "53", "name": "Rajbari"},
    {"id": "58", "name": "Shariatpur"},
    {"id": "63", "name": "Tangail"},

    {"id": "1002", "name": "Chattogram Division"},
    {"id": "3", "name": "Bandarban"},
    {"id": "1", "name": "Brahmanbaria"},
    {"id": "8", "name": "Chandpur"},
    {"id": "10", "name": "Chattogram"},
    {"id": "13", "name": "Cox's Bazar"},
    {"id": "12", "name": "Cumilla"},
    {"id": "17", "name": "Feni"},
    {"id": "27", "name": "Khagrachhari"},
    {"id": "33", "name": "Lakshmipur"},
    {"id": "48", "name": "Noakhali"},
    {"id": "55", "name": "Rangamati"},

    {"id": "1001", "name": "Barishal Division"},
    {"id": "7", "name": "Barguna"},
    {"id": "4", "name": "Barishal"},
    {"id": "5", "name": "Bhola"},
    {"id": "24", "name": "Jhalakathi"},
    {"id": "51", "name": "Patuakhali"},
    {"id": "52", "name": "Pirojpur"},

    {"id": "1004", "name": "Khulna Division"},
    {"id": "2", "name": "Bagerhat"},
    {"id": "11", "name": "Chuadanga"},
    {"id": "23", "name": "Jashore"},
    {"id": "25", "name": "Jhenaidah"},
    {"id": "28", "name": "Khulna"},
    {"id": "31", "name": "Kushtia"},
    {"id": "35", "name": "Magura"},
    {"id": "37", "name": "Meherpur"},
    {"id": "42", "name": "Narail"},
    {"id": "57", "name": "Satkhira"},

    {"id": "1005", "name": "Mymensingh Division"},
    {"id": "22", "name": "Jamalpur"},
    {"id": "40", "name": "Mymensingh"},
    {"id": "46", "name": "Netrokona"},
    {"id": "59", "name": "Sherpur"},

    {"id": "1006", "name": "Rajshahi Division"},
    {"id": "6", "name": "Bogura"},
    {"id": "9", "name": "Chapainawabganj"},
    {"id": "26", "name": "Joypurhat"},
    {"id": "41", "name": "Naogaon"},
    {"id": "45", "name": "Natore"},
    {"id": "49", "name": "Pabna"},
    {"id": "54", "name": "Rajshahi"},
    {"id": "60", "name": "Sirajganj"},

    {"id": "1007", "name": "Rangpur Division"},
    {"id": "15", "name": "Dinajpur"},
    {"id": "18", "name": "Gaibandha"},
    {"id": "30", "name": "Kurigram"},
    {"id": "32", "name": "Lalmonirhat"},
    {"id": "47", "name": "Nilphamari"},
    {"id": "50", "name": "Panchagarh"},
    {"id": "56", "name": "Rangpur"},
    {"id": "64", "name": "Thakurgaon"},

    {"id": "1008", "name": "Sylhet Division"},
    {"id": "21", "name": "Habiganj"},
    {"id": "38", "name": "Moulvibazar"},
    {"id": "61", "name": "Sunamganj"},
    {"id": "62", "name": "Sylhet"},
]


def get_city_id(city_name: str) -> Optional[str]:
    """
    Get city ID by name for location filtering.

    Args:
        city_name: Name of the city (case-insensitive)

    Returns:
        City ID if found, None otherwise

    Example:
        >>> get_city_id("Dhaka")
        "10"
        >>> get_city_id("Unknown City")
        None
    """
    if not city_name:
        return None

    city_name_lower = city_name.lower().strip()

    for city in CITY_ID_MAP:
        if city["name"].lower() == city_name_lower:
            return city["id"]

    return None


def get_city_name(city_id: str) -> Optional[str]:
    """
    Get city name by ID.

    Args:
        city_id: ID of the city

    Returns:
        City name if found, None otherwise

    Example:
        >>> get_city_name("10")
        "Chattogram"
        >>> get_city_name("999")
        None
    """
    if not city_id:
        return None

    for city in CITY_ID_MAP:
        if city["id"] == city_id:
            return city["name"]

    return None


def get_all_cities() -> List[Dict[str, str]]:
    """
    Get all available cities.

    Returns:
        List of dictionaries with 'id' and 'name' keys

    Example:
        >>> cities = get_all_cities()
        >>> len(cities) > 0
        True
    """
    return CITY_ID_MAP.copy()


def search_cities(query: str) -> List[Dict[str, str]]:
    """
    Search for cities by partial name match.

    Args:
        query: Search query (case-insensitive)

    Returns:
        List of matching cities

    Example:
        >>> results = search_cities("dhaka")
        >>> len(results) > 0
        True
    """
    if not query:
        return []

    query_lower = query.lower().strip()

    return [city for city in CITY_ID_MAP if query_lower in city["name"].lower()]
