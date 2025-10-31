import requests
import logging

logger = logging.getLogger(__name__)

def get_road_distance(from_lat, from_lng, to_lat, to_lng):
    """
    Get real road distance between two points using OSRM API.
    
    Returns:
        distance_km (float): Real road distance in kilometers
        duration_seconds (int): Expected travel time in seconds
    """
    try:
        # OSRM API endpoint
        url = f"https://router.project-osrm.org/route/v1/driving/{from_lng},{from_lat};{to_lng},{to_lat}"
        params = {
            'overview': 'false',  # We don't need the full route geometry
            'steps': 'false'
        }
        
        logger.info(f"🌐 Requesting OSRM route from ({from_lat},{from_lng}) to ({to_lat},{to_lng})")
        
        response = requests.get(url, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('code') == 'Ok' and data.get('routes'):
                route = data['routes'][0]
                distance_meters = route['distance']  # meters
                duration_seconds = route['duration']  # seconds
                
                distance_km = distance_meters / 1000.0
                
                logger.info(f"✅ OSRM returned: {distance_km:.2f} km, {duration_seconds:.0f} seconds")
                
                return distance_km, duration_seconds
            else:
                logger.warning(f"⚠️ OSRM returned no route: {data.get('code')}")
                return None, None
        else:
            logger.error(f"❌ OSRM request failed: {response.status_code}")
            return None, None
            
    except requests.Timeout:
        logger.error("❌ OSRM request timeout")
        return None, None
    except Exception as e:
        logger.exception(f"❌ Error getting road distance: {e}")
        return None, None


def get_road_distance_with_fallback(from_lat, from_lng, to_lat, to_lng):
    """
    Get road distance with fallback to straight-line if API fails.
    
    Returns:
        distance_km (float): Distance in kilometers
        is_road_distance (bool): True if real road distance, False if straight-line
    """
    import math
    
    # Try to get real road distance
    road_dist, _ = get_road_distance(from_lat, from_lng, to_lat, to_lng)
    
    if road_dist is not None:
        return road_dist, True
    
    # Fallback to straight-line distance (Haversine)
    logger.warning("⚠️ Falling back to straight-line distance")
    
    R = 6371  # Earth radius in km
    phi1 = math.radians(from_lat)
    phi2 = math.radians(to_lat)
    dphi = math.radians(to_lat - from_lat)
    dlambda = math.radians(to_lng - from_lng)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    straight_dist = R * c
    
    # Multiply by 1.3 to approximate road distance (roads aren't straight)
    estimated_road_dist = straight_dist * 1.3
    
    return estimated_road_dist, False