#!/usr/bin/env python3
"""
Test Menu Processing Pipeline
Tests the complete menu processing workflow against 10 random images from example.json
"""

import json
import random
import time
import sys
import os
import uuid
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
from pathlib import Path

from tasks import MenuProcessor, run_menu_processing_pipeline
from utils import classify_menu_image, analyze_menu_image
from utils.supabase_utils import supabase

# Model pricing per 1K tokens (approximate costs)
MODEL_PRICING = {
    "gpt-4.1": 0.003,
    "gpt-4.1-mini": 0.0008,
    "gpt-4.1-nano": 0.0002,
    "gpt-4o": 0.003,  # Default fallback
}


def calculate_cost(tokens_used: int, model: str = "gpt-4.1") -> float:
    """Calculate cost based on token usage and model pricing"""
    if not tokens_used:
        return 0.0

    cost_per_1k = MODEL_PRICING.get(model, MODEL_PRICING["gpt-4o"])
    return (tokens_used * cost_per_1k) / 1000


def load_example_data():
    """Load the example.json file and extract image URLs"""
    try:
        with open("tests/example.json", "r") as f:
            data = json.load(f)

        all_image_urls = []

        # Extract image URLs from all restaurants
        for restaurant in data.get("restaurants", []):
            place_id = restaurant.get("placeId", "")
            restaurant_name = restaurant.get("name", "Unknown")
            image_urls = restaurant.get("imageUrls", [])

            # Add restaurant context to each image URL
            for url in image_urls:
                all_image_urls.append(
                    {
                        "url": url,
                        "place_id": place_id,
                        "restaurant_name": restaurant_name,
                    }
                )

        print(
            f"Loaded {len(all_image_urls)} total images from {len(data.get('restaurants', []))} restaurants"
        )
        return all_image_urls

    except FileNotFoundError:
        print("Error: example.json not found in tests/ directory")
        return []
    except json.JSONDecodeError:
        print("Error: Invalid JSON in example.json")
        return []


def select_random_images(all_images, count=10):
    """Select random images for testing, prioritizing URLs likely to contain menus"""
    if len(all_images) < count:
        print(f"Warning: Only {len(all_images)} images available, using all of them")
        return all_images

    # Sort images by menu likelihood first (prioritize /p/ URLs)
    sorted_images = sort_images_by_menu_likelihood(all_images)

    # Count how many of each type we have
    p_images = [img for img in sorted_images if "/p/" in img.get("url", "")]
    gps_images = [img for img in sorted_images if "/gps-cs-s/" in img.get("url", "")]
    other_images = [
        img
        for img in sorted_images
        if "/p/" not in img.get("url", "") and "/gps-cs-s/" not in img.get("url", "")
    ]

    print(
        f"📊 Image distribution: {len(p_images)} /p/ URLs, {len(gps_images)} /gps-cs-s/ URLs, {len(other_images)} other URLs"
    )

    # Select from the sorted list to bias towards menu-likely images
    # Take more from high-priority groups
    selected_images = []

    # First, try to get images from /p/ URLs (most likely to have menus)
    p_count = min(count // 2, len(p_images))  # Up to half from /p/ URLs
    if p_count > 0:
        selected_images.extend(random.sample(p_images, p_count))
        print(f"   Selected {p_count} /p/ URLs (high menu probability)")

    # Then get some from /gps-cs-s/ URLs
    remaining_count = count - len(selected_images)
    gps_count = min(remaining_count // 2, len(gps_images))
    if gps_count > 0:
        selected_images.extend(random.sample(gps_images, gps_count))
        print(f"   Selected {gps_count} /gps-cs-s/ URLs (medium menu probability)")

    # Fill the rest with any remaining images
    remaining_count = count - len(selected_images)
    if remaining_count > 0:
        remaining_images = [img for img in sorted_images if img not in selected_images]
        if remaining_images:
            final_count = min(remaining_count, len(remaining_images))
            selected_images.extend(random.sample(remaining_images, final_count))
            print(f"   Selected {final_count} additional URLs")

    return selected_images


def sort_images_by_menu_likelihood(image_data_list):
    """
    Sort image data by likelihood of containing a menu.
    URLs with /p/ are prioritized as they're more likely to have menus.

    Args:
        image_data_list: List of image data dictionaries with 'url' key

    Returns:
        Sorted list of image data
    """

    def get_priority(image_data):
        """Return priority score (lower = higher priority)"""
        url = image_data.get("url", "")
        if "/p/" in url:
            return 0  # Highest priority - most likely to have menus
        elif "/gps-cs-s/" in url:
            return 1  # Lower priority
        else:
            return 2  # Lowest priority - other URL types

    return sorted(image_data_list, key=get_priority)


def test_image_classification(image_urls):
    """Test the menu classification functionality"""
    print("\n" + "=" * 60)
    print("TESTING IMAGE CLASSIFICATION")
    print("=" * 60)

    classification_results = []
    total_classification_cost = 0.0
    total_classification_tokens = 0

    for i, image_data in enumerate(image_urls, 1):
        url = image_data["url"]
        restaurant_name = image_data["restaurant_name"]

        print(f"\n[{i}/10] Classifying image from {restaurant_name}")
        print(f"URL: {url[:80]}..." if len(url) > 80 else f"URL: {url}")

        try:
            start_time = time.time()
            result = classify_menu_image(url)
            processing_time = time.time() - start_time

            # Calculate cost
            tokens_used = result.get("tokens_used", 0)
            cost = calculate_cost(tokens_used) if tokens_used else 0.0
            total_classification_cost += cost
            total_classification_tokens += tokens_used or 0

            # Add context
            result["restaurant_name"] = restaurant_name
            result["place_id"] = image_data["place_id"]
            result["url"] = url
            result["processing_time"] = processing_time
            result["cost"] = cost

            classification_results.append(result)

            # Display results
            is_menu = result.get("is_menu", False)
            confidence = result.get("confidence_level", "unknown")
            image_type = result.get("image_type", "unknown")
            reasoning = result.get("reasoning", "No reasoning provided")

            print(f"   ✅ Result: {'MENU' if is_menu else 'NOT MENU'}")
            print(f"   📊 Confidence: {confidence}")
            print(f"   🏷️  Type: {image_type}")
            print(f"   ⏱️  Time: {processing_time:.2f}s")
            print(f"   🪄 Tokens: {tokens_used}")
            print(f"   💰 Cost: ${cost:.4f}")
            print(f"   💭 Reasoning: {reasoning[:100]}...")

            if result.get("error"):
                print(f"   ❌ Error: {result['error']}")

        except Exception as e:
            print(f"   ❌ FAILED: {str(e)}")
            classification_results.append(
                {
                    "restaurant_name": restaurant_name,
                    "place_id": image_data["place_id"],
                    "url": url,
                    "error": str(e),
                    "is_menu": False,
                    "processing_time": 0,
                    "cost": 0.0,
                    "tokens_used": 0,
                }
            )

    print(f"\n💰 Classification Summary:")
    print(f"   Total tokens used: {total_classification_tokens:,}")
    print(f"   Total cost: ${total_classification_cost:.4f}")

    return classification_results


def test_menu_analysis(classification_results):
    """Test menu analysis on images classified as menus"""
    print("\n" + "=" * 60)
    print("TESTING MENU ANALYSIS")
    print("=" * 60)

    # Filter for menu images
    menu_images = [
        result for result in classification_results if result.get("is_menu", False)
    ]

    if not menu_images:
        print("❌ No images were classified as menus. Cannot test menu analysis.")
        return []

    print(f"🍽️  Found {len(menu_images)} menu images to analyze")

    analysis_results = []
    total_analysis_cost = 0.0
    total_analysis_tokens = 0

    for i, menu_image in enumerate(menu_images, 1):
        url = menu_image["url"]
        restaurant_name = menu_image["restaurant_name"]

        print(f"\n[{i}/{len(menu_images)}] Analyzing menu from {restaurant_name}")

        try:
            start_time = time.time()
            result = analyze_menu_image(url)
            processing_time = time.time() - start_time

            # Calculate cost
            tokens_used = result.get("tokens_used", 0)
            cost = calculate_cost(tokens_used) if tokens_used else 0.0
            total_analysis_cost += cost
            total_analysis_tokens += tokens_used or 0

            # Add context
            result["restaurant_name"] = restaurant_name
            result["place_id"] = menu_image["place_id"]
            result["url"] = url
            result["processing_time"] = processing_time
            result["cost"] = cost

            analysis_results.append(result)

            # Display results
            menu_items = result.get("menu_items", [])
            total_items = result.get("total_items", 0)
            has_prices = result.get("has_prices", False)
            has_descriptions = result.get("has_descriptions", False)

            print(f"   ✅ Extracted {total_items} menu items")
            print(f"   💰 Has prices: {'Yes' if has_prices else 'No'}")
            print(f"   📝 Has descriptions: {'Yes' if has_descriptions else 'No'}")
            print(f"   ⏱️  Time: {processing_time:.2f}s")
            print(f"   🪄 Tokens: {tokens_used}")
            print(f"   💰 Cost: ${cost:.4f}")

            # Show ALL menu items with full details
            if menu_items:
                print(f"   📋 ALL MENU ITEMS ({len(menu_items)} items):")
                for idx, item in enumerate(menu_items, 1):
                    name = item.get("name", "No name")
                    price = item.get("price", "No price")
                    category = item.get("category", "No category")
                    description = item.get("description", "")
                    calories = item.get("calories", "")
                    protein = item.get("protein", "")
                    carbs = item.get("carbs", "")
                    fat = item.get("fat", "")

                    print(f"      {idx:2d}. {name}")
                    print(f"          💰 Price: {price}")
                    print(f"          🏷️  Category: {category}")
                    if description:
                        print(f"          📝 Description: {description}")
                    if calories:
                        print(f"          🔥 Calories: {calories}")
                    if protein or carbs or fat:
                        macros = []
                        if protein:
                            macros.append(f"Protein: {protein}")
                        if carbs:
                            macros.append(f"Carbs: {carbs}")
                        if fat:
                            macros.append(f"Fat: {fat}")
                        print(f"          🥗 Macros: {', '.join(macros)}")
                    print()  # Empty line between items

            if result.get("error"):
                print(f"   ❌ Error: {result['error']}")

        except Exception as e:
            print(f"   ❌ FAILED: {str(e)}")
            analysis_results.append(
                {
                    "restaurant_name": restaurant_name,
                    "place_id": menu_image["place_id"],
                    "url": url,
                    "error": str(e),
                    "menu_items": [],
                    "total_items": 0,
                    "processing_time": 0,
                    "cost": 0.0,
                    "tokens_used": 0,
                }
            )

    print(f"\n💰 Analysis Summary:")
    print(f"   Total tokens used: {total_analysis_tokens:,}")
    print(f"   Total cost: ${total_analysis_cost:.4f}")

    return analysis_results


def test_end_to_end_processing():
    """Test the complete end-to-end processing pipeline with real restaurant data"""
    print("\n" + "=" * 60)
    print("TESTING END-TO-END PROCESSING WITH REAL DATA")
    print("=" * 60)

    # Specific restaurant place ID to test
    test_place_id = "ChIJXZ2X9RTIlzMRtrFuMxGE6n8"
    print(f"🏪 Testing with restaurant place ID: {test_place_id}")

    try:
        # First, check if the restaurant exists in our database
        restaurant_response = (
            supabase.table("restaurants")
            .select("id, name, place_id, image_urls, images, status")
            .eq("place_id", test_place_id)
            .execute()
        )

        if not restaurant_response.data:
            print(f"❌ Restaurant with place_id {test_place_id} not found in database")
            print(
                "   Please ensure the restaurant data has been uploaded to Supabase first"
            )
            return None

        restaurant_data = restaurant_response.data[0]
        restaurant_name = restaurant_data.get("name", "Unknown")
        restaurant_id = restaurant_data["id"]
        current_status = restaurant_data.get("status", "unknown")

        print(f"✅ Found restaurant: {restaurant_name}")
        print(f"🆔 Restaurant ID: {restaurant_id}")
        print(f"📊 Current status: {current_status}")

        # Check available images
        image_urls = restaurant_data.get("image_urls", [])
        images_json = restaurant_data.get("images")

        total_images = len(image_urls)
        if images_json and isinstance(images_json, dict) and "items" in images_json:
            total_images += len(images_json["items"])
        elif images_json and isinstance(images_json, list):
            total_images += len(images_json)

        print(f"📸 Total images available: {total_images}")

        if total_images == 0:
            print("❌ No images found for this restaurant")
            return None

        if total_images < 20:
            print(f"⚠️  Only {total_images} images available (requested 20)")
            print("   Will process all available images")

        # Initialize MenuProcessor with production settings
        processor = MenuProcessor(
            max_workers=5, classification_workers=3, analysis_workers=2
        )

        print(f"\n🔧 Processor Configuration:")
        print(f"   • Max workers: {processor.max_workers}")
        print(f"   • Classification workers: {processor.classification_workers}")
        print(f"   • Analysis workers: {processor.analysis_workers}")

        # Reset restaurant status to pending for fresh test
        print(f"\n🔄 Resetting restaurant status to 'pending' for test...")
        supabase.table("restaurants").update({"status": "pending"}).eq(
            "place_id", test_place_id
        ).execute()

        # Clear any existing menu items for this restaurant
        print("🧹 Clearing existing menu items...")
        supabase.table("menu_items").delete().eq(
            "restaurant_id", restaurant_id
        ).execute()

        # Clear existing processing logs for this restaurant
        print("🧹 Clearing existing processing logs...")
        supabase.table("image_processing_log").delete().eq(
            "restaurant_id", restaurant_id
        ).execute()
        supabase.table("processing_queue").delete().eq(
            "restaurant_id", restaurant_id
        ).execute()

        print(f"\n🚀 Starting end-to-end processing...")
        start_time = time.time()

        # Process the restaurant using the actual MenuProcessor
        result = processor.process_restaurant_images(test_place_id)

        processing_time = time.time() - start_time

        print(f"\n📋 PROCESSING RESULTS:")
        print(f"   • Processing time: {processing_time:.2f} seconds")
        print(f"   • Total images processed: {result.total_images}")
        print(f"   • Menu images found: {result.menu_images_found}")
        print(f"   • Menu items extracted: {result.total_menu_items}")

        if result.error:
            print(f"   • Error: {result.error}")
        else:
            print(f"   • Status: ✅ SUCCESS")

        # Verify the results in the database
        print(f"\n🔍 VERIFYING DATABASE RESULTS:")

        # Check restaurant status
        final_restaurant = (
            supabase.table("restaurants")
            .select("status")
            .eq("place_id", test_place_id)
            .execute()
        )
        final_status = (
            final_restaurant.data[0]["status"] if final_restaurant.data else "unknown"
        )
        print(f"   • Final restaurant status: {final_status}")

        # Check menu items
        menu_items_response = (
            supabase.table("menu_items")
            .select("*")
            .eq("restaurant_id", restaurant_id)
            .execute()
        )
        menu_items_count = (
            len(menu_items_response.data) if menu_items_response.data else 0
        )
        print(f"   • Menu items in database: {menu_items_count}")

        # Check image processing logs
        logs_response = (
            supabase.table("image_processing_log")
            .select("*")
            .eq("restaurant_id", restaurant_id)
            .execute()
        )
        logs_count = len(logs_response.data) if logs_response.data else 0
        menu_logs_count = (
            len([log for log in logs_response.data if log.get("is_menu_image")])
            if logs_response.data
            else 0
        )
        print(
            f"   • Image processing logs: {logs_count} total, {menu_logs_count} menu images"
        )

        # Check processing queue
        queue_response = (
            supabase.table("processing_queue")
            .select("*")
            .eq("restaurant_id", restaurant_id)
            .execute()
        )
        queue_status = (
            queue_response.data[0]["status"] if queue_response.data else "not found"
        )
        print(f"   • Processing queue status: {queue_status}")

        # Show sample menu items if any were extracted
        if menu_items_response.data:
            print(f"\n🍽️  SAMPLE MENU ITEMS:")
            for i, item in enumerate(menu_items_response.data[:5], 1):
                name = item.get("name", "No name")
                price = item.get("price", "No price")
                category = item.get("category", "No category")
                calories = item.get("calories", "")

                print(f"   {i}. {name}")
                print(f"      💰 Price: {price}")
                print(f"      🏷️  Category: {category}")
                if calories:
                    print(f"      🔥 Calories: {calories}")
                print()

        # Performance metrics
        if result.total_images > 0:
            avg_time_per_image = processing_time / result.total_images
            print(f"\n⚡ PERFORMANCE METRICS:")
            print(f"   • Average time per image: {avg_time_per_image:.2f}s")
            print(
                f"   • Menu detection rate: {(result.menu_images_found/result.total_images)*100:.1f}%"
            )
            if result.menu_images_found > 0:
                print(
                    f"   • Items per menu image: {result.total_menu_items/result.menu_images_found:.1f}"
                )

        return {
            "place_id": test_place_id,
            "restaurant_name": restaurant_name,
            "processing_time": processing_time,
            "result": result,
            "final_status": final_status,
            "menu_items_count": menu_items_count,
            "logs_count": logs_count,
            "menu_logs_count": menu_logs_count,
        }

    except Exception as e:
        print(f"❌ Exception occurred during end-to-end test: {str(e)}")
        import traceback

        traceback.print_exc()
        return None


def print_summary(classification_results, analysis_results):
    """Print a summary of test results"""
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    # Classification summary
    total_classified = len(classification_results)
    menu_images = len([r for r in classification_results if r.get("is_menu", False)])
    classification_errors = len([r for r in classification_results if r.get("error")])
    avg_classification_time = sum(
        r.get("processing_time", 0) for r in classification_results
    ) / max(total_classified, 1)
    total_classification_cost = sum(r.get("cost", 0) for r in classification_results)
    total_classification_tokens = sum(
        r.get("tokens_used", 0) for r in classification_results
    )

    print(f"📊 CLASSIFICATION RESULTS:")
    print(f"   • Total images tested: {total_classified}")
    print(f"   • Images classified as menus: {menu_images}")
    print(f"   • Classification errors: {classification_errors}")
    print(f"   • Average processing time: {avg_classification_time:.2f}s")
    print(f"   • Menu detection rate: {menu_images/max(total_classified, 1)*100:.1f}%")
    print(f"   • Total tokens used: {total_classification_tokens:,}")
    print(f"   • Total cost: ${total_classification_cost:.4f}")

    # Analysis summary
    if analysis_results:
        total_analyzed = len(analysis_results)
        total_menu_items = sum(r.get("total_items", 0) for r in analysis_results)
        analysis_errors = len([r for r in analysis_results if r.get("error")])
        avg_analysis_time = sum(
            r.get("processing_time", 0) for r in analysis_results
        ) / max(total_analyzed, 1)
        avg_items_per_menu = total_menu_items / max(total_analyzed, 1)
        total_analysis_cost = sum(r.get("cost", 0) for r in analysis_results)
        total_analysis_tokens = sum(r.get("tokens_used", 0) for r in analysis_results)

        print(f"\n🍽️  MENU ANALYSIS RESULTS:")
        print(f"   • Menus analyzed: {total_analyzed}")
        print(f"   • Total menu items extracted: {total_menu_items}")
        print(f"   • Analysis errors: {analysis_errors}")
        print(f"   • Average items per menu: {avg_items_per_menu:.1f}")
        print(f"   • Average processing time: {avg_analysis_time:.2f}s")
        print(f"   • Total tokens used: {total_analysis_tokens:,}")
        print(f"   • Total cost: ${total_analysis_cost:.4f}")

    # Overall performance and costs
    total_time = sum(r.get("processing_time", 0) for r in classification_results)
    total_cost = total_classification_cost
    total_tokens = total_classification_tokens

    if analysis_results:
        total_time += sum(r.get("processing_time", 0) for r in analysis_results)
        total_cost += sum(r.get("cost", 0) for r in analysis_results)
        total_tokens += sum(r.get("tokens_used", 0) for r in analysis_results)

    success_count = (
        total_classified
        + len(analysis_results)
        - classification_errors
        - len([r for r in analysis_results if r.get("error")])
        if analysis_results
        else total_classified - classification_errors
    )
    total_operations = (
        total_classified + len(analysis_results)
        if analysis_results
        else total_classified
    )

    print(f"\n⏱️  PERFORMANCE & COSTS:")
    print(f"   • Total processing time: {total_time:.2f}s")
    print(f"   • Total tokens used: {total_tokens:,}")
    print(f"   • Total cost: ${total_cost:.4f}")
    print(
        f"   • Average cost per operation: ${total_cost/max(total_operations, 1):.4f}"
    )
    print(f"   • Success rate: {(success_count/max(total_operations, 1)*100):.1f}%")

    # Cost breakdown by model (assuming gpt-4.1 for now)
    print(f"\n💰 COST BREAKDOWN:")
    print(
        f"   • Classification cost: ${total_classification_cost:.4f} ({total_classification_tokens:,} tokens)"
    )
    if analysis_results:
        print(
            f"   • Analysis cost: ${sum(r.get('cost', 0) for r in analysis_results):.4f} ({sum(r.get('tokens_used', 0) for r in analysis_results):,} tokens)"
        )
    print(f"   • Model used: gpt-4.1 (${MODEL_PRICING['gpt-4.1']:.3f} per 1K tokens)")

    # Detailed results
    print(f"\n📋 DETAILED RESULTS:")
    for i, result in enumerate(classification_results, 1):
        is_menu = result.get("is_menu", False)
        confidence = result.get("confidence_level", "unknown")
        restaurant = result.get("restaurant_name", "Unknown")
        cost = result.get("cost", 0)
        tokens = result.get("tokens_used", 0)
        print(
            f"   {i:2d}. {restaurant[:25]:25} | {'MENU' if is_menu else 'NOT MENU':8} | {confidence:6} | ${cost:.4f} ({tokens} tokens)"
        )


def main():
    """Main test function"""
    print("🧪 MENU PROCESSING PIPELINE TEST")
    print("=" * 60)
    print("Testing real end-to-end menu processing with Supabase integration")

    # Test the real end-to-end processing first
    end_to_end_result = test_end_to_end_processing()

    if end_to_end_result:
        print(f"\n✅ END-TO-END TEST COMPLETED SUCCESSFULLY!")
        print(f"Restaurant: {end_to_end_result['restaurant_name']}")
        print(f"Processing time: {end_to_end_result['processing_time']:.2f}s")
        print(f"Menu items extracted: {end_to_end_result['menu_items_count']}")

        # Offer to run additional example.json tests
        print(f"\n" + "=" * 60)
        print("OPTIONAL: Additional tests with example.json images")
        print("=" * 60)

        try:
            # Try to load example data for additional testing
            all_images = load_example_data()
            if all_images:
                print(f"📋 Found {len(all_images)} images in example.json")
                print("Running additional classification and analysis tests...")

                # Select random images for additional testing
                test_images = select_random_images(all_images, 10)
                print(
                    f"🎯 Selected {len(test_images)} random images for additional testing"
                )

                # Test image classification
                classification_results = test_image_classification(test_images)

                # Test menu analysis on classified menu images
                analysis_results = test_menu_analysis(classification_results)

                # Print summary of additional tests
                print_summary(classification_results, analysis_results)
            else:
                print("⚠️  No example.json data found, skipping additional tests")

        except Exception as e:
            print(f"⚠️  Could not run additional example.json tests: {str(e)}")
            print("   This is not critical - the main end-to-end test was successful")

    else:
        print(f"\n❌ END-TO-END TEST FAILED")
        print("Falling back to example.json testing...")

        # Fallback to example.json tests if end-to-end fails
        all_images = load_example_data()
        if not all_images:
            print("❌ No test data available. Exiting.")
            return

        # Select random images for testing
        test_images = select_random_images(all_images, 10)
        print(f"\n🎯 Selected {len(test_images)} random images for testing")

        # Test image classification
        classification_results = test_image_classification(test_images)

        # Test menu analysis on classified menu images
        analysis_results = test_menu_analysis(classification_results)

        # Print summary
        print_summary(classification_results, analysis_results)

    print(f"\n✅ Testing complete!")
    print(f"💡 The end-to-end test uses real Supabase data and MenuProcessor pipeline.")
    print(f"💡 Ensure restaurant data is uploaded to Supabase for full functionality.")


if __name__ == "__main__":
    main()
