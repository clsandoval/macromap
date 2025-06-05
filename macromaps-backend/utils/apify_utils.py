import requests
import time
import os


# Apify API configuration
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN", "your-apify-token-here")
APIFY_ACTOR_ID = "compass/crawler-google-places"
APIFY_API_BASE = "https://api.apify.com/v2"


def start_apify_actor(latitude, longitude):
    """Start the Apify actor for restaurant data extraction"""
    # Create location query from coordinates
    location_query = f"{latitude},{longitude}"

    # Apify actor input configuration
    actor_input = {
        "searchStringsArray": ["restaurants"],
        "locationQuery": location_query,
        "maxCrawledPlacesPerSearch": 10,
        "language": "en",
        "skipClosedPlaces": False,
        "exportPlaceUrls": False,
        "exportReviews": False,
        "exportReviewsTranslated": False,
        "exportCallToActions": False,
        "exportOpeningHours": True,
        "exportPeopleAlsoSearch": False,
        "exportImagesFromPlace": True,
        "exportOtherQuestions": False,
        "additionalInfo": False,
        "reviewsSort": "newest",
        "reviewsTranslation": "originalAndTranslated",
        "personalDataOptions": "personal-data-to-be-excluded",
        "cacheBusting": False,
    }

    print(f"Starting Apify actor for location: {location_query}")

    # Start the Apify actor
    actor_url = f"{APIFY_API_BASE}/acts/{APIFY_ACTOR_ID}/runs"
    headers = {
        "Authorization": f"Bearer {APIFY_API_TOKEN}",
        "Content-Type": "application/json",
    }

    response = requests.post(actor_url, json=actor_input, headers=headers)

    if response.status_code != 201:
        print(f"Failed to start actor: {response.status_code} - {response.text}")
        return None, f"Failed to start data extraction: {response.text}"

    run_info = response.json()["data"]
    run_id = run_info["id"]

    print(f"Actor started with run ID: {run_id}")
    return run_id, None


def check_run_status(run_id):
    """Check the status of an Apify actor run"""
    headers = {
        "Authorization": f"Bearer {APIFY_API_TOKEN}",
        "Content-Type": "application/json",
    }

    status_url = f"{APIFY_API_BASE}/actor-runs/{run_id}"
    status_response = requests.get(status_url, headers=headers)

    if status_response.status_code != 200:
        return None, f"Failed to check run status: {status_response.text}"

    run_data = status_response.json()["data"]
    return run_data, None


def get_apify_results(dataset_id):
    """Get results from the Apify dataset"""
    headers = {
        "Authorization": f"Bearer {APIFY_API_TOKEN}",
        "Content-Type": "application/json",
    }

    results_url = f"{APIFY_API_BASE}/datasets/{dataset_id}/items"
    results_response = requests.get(results_url, headers=headers)

    if results_response.status_code != 200:
        return None, f"Failed to retrieve results: {results_response.text}"

    restaurants = results_response.json()
    return restaurants, None


def format_restaurant_data(restaurants):
    """Format restaurant data from Apify response to standard format"""
    formatted_restaurants = []
    for restaurant in restaurants:
        formatted_restaurant = {
            "name": restaurant.get("title", "Unknown"),
            "address": restaurant.get("address", "Address not available"),
            "rating": restaurant.get("totalScore", 0),
            "reviewsCount": restaurant.get("reviewsCount", 0),
            "category": restaurant.get("categoryName", "Restaurant"),
            "phone": restaurant.get("phone", ""),
            "website": restaurant.get("website", ""),
            "priceLevel": restaurant.get("priceLevel", ""),
            "openingHours": restaurant.get("openingHours", []),
            "location": {
                "lat": restaurant.get("location", {}).get("lat", 0),
                "lng": restaurant.get("location", {}).get("lng", 0),
            },
            "placeId": restaurant.get("placeId", ""),
            "url": restaurant.get("url", ""),
            "menuItems": restaurant.get("menuItems", []),
            # Photo data from Apify
            "images": restaurant.get(
                "images", []
            ),  # Array of image objects with photographer info
            "imageUrls": restaurant.get("imageUrls", []),  # Array of direct image URLs
        }
        formatted_restaurants.append(formatted_restaurant)
    return formatted_restaurants


def wait_for_apify_completion(run_id, max_wait_time=120, check_interval=5):
    """Wait for the Apify actor to complete and return results"""
    waited_time = 0

    while waited_time < max_wait_time:
        # Check run status
        run_data, error = check_run_status(run_id)

        if error:
            return None, error

        status = run_data["status"]
        print(f"Run status: {status}")

        if status == "SUCCEEDED":
            # Get the results
            dataset_id = run_data["defaultDatasetId"]
            restaurants, error = get_apify_results(dataset_id)

            if error:
                return None, error

            # Format the response
            formatted_restaurants = format_restaurant_data(restaurants)
            return formatted_restaurants, None

        elif status == "FAILED":
            error_msg = run_data.get("statusMessage", "Unknown error")
            return None, f"Data extraction failed: {error_msg}"

        elif status in ["READY", "RUNNING"]:
            # Still running, wait a bit more
            time.sleep(check_interval)
            waited_time += check_interval
        else:
            return None, f"Unexpected run status: {status}"

    # Timeout reached
    return None, "Request timeout - data extraction is taking too long"


def extract_restaurants_via_apify(latitude, longitude):
    """Main function to extract restaurant data using Apify API"""
    # Start the Apify actor
    run_id, error = start_apify_actor(latitude, longitude)
    if error:
        return None, error

    # Wait for completion and get results
    restaurants, error = wait_for_apify_completion(run_id)
    if error:
        return None, error

    return restaurants, None
