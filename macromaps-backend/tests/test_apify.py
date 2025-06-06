import sys
import os
import json
from pathlib import Path

from utils import extract_restaurants_via_apify


def test_apify_api_and_save_response():
    """Test the Apify API and save the response to example.json"""

    # Print the API key being used
    api_key = os.getenv("APIFY_API_TOKEN", "your-apify-token-here")
    print(f"Using Apify API key: {api_key}")

    # Test coordinates (SM Megamall, Mandaluyong City)
    test_latitude = 14.5851
    test_longitude = 121.0560

    print(f"Testing Apify API with coordinates: {test_latitude}, {test_longitude}")
    print("This may take up to 2 minutes to complete...")

    try:
        # Call the main Apify function
        restaurants, error = extract_restaurants_via_apify(
            test_latitude, test_longitude
        )

        # Prepare the response data
        response_data = {
            "test_coordinates": {
                "latitude": test_latitude,
                "longitude": test_longitude,
                "location_description": "Times Square, New York City",
            },
            "success": error is None,
            "error": error,
            "restaurant_count": len(restaurants) if restaurants else 0,
            "restaurants": restaurants,
        }

        # Save to example.json
        output_file = Path(__file__).parent / "example.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(response_data, f, indent=2, ensure_ascii=False)

        # Print results
        if error:
            print(f"❌ API test failed with error: {error}")
        else:
            print(f"✅ API test successful!")
            print(f"Found {len(restaurants)} restaurants")
            print(f"Response saved to: {output_file}")

            # Print first restaurant as example
            if restaurants:
                print("\nFirst restaurant example:")
                first_restaurant = restaurants[0]
                print(f"  Name: {first_restaurant.get('name', 'N/A')}")
                print(f"  Address: {first_restaurant.get('address', 'N/A')}")
                print(f"  Rating: {first_restaurant.get('rating', 'N/A')}")
                print(f"  Category: {first_restaurant.get('category', 'N/A')}")

        return response_data

    except Exception as e:
        error_data = {
            "test_coordinates": {
                "latitude": test_latitude,
                "longitude": test_longitude,
                "location_description": "Times Square, New York City",
            },
            "success": False,
            "error": f"Exception occurred: {str(e)}",
            "restaurant_count": 0,
            "restaurants": None,
        }

        # Save error response
        output_file = Path(__file__).parent / "example.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(error_data, f, indent=2, ensure_ascii=False)

        print(f"❌ Exception occurred: {e}")
        print(f"Error response saved to: {output_file}")
        return error_data


if __name__ == "__main__":
    test_apify_api_and_save_response()
