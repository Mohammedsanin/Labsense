import os
import logging
import googlemaps
from datetime import datetime

def find_nearby_hospitals(location: str, radius: int = 5000):
    """Find nearby hospitals using Google Maps Places API"""
    try:
        api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
        if not api_key:
            return {"error": "Google Maps API key not configured"}
        
        gmaps = googlemaps.Client(key=api_key)
        
        geocode_result = gmaps.geocode(location)
        if not geocode_result:
            return {"error": "Location not found"}
        
        lat = geocode_result[0]['geometry']['location']['lat']
        lng = geocode_result[0]['geometry']['location']['lng']
        
        places_result = gmaps.places_nearby(
            location=(lat, lng),
            radius=radius,
            type='hospital'
        )
        
        hospitals = []
        for place in places_result.get('results', [])[:10]:
            hospital_info = {
                'name': place.get('name', 'Unknown'),
                'address': place.get('vicinity', 'Address not available'),
                'rating': place.get('rating', 'N/A'),
                'lat': place['geometry']['location']['lat'],
                'lng': place['geometry']['location']['lng'],
                'open_now': place.get('opening_hours', {}).get('open_now', None)
            }
            hospitals.append(hospital_info)
        
        return {
            'center': {'lat': lat, 'lng': lng},
            'hospitals': hospitals
        }
        
    except Exception as e:
        logging.error(f"Maps error: {e}")
        return {"error": str(e)}

def get_directions(origin: str, destination: str):
    """Get directions between two locations"""
    try:
        api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
        if not api_key:
            return {"error": "Google Maps API key not configured"}
        
        gmaps = googlemaps.Client(key=api_key)
        
        directions_result = gmaps.directions(
            origin,
            destination,
            mode="driving",
            departure_time=datetime.now()
        )
        
        if directions_result:
            route = directions_result[0]
            leg = route['legs'][0]
            return {
                'distance': leg['distance']['text'],
                'duration': leg['duration']['text'],
                'steps': [step['html_instructions'] for step in leg['steps']]
            }
        else:
            return {"error": "No route found"}
            
    except Exception as e:
        logging.error(f"Directions error: {e}")
        return {"error": str(e)}
