"""
Repo: https://github.com/ruirzma/Amsterdam_SVI_Building
Author: Rui Ma
Time: 2024.06.04

"""

import json
import requests
from io import BytesIO
from PIL import Image

def send_get_request(url):
    """
    Send a GET request to the specified URL and return the JSON content.
    
    Args:
    url (str): URL to send the GET request to.
    
    Returns:
    dict: JSON response from the server.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises stored HTTPError, if one occurred.
        return json.loads(response.content)
    except requests.exceptions.RequestException as e:
        print(f'Request failed: {e}')
        return None

def construct_pano_url(mission_year, bbox):
    """
    Construct the URL for panorama API requests.
    
    Args:
    mission_year (int): The year of the mission.
    bbox (tuple): Bounding box coordinates.
    
    Returns:
    str: Constructed URL.
    """
    base_url = "https://api.data.amsterdam.nl/panorama/panoramas/"
    params = f"tags=mission-{mission_year}&bbox={bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}&srid=28992"
    return base_url + "?" + params

def fetch_panorama_ids(mission_year, bbox):
    """
    Retrieve panorama IDs for a defined bounding box and mission year.
    Handles API pagination to collect all relevant IDs.
    """
    pano_url = construct_pano_url(mission_year, bbox)
    panorama_ids = []

    while pano_url:
        data = send_get_request(pano_url)
        if data is None:
            break

        panoramas = data['_embedded']['panoramas']
        panorama_ids.extend([item['pano_id'] for item in panoramas])

        pano_url = data['_links'].get('next', {}).get('href')

    return panorama_ids

def fetch_panorama_image(pano_id):
    """
    Fetch a panoramic image using its ID and return the image along with its geographical coordinates.
    """
    pano_url = f"https://api.data.amsterdam.nl/panorama/panoramas/{pano_id}/"
    pano_data = send_get_request(pano_url)
    if pano_data is None:
        return None, None

    image_location = pano_data['geometry']['coordinates']
    image = Image.open(BytesIO(requests.get(pano_data['_links']['equirectangular_medium']['href']).content))
    return image, image_location

def search_buildings(observer, radius):
    """
    Search for building data within a specified radius around a location.
    """
    bag_url = f"https://api.data.amsterdam.nl/bag/v1.1/pand/?format=json&locatie={observer[0]}%2C{observer[1]}%2C{radius}"

    return send_get_request(bag_url)['results']

def fetch_building_polygons(building_data):
    """
    Extract polygon data for buildings from the provided JSON.
    """
    building_polygons = {}
    for item in building_data:
        building_details = send_get_request(item['_links']['self']['href'])
        if building_details is None:
            continue

        building_id = building_details['pandidentificatie']
        polygon = building_details['geometrie']['coordinates'][0]

        if len(polygon) > 2 and building_id:
            building_polygons[building_id] = polygon

    return building_polygons

def download_panorama_image(image_url):
    """
    Download a panoramic image from the specified URL.
    """
    try:
        response = requests.get(image_url)
        return Image.open(BytesIO(response.content))
    except requests.exceptions.RequestException as e:
        print(f'HTTP Request failed: {e}')
        return None
