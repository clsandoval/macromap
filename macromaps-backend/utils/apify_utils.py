import os
from apify_client import ApifyClient


# Apify API configuration
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN", "your-apify-token-here")
APIFY_ACTOR_ID = "compass/crawler-google-places"


def extract_restaurants_via_apify(latitude, longitude):
    """Main function to extract restaurant data using Apify API"""
    try:
        # Initialize the ApifyClient with your Apify API token
        client = ApifyClient(APIFY_API_TOKEN)

        # Create location query from coordinates
        location_query = f"{latitude},{longitude}"

        print(f"Starting Apify actor for location: {location_query}")

        # Prepare the Actor input
        run_input = {
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
            "maxImages": 5,  # Limit images to avoid too much data
        }

        # Run the Actor and wait for it to finish
        print("Running Apify actor... This may take a few minutes.")
        run = client.actor(APIFY_ACTOR_ID).call(run_input=run_input)

        # Check if the run was successful
        if not run.get("defaultDatasetId"):
            return None, "Failed to get dataset ID from Apify run"

        print(f"✅ Actor completed. Dataset ID: {run['defaultDatasetId']}")

        # Fetch results from the dataset
        restaurants = []
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            restaurants.append(item)

        if not restaurants:
            return [], None  # Return empty list if no restaurants found

        # Format the response
        formatted_restaurants = format_restaurant_data(restaurants)
        return formatted_restaurants, None

    except Exception as e:
        error_msg = f"Apify API error: {str(e)}"
        print(f"❌ {error_msg}")
        return None, error_msg


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
