import os
from dotenv import load_dotenv
from apify_client import ApifyClient

load_dotenv()


# Apify API configuration
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN", "your-apify-token-here")
APIFY_ACTOR_ID = "compass/crawler-google-places"


def extract_restaurants_via_apify(latitude, longitude):
    """Main function to extract restaurant data using Apify API"""
    try:
        # Initialize the ApifyClient with your Apify API token
        client = ApifyClient(APIFY_API_TOKEN)

        # Create custom geolocation object with coordinates and radius
        custom_geolocation = {
            "type": "Point",
            "coordinates": [
                longitude,
                latitude,
            ],  # Note: longitude first, then latitude
            "radiusKm": 1,
        }

        print(
            f"Starting Apify actor for location: {latitude},{longitude} with {custom_geolocation['radiusKm']}km radius"
        )

        # Prepare the Actor input
        run_input = {
            "searchStringsArray": ["restaurants"],
            "customGeolocation": custom_geolocation,
            "maxCrawledPlacesPerSearch": 5,
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
            "maxImages": 50,  # 50 for now, 100 when its all working
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
        # Handle location data with proper null checks
        location = restaurant.get("location", {})
        latitude = location.get("lat") if location else None
        longitude = location.get("lng") if location else None

        # Handle image URLs - ensure they're properly formatted as array
        image_urls = restaurant.get("imageUrls", [])
        if not isinstance(image_urls, list):
            image_urls = []

        # Handle images JSONB field - structure the data properly for database
        images_data = restaurant.get("images", [])
        images_json = None

        if images_data:
            if isinstance(images_data, list):
                # If images is an array of image objects, structure it properly for JSONB
                images_json = {
                    "items": images_data,
                    "count": len(images_data),
                    "source": "apify",
                }
            elif isinstance(images_data, dict):
                # If it's already a structured object, use it as is
                images_json = images_data
            else:
                # Invalid format, create empty structure
                images_json = None

        # Handle opening hours - ensure it's properly structured as array
        opening_hours = restaurant.get("openingHours", [])
        if not isinstance(opening_hours, list):
            opening_hours = []

        # Handle ratings and counts with proper type conversion
        rating = restaurant.get("totalScore")
        if rating is not None:
            try:
                rating = float(rating)
                # Ensure rating is within valid range (0-5)
                if rating < 0 or rating > 5:
                    rating = None
            except (ValueError, TypeError):
                rating = None

        reviews_count = restaurant.get("reviewsCount", 0)
        try:
            reviews_count = int(reviews_count) if reviews_count is not None else 0
            # Ensure reviews count is non-negative
            if reviews_count < 0:
                reviews_count = 0
        except (ValueError, TypeError):
            reviews_count = 0

        formatted_restaurant = {
            "name": restaurant.get("title", "Unknown"),
            "address": restaurant.get("address", "Address not available"),
            "rating": rating,
            "reviewsCount": reviews_count,
            "category": restaurant.get("categoryName", "Restaurant"),
            "phone": restaurant.get("phone", ""),
            "website": restaurant.get("website", ""),
            "priceLevel": restaurant.get("priceLevel", ""),
            "openingHours": opening_hours,
            "location": {
                "lat": latitude,
                "lng": longitude,
            },
            "placeId": restaurant.get("placeId", ""),
            "url": restaurant.get("url", ""),
            "menuItems": restaurant.get("menuItems", []),
            # Properly structured image data for database schema
            "images": images_json,  # JSONB field - structured object or null
            "imageUrls": image_urls,  # TEXT[] field - array of direct URLs
            # Additional metadata for tracking
            "source": "apify",
            "extracted_at": restaurant.get("scrapedAt", ""),
        }
        formatted_restaurants.append(formatted_restaurant)
    return formatted_restaurants
