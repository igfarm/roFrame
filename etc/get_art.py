import requests
import os
import time
import sys

#
# Get some images from the Art Institute of Chicago API
#
def get_random_art(orientation="landscape"):
    url = "https://api.artic.edu/api/v1/artworks/search"
    params = {
        "page": 5,
        "query[term][is_public_domain]": "true",
        "limit": 100,  # Fetch more results to increase chances of desired orientation
        "fields": "id,title,image_id,artwork_type_title,thumbnail.width,thumbnail.height"
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        return "Error fetching data."

    data = response.json()
    artworks = data.get("data", [])

    # Filter artworks by artwork_type_title
    valid_types = {"Painting"}
    artworks = [
        art for art in artworks 
        if art.get("artwork_type_title") in valid_types
    ]

    # Filter artworks with valid image_id and specified orientation
    if orientation == "landscape":
        valid_artworks = [
            art for art in artworks 
            if art.get("image_id") 
            and art.get("thumbnail", {}).get("width", 0) > art.get("thumbnail", {}).get("height", 0)
            and art.get("thumbnail", {}).get("width", 0) / art.get("thumbnail", {}).get("height", 1) >= 1.3
        ]
    elif orientation == "portrait":
        valid_artworks = [
            art for art in artworks 
            if art.get("image_id") 
            and art.get("thumbnail", {}).get("width", 0) < art.get("thumbnail", {}).get("height", 0)
        ]
    else:
        return "Invalid orientation specified. Use 'landscape' or 'portrait'."

    if not valid_artworks:
        return f"No {orientation} open-access images found."

    for artwork in valid_artworks:
        image_id = artwork["image_id"]
        image_url = f"https://www.artic.edu/iiif/2/{image_id}/full/1024,/0/default.jpg"
        save_image(image_url, image_id, orientation)

def save_image(image_url, image_id, orientation="landscape"):
    """Downloads and saves the image locally."""
    print("Downloading image:", image_url)
    response = requests.get(image_url, stream=True)
    if response.status_code == 200:
        os.makedirs("art_images", exist_ok=True)  # Ensure directory exists
        image_path = f"pictures/art_{orientation}_{image_id}.jpg"
        with open(image_path, "wb") as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        time.sleep(1)  # Be kind to the API
        print("Image saved to:", image_path)
    else:
        print("Failed to download image:", image_url)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python get_art.py <orientation>")
        print("Orientation must be 'landscape' or 'portrait'.")
        sys.exit(1)

    orientation = sys.argv[1].lower()
    result = get_random_art(orientation=orientation)
    if isinstance(result, str):  # Handle error or no results message
        print(result)

