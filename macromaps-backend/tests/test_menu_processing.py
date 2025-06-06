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
from dotenv import load_dotenv

load_dotenv()
from pathlib import Path

from tasks import MenuProcessor, run_menu_processing_pipeline
from utils import classify_menu_image, analyze_menu_image

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
    """Select random images for testing"""
    if len(all_images) < count:
        print(f"Warning: Only {len(all_images)} images available, using all of them")
        return all_images

    return random.sample(all_images, count)


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
    """Test the complete end-to-end processing pipeline"""
    print("\n" + "=" * 60)
    print("TESTING END-TO-END PROCESSING")
    print("=" * 60)

    # Use a sample restaurant place ID from the test data
    try:
        with open("tests/example.json", "r") as f:
            data = json.load(f)

        if not data.get("restaurants"):
            print("❌ No restaurants found in example.json")
            return

        # Get the first restaurant for testing
        test_restaurant = data["restaurants"][0]
        place_id = test_restaurant.get("placeId", "")
        restaurant_name = test_restaurant.get("name", "")

        if not place_id:
            print("❌ No place_id found for test restaurant")
            return

        print(f"🏪 Testing with restaurant: {restaurant_name}")
        print(f"🆔 Place ID: {place_id}")

        # Note: This would normally pull from Supabase, but for testing we'll simulate
        print("\n⚠️  NOTE: End-to-end testing requires restaurant data in Supabase")
        print(
            "   This test demonstrates the workflow but won't execute without proper DB setup"
        )

        # Show what the pipeline would do
        processor = MenuProcessor(
            max_workers=5, classification_workers=2, analysis_workers=2
        )

        print(f"\n📊 Processor configuration:")
        print(f"   • Max workers: {processor.max_workers}")
        print(f"   • Classification workers: {processor.classification_workers}")
        print(f"   • Analysis workers: {processor.analysis_workers}")

        print(f"\n🔄 Would process: {place_id}")
        print("   1. Retrieve images from Supabase")
        print("   2. Classify images in parallel")
        print("   3. Analyze menu images in parallel")
        print("   4. Aggregate menu items")
        print("   5. Save results to Supabase")

    except Exception as e:
        print(f"❌ Error in end-to-end test: {str(e)}")


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
    print("Testing menu image classification and analysis against example.json data")

    # Load test data
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

    # Test end-to-end processing (conceptual)
    test_end_to_end_processing()

    # Print summary
    print_summary(classification_results, analysis_results)

    print(f"\n✅ Testing complete!")
    print(
        f"💡 To run full end-to-end tests, ensure your Supabase tables are set up correctly."
    )


if __name__ == "__main__":
    main()
