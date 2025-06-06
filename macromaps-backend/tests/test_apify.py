import sys
import os
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

from utils import extract_restaurants_via_apify
from utils.supabase_utils import supabase


def map_restaurant_to_schema(
    restaurant: Dict[str, Any], apify_run_id: str = None
) -> Dict[str, Any]:
    """
    Map restaurant data from Apify format to Supabase schema

    Args:
        restaurant: Restaurant data from Apify
        apify_run_id: Optional run ID for tracking

    Returns:
        Dictionary formatted for Supabase insertion
    """
    # Extract location data
    location = restaurant.get("location", {})
    latitude = location.get("lat") if location else restaurant.get("latitude")
    longitude = location.get("lng") if location else restaurant.get("longitude")

    # Convert imageUrls to array format
    image_urls = restaurant.get("imageUrls", [])
    if isinstance(image_urls, list):
        image_urls_array = image_urls
    else:
        image_urls_array = []

    # Prepare opening hours as JSONB
    opening_hours = restaurant.get("openingHours", [])
    if isinstance(opening_hours, list):
        opening_hours_json = opening_hours
    else:
        opening_hours_json = []

    # Map to database schema
    mapped_data = {
        "place_id": restaurant.get("placeId", ""),
        "name": restaurant.get("name", ""),
        "address": restaurant.get("address", ""),
        "phone": restaurant.get("phone", ""),
        "website": restaurant.get("website", ""),
        "latitude": float(latitude) if latitude else None,
        "longitude": float(longitude) if longitude else None,
        "rating": float(restaurant.get("rating")) if restaurant.get("rating") else None,
        "reviews_count": int(restaurant.get("reviewsCount", 0)),
        "category": restaurant.get("category", ""),
        "price_level": restaurant.get("priceLevel", ""),
        "opening_hours": opening_hours_json,
        "image_urls": image_urls_array,
        "images": restaurant.get("images", {}),
        "status": "pending",  # Default status for new restaurants
        "google_maps_url": restaurant.get("url", ""),
        "apify_run_id": apify_run_id,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }

    # Remove None values to let database handle defaults
    return {k: v for k, v in mapped_data.items() if v is not None and v != ""}


def upload_restaurants_to_supabase(
    restaurants: List[Dict[str, Any]], apify_run_id: str = None
) -> Dict[str, Any]:
    """
    Upload restaurants to Supabase database

    Args:
        restaurants: List of restaurant data from Apify
        apify_run_id: Optional run ID for tracking

    Returns:
        Dictionary with upload results
    """
    if not restaurants:
        return {
            "success": False,
            "message": "No restaurants to upload",
            "uploaded_count": 0,
            "errors": [],
        }

    print(f"🗄️ Uploading {len(restaurants)} restaurants to Supabase...")

    uploaded_count = 0
    errors = []

    for i, restaurant in enumerate(restaurants, 1):
        try:
            # Map restaurant data to schema
            mapped_restaurant = map_restaurant_to_schema(restaurant, apify_run_id)

            if not mapped_restaurant.get("place_id"):
                errors.append(f"Restaurant {i}: Missing place_id")
                continue

            if not mapped_restaurant.get("name"):
                errors.append(f"Restaurant {i}: Missing name")
                continue

            # Insert into Supabase (upsert to handle duplicates)
            response = (
                supabase.table("restaurants")
                .upsert(mapped_restaurant, on_conflict="place_id")
                .execute()
            )

            if response.data:
                uploaded_count += 1
                print(f"   ✅ {i}/{len(restaurants)}: {mapped_restaurant['name']}")
            else:
                errors.append(f"Restaurant {i}: No data returned from insert")

        except Exception as e:
            error_msg = (
                f"Restaurant {i} ({restaurant.get('name', 'Unknown')}): {str(e)}"
            )
            errors.append(error_msg)
            print(f"   ❌ {error_msg}")

    success = uploaded_count > 0

    print(f"📊 Upload Summary:")
    print(f"   Total restaurants: {len(restaurants)}")
    print(f"   Successfully uploaded: {uploaded_count}")
    print(f"   Errors: {len(errors)}")

    return {
        "success": success,
        "message": f"Uploaded {uploaded_count}/{len(restaurants)} restaurants",
        "uploaded_count": uploaded_count,
        "total_restaurants": len(restaurants),
        "errors": errors,
    }


def test_apify_api_and_upload_to_supabase():
    """Test the Apify API and upload results to Supabase database"""

    # Print the API key being used
    api_key = os.getenv("APIFY_API_TOKEN", "your-apify-token-here")
    print(
        f"Using Apify API key: {api_key[:10]}...{api_key[-4:] if len(api_key) > 14 else api_key}"
    )

    # Test coordinates (SM Megamall, Mandaluyong City)
    test_latitude = 14.5851
    test_longitude = 121.0560

    print(f"🌍 Testing Apify API with coordinates: {test_latitude}, {test_longitude}")
    print("This may take up to 2 minutes to complete...")

    try:
        # Call the main Apify function
        restaurants, error = extract_restaurants_via_apify(
            test_latitude, test_longitude
        )

        # Generate a unique run ID for tracking
        apify_run_id = f"test_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        # Prepare the response data
        response_data = {
            "test_info": {
                "run_id": apify_run_id,
                "timestamp": datetime.utcnow().isoformat(),
                "coordinates": {
                    "latitude": test_latitude,
                    "longitude": test_longitude,
                    "location_description": "SM Megamall, Mandaluyong City, Philippines",
                },
            },
            "apify_results": {
                "success": error is None,
                "error": error,
                "restaurant_count": len(restaurants) if restaurants else 0,
            },
            "restaurants": restaurants,
        }

        # Upload to Supabase if restaurants were found
        upload_results = None
        if restaurants and not error:
            upload_results = upload_restaurants_to_supabase(restaurants, apify_run_id)
            response_data["supabase_upload"] = upload_results
        else:
            print("⚠️ Skipping Supabase upload - no restaurants or API error")
            response_data["supabase_upload"] = {
                "success": False,
                "message": "Skipped due to API error or no restaurants",
                "uploaded_count": 0,
            }

        # Save to example.json for reference
        output_file = Path(__file__).parent / "example.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(response_data, f, indent=2, ensure_ascii=False)

        # Print results
        print(f"\n📋 Test Results:")
        if error:
            print(f"❌ Apify API failed: {error}")
        else:
            print(f"✅ Apify API successful!")
            print(f"📊 Found {len(restaurants)} restaurants")

            if upload_results:
                if upload_results["success"]:
                    print(f"✅ Supabase upload successful!")
                    print(f"📊 Uploaded {upload_results['uploaded_count']} restaurants")
                else:
                    print(f"❌ Supabase upload failed")
                    if upload_results.get("errors"):
                        print(f"   Errors: {len(upload_results['errors'])}")

            # Print first restaurant as example
            if restaurants:
                print("\n🏪 First restaurant example:")
                first_restaurant = restaurants[0]
                print(f"   Name: {first_restaurant.get('name', 'N/A')}")
                print(f"   Address: {first_restaurant.get('address', 'N/A')}")
                print(f"   Rating: {first_restaurant.get('rating', 'N/A')}")
                print(f"   Category: {first_restaurant.get('category', 'N/A')}")
                print(f"   Place ID: {first_restaurant.get('placeId', 'N/A')}")
                print(f"   Images: {len(first_restaurant.get('imageUrls', []))} URLs")

        print(f"💾 Response saved to: {output_file}")
        return response_data

    except Exception as e:
        error_data = {
            "test_info": {
                "run_id": f"error_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                "timestamp": datetime.utcnow().isoformat(),
                "coordinates": {
                    "latitude": test_latitude,
                    "longitude": test_longitude,
                    "location_description": "SM Megamall, Mandaluyong City, Philippines",
                },
            },
            "apify_results": {
                "success": False,
                "error": f"Exception occurred: {str(e)}",
                "restaurant_count": 0,
            },
            "restaurants": None,
            "supabase_upload": {
                "success": False,
                "message": "Skipped due to API exception",
                "uploaded_count": 0,
            },
        }

        # Save error response
        output_file = Path(__file__).parent / "example.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(error_data, f, indent=2, ensure_ascii=False)

        print(f"❌ Exception occurred: {e}")
        print(f"💾 Error response saved to: {output_file}")
        return error_data


if __name__ == "__main__":
    test_apify_api_and_upload_to_supabase()
