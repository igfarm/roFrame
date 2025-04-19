import requests
import random

def get_random_painting(aspect_ratio=16/9, deviation=0.1):
    base_url = "https://api.artic.edu/api/v1/artworks/search"
    
    params = {
        "fields": "id,title,artist_title,image_id,thumbnail",
        "query": "is_public_domain=true AND classification_title=Painting",
        "limit": 100,
        "page": random.randint(1, 100)  # randomize page
    }


    response = requests.get(base_url, params=params)
    data = response.json()

    paintings = data.get('data', [])

    # Image info is hosted separately via IIIF
    image_url_template = "https://www.artic.edu/iiif/2/{id}/full/843,/0/default.jpg"

    for painting in random.sample(paintings, len(paintings)):
        image_id = painting.get("image_id")
        if not image_id:
            continue

        # Fetch image dimensions
        iiif_metadata_url = f"https://www.artic.edu/iiif/2/{image_id}/info.json"
        info_response = requests.get(iiif_metadata_url)
        if info_response.status_code != 200:
            continue

        info = info_response.json()
        width = info.get("width")
        height = info.get("height")

        if not width or not height:
            continue

        actual_ratio = width / height
        if abs(actual_ratio - aspect_ratio) <= deviation:
            return {
                "title": painting.get("title", "Unknown"),
                "artist": painting.get("artist_title", "Unknown"),
                "image_url": image_url_template.format(id=image_id),
                "aspect_ratio": round(actual_ratio, 2)
            }

    return {"error": "No painting found matching aspect ratio criteria"}

