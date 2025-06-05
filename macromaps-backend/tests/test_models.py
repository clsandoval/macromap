"""
OpenAI Model Comparison Test for Menu Item and Price Extraction

This script tests different OpenAI models on their ability to extract
menu items and prices from a restaurant menu image.

Models tested:
- gpt-4o
- gpt-4o-mini
- gpt-4.1
- gpt-4.1-mini
- gpt-4.1-nano

Usage:
    python test_models.py --image_url "https://example.com/menu.jpg"

Environment Variables Required:
    OPENAI_API_KEY: Your OpenAI API key
"""

import os
import json
import time
import base64
import random
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import argparse
import requests

from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class MenuItem(BaseModel):
    """Individual menu item"""

    category: str
    name: str
    price: str
    description: Optional[str] = ""


class MenuExtraction(BaseModel):
    """Complete menu extraction result"""

    menu_items: List[MenuItem]
    total_items_found: int
    confidence_level: str  # "high", "medium", or "low"


class MenuClassification(BaseModel):
    """Classification of whether an image is a menu or not"""

    is_menu: bool
    confidence_level: str  # "high", "medium", or "low"
    reasoning: str
    image_type: str  # "menu", "restaurant_interior", "food_photo", "other", etc.


@dataclass
class ModelResult:
    """Container for model test results"""

    model_name: str
    response_time: float
    extracted_items: List[Dict[str, Any]]
    raw_response: str
    error: Optional[str] = None
    tokens_used: Optional[int] = None
    cost_estimate: Optional[float] = None


@dataclass
class ClassificationResult:
    """Container for classification test results"""

    model_name: str
    image_url: str
    response_time: float
    is_menu: bool
    confidence_level: str
    reasoning: str
    image_type: str
    error: Optional[str] = None
    tokens_used: Optional[int] = None
    cost_estimate: Optional[float] = None


class MenuExtractionTester:
    """Test suite for comparing OpenAI models on menu extraction"""

    # Model configurations with pricing (approximate costs per 1K tokens)
    MODELS = {
        "gpt-4.1": {
            "name": "gpt-4.1",
            "supports_vision": True,
            "cost_per_1k_tokens": 0.003,
        },
        "gpt-4.1-mini": {
            "name": "gpt-4.1-mini",
            "supports_vision": True,
            "cost_per_1k_tokens": 0.0008,
        },
        "gpt-4.1-nano": {
            "name": "gpt-4.1-nano",
            "supports_vision": True,
            "cost_per_1k_tokens": 0.0002,
        },
    }

    def __init__(self):
        """Initialize the tester with OpenAI client"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        self.client = OpenAI(api_key=api_key)
        self.results: List[ModelResult] = []

    def download_and_encode_image(self, image_url: str) -> str:
        """Download image from URL and encode to base64 string"""
        try:
            print(f"📥 Downloading image from: {image_url}")

            # Set headers to mimic a browser request
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }

            # Download the image
            response = requests.get(image_url, headers=headers, timeout=30)
            response.raise_for_status()  # Raise an exception for bad status codes

            # Check if the response contains image data
            content_type = response.headers.get("content-type", "").lower()
            if not any(
                img_type in content_type
                for img_type in ["image/", "jpeg", "jpg", "png", "gif", "webp"]
            ):
                raise ValueError(
                    f"URL does not appear to contain an image. Content-Type: {content_type}"
                )

            # Encode to base64
            image_base64 = base64.b64encode(response.content).decode("utf-8")
            print(f"✅ Image downloaded and encoded ({len(response.content)} bytes)")

            return image_base64

        except requests.exceptions.RequestException as e:
            raise Exception(f"Error downloading image from URL: {str(e)}")
        except Exception as e:
            raise Exception(f"Error processing image: {str(e)}")

    def encode_image_from_path(self, image_path: str) -> str:
        """Encode local image file to base64 string"""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8")
        except FileNotFoundError:
            raise FileNotFoundError(f"Image file not found: {image_path}")
        except Exception as e:
            raise Exception(f"Error encoding image: {str(e)}")

    def get_system_prompt(self) -> str:
        """Get the system prompt for menu extraction"""
        return """You are an expert at extracting menu items and prices from restaurant menu images.

Your task is to:
1. Identify all menu items and their corresponding prices, do not convert prices to USD, keep them as is.
2. Return the information in a structured format
3. Be as accurate as possible with item names and prices
4. If a price is unclear, mark it as "unclear" 
5. Group items by categories if visible (appetizers, mains, desserts, etc.)

Be thorough but accurate. Only include items you can clearly see and read."""

    def get_user_prompt(self) -> str:
        """Get the user prompt for menu extraction"""
        return """Please analyze this menu image and extract all menu items with their prices. 
        
Pay close attention to:
- Item names (spell them correctly)
- Prices (include currency symbols if present)
- Categories (group similar items together)
- Descriptions (if clearly visible)
        
Be thorough but only include items you can clearly read and identify."""

    def test_model_with_image(
        self, model_config: Dict[str, Any], image_input: str
    ) -> ModelResult:
        """Test a single model with the given image URL or path"""
        model_name = model_config["name"]
        print(f"\n🧪 Testing {model_name}...")

        try:
            start_time = time.time()

            if model_config["supports_vision"]:
                # Always encode to base64, whether URL or local file
                if image_input.startswith(("http://", "https://")):
                    # Download and encode URL
                    base64_image = self.download_and_encode_image(image_input)
                else:
                    # Encode local file
                    print(f"📁 Encoding local file: {image_input}")
                    base64_image = self.encode_image_from_path(image_input)

                messages = [
                    {"role": "system", "content": self.get_system_prompt()},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": self.get_user_prompt()},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                    "detail": "high",
                                },
                            },
                        ],
                    },
                ]
            else:
                # For non-vision models, we can't test image analysis
                end_time = time.time()
                return ModelResult(
                    model_name=model_name,
                    response_time=end_time - start_time,
                    extracted_items=[],
                    raw_response="",
                    error="Model does not support vision/image analysis",
                )

            # Make API call with structured output
            response = self.client.beta.chat.completions.parse(
                model=model_name,
                messages=messages,
                max_tokens=4000,  # Increased to prevent truncation
                temperature=0.1,  # Low temperature for consistency
                response_format=MenuExtraction,
            )

            end_time = time.time()
            response_time = end_time - start_time

            # Extract response data
            tokens_used = response.usage.total_tokens if response.usage else None
            cost_estimate = (
                (tokens_used * model_config["cost_per_1k_tokens"] / 1000)
                if tokens_used
                else None
            )

            # Get parsed structured data
            parsed_result = response.choices[0].message.parsed
            raw_response = response.choices[0].message.content or str(parsed_result)

            # Convert Pydantic model to list of dicts for compatibility
            extracted_items = []
            if parsed_result and parsed_result.menu_items:
                extracted_items = [
                    item.model_dump() for item in parsed_result.menu_items
                ]

            print(f"✅ {model_name} completed in {response_time:.2f}s")
            print(
                f"   Tokens used: {tokens_used}, Estimated cost: ${cost_estimate:.4f}"
                if tokens_used
                else ""
            )
            print(f"   Items found: {len(extracted_items)}")

            return ModelResult(
                model_name=model_name,
                response_time=response_time,
                extracted_items=extracted_items,
                raw_response=raw_response,
                tokens_used=tokens_used,
                cost_estimate=cost_estimate,
            )

        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time

            print(f"❌ {model_name} failed: {str(e)}")

            return ModelResult(
                model_name=model_name,
                response_time=response_time,
                extracted_items=[],
                raw_response="",
                error=str(e),
            )

    def run_comparison_test(self, image_input: str) -> List[ModelResult]:
        """Run comparison test across all models"""
        print("🚀 Starting OpenAI Model Comparison Test")
        print("=" * 50)
        print(f"Image source: {image_input}")
        print(f"Testing {len(self.MODELS)} models...")

        # For local files, verify they exist
        if (
            not image_input.startswith(("http://", "https://"))
            and not Path(image_input).exists()
        ):
            raise FileNotFoundError(f"Image file not found: {image_input}")

        results = []

        # Test each model
        for model_key, model_config in self.MODELS.items():
            result = self.test_model_with_image(model_config, image_input)
            results.append(result)

            # Small delay between API calls to be respectful
            time.sleep(1)

        self.results = results
        return results

    def generate_comparison_report(self) -> str:
        """Generate a detailed comparison report"""
        if not self.results:
            return "No test results available"

        report = ["", "📊 MODEL COMPARISON REPORT", "=" * 50, ""]

        # Summary table
        report.append("SUMMARY:")
        report.append("-" * 40)
        for result in self.results:
            status = "✅ SUCCESS" if not result.error else f"❌ ERROR: {result.error}"
            items_count = len(result.extracted_items) if result.extracted_items else 0

            report.append(f"{result.model_name:<20} | {status}")
            report.append(
                f"{'':20} | Time: {result.response_time:.2f}s | Items: {items_count}"
            )

            if result.tokens_used:
                report.append(
                    f"{'':20} | Tokens: {result.tokens_used} | Cost: ${result.cost_estimate:.4f}"
                )
            report.append("")

        # Detailed results for successful extractions
        successful_results = [
            r for r in self.results if not r.error and r.extracted_items
        ]

        if successful_results:
            report.append("\nDETAILED EXTRACTION RESULTS:")
            report.append("-" * 40)

            for result in successful_results:
                report.append(f"\n🤖 {result.model_name.upper()}:")
                report.append(f"Items extracted: {len(result.extracted_items)}")

                # Show first few items as sample
                for i, item in enumerate(result.extracted_items[:5]):
                    category = item.get("category", "N/A")
                    name = item.get("name", "N/A")
                    price = item.get("price", "N/A")
                    report.append(f"  {i+1}. [{category}] {name} - {price}")

                if len(result.extracted_items) > 5:
                    report.append(
                        f"  ... and {len(result.extracted_items) - 5} more items"
                    )

        # Performance comparison
        report.append("\n⚡ PERFORMANCE COMPARISON:")
        report.append("-" * 40)

        # Sort by response time
        sorted_by_time = sorted(
            [r for r in self.results if not r.error], key=lambda x: x.response_time
        )

        if sorted_by_time:
            report.append("Fastest to slowest:")
            for i, result in enumerate(sorted_by_time, 1):
                report.append(
                    f"  {i}. {result.model_name}: {result.response_time:.2f}s"
                )

        # Cost comparison
        cost_results = [r for r in self.results if r.cost_estimate is not None]
        if cost_results:
            report.append("\nCost comparison (estimated):")
            sorted_by_cost = sorted(cost_results, key=lambda x: x.cost_estimate)
            for i, result in enumerate(sorted_by_cost, 1):
                report.append(
                    f"  {i}. {result.model_name}: ${result.cost_estimate:.4f}"
                )

        return "\n".join(report)

    def save_results(self, output_file: str = None):
        """Save detailed results to JSON file"""
        if not output_file:
            timestamp = int(time.time())
            output_file = f"menu_extraction_test_results_{timestamp}.json"

        results_data = {
            "test_timestamp": time.time(),
            "models_tested": len(self.results),
            "results": [asdict(result) for result in self.results],
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Detailed results saved to: {output_file}")

    def get_classification_system_prompt(self) -> str:
        """Get the system prompt for menu classification"""
        return """You are an expert at analyzing images to determine if they contain clear, readable restaurant menus in English.

Your task is to:
1. Analyze the image carefully
2. Determine if the image shows a clear, readable restaurant menu in English
3. Provide your confidence level in this classification
4. Explain your reasoning
5. Identify what type of image it is

Consider these as MENU images (ALL criteria must be met):
- Physical printed menus with clear, readable text
- Digital menu boards/screens with legible content
- Menu displays on tablets/devices that are clearly visible
- Handwritten menu boards that are clearly readable
- Take-out menus with visible text
- Text listing food items with prices in English
- Menu must be clear enough to read item names and prices
- Text must be primarily in English

Consider these as NOT MENU images:
- Blurry, unclear, or unreadable menu images
- Menus in languages other than English
- Restaurant interior/exterior photos
- Food photos (individual dishes)
- People dining
- Kitchen scenes
- Logos or signage without clear menu content
- Street views or general business photos
- Images where menu text is too small/unclear to read
- Partially obscured or cut-off menus

IMPORTANT: Only classify as MENU if the text is clear, readable, and primarily in English. If you cannot clearly read menu items and prices, classify as NOT MENU.

Be thorough but decisive in your classification."""

    def get_classification_user_prompt(self) -> str:
        """Get the user prompt for menu classification"""
        return """Please analyze this image and determine if it shows a clear, readable restaurant menu in English.

Look for:
- Clear, legible text listing food/drink items
- Prices that are clearly visible next to items
- Menu structure/organization that is easy to follow
- Text that is primarily in English
- Image quality that allows you to actually read the content

CRITICAL: Only classify as MENU if:
1. The menu text is clear and readable
2. The content is primarily in English
3. You can actually see food/drink items with prices
4. The image quality is sufficient to extract menu information

If the menu is blurry, in another language, or unclear, classify as NOT MENU.

Provide your classification with detailed reasoning."""

    def test_model_classification(
        self, model_config: Dict[str, Any], image_url: str
    ) -> ClassificationResult:
        """Test a single model on menu classification"""
        model_name = model_config["name"]
        print(f"   🔍 {model_name} classifying image...")

        try:
            start_time = time.time()

            if model_config["supports_vision"]:
                # Download and encode image
                base64_image = self.download_and_encode_image(image_url)

                messages = [
                    {
                        "role": "system",
                        "content": self.get_classification_system_prompt(),
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": self.get_classification_user_prompt(),
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                    "detail": "high",
                                },
                            },
                        ],
                    },
                ]

                # Make API call with structured output
                response = self.client.beta.chat.completions.parse(
                    model=model_name,
                    messages=messages,
                    max_tokens=1000,
                    temperature=0.1,
                    response_format=MenuClassification,
                )

                end_time = time.time()
                response_time = end_time - start_time

                # Extract response data
                tokens_used = response.usage.total_tokens if response.usage else None
                cost_estimate = (
                    (tokens_used * model_config["cost_per_1k_tokens"] / 1000)
                    if tokens_used
                    else None
                )

                # Get parsed structured data
                parsed_result = response.choices[0].message.parsed

                print(f"      ✅ {model_name} classified in {response_time:.2f}s")
                print(
                    f"         Tokens used: {tokens_used}, Estimated cost: ${cost_estimate:.4f}, cost per 1k tokens: ${model_config['cost_per_1k_tokens']:.4f}"
                    if tokens_used
                    else ""
                )
                print(
                    f"         Result: {'MENU' if parsed_result.is_menu else 'NOT MENU'} ({parsed_result.confidence_level} confidence)"
                )

                return ClassificationResult(
                    model_name=model_name,
                    image_url=image_url,
                    response_time=response_time,
                    is_menu=parsed_result.is_menu,
                    confidence_level=parsed_result.confidence_level,
                    reasoning=parsed_result.reasoning,
                    image_type=parsed_result.image_type,
                    tokens_used=tokens_used,
                    cost_estimate=cost_estimate,
                )
            else:
                return ClassificationResult(
                    model_name=model_name,
                    image_url=image_url,
                    response_time=0,
                    is_menu=False,
                    confidence_level="low",
                    reasoning="Model does not support vision",
                    image_type="unknown",
                    error="Model does not support vision/image analysis",
                )

        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time

            return ClassificationResult(
                model_name=model_name,
                image_url=image_url,
                response_time=response_time,
                is_menu=False,
                confidence_level="low",
                reasoning="Error occurred",
                image_type="unknown",
                error=str(e),
            )

    def load_random_images_from_json(
        self, json_file: str, count: int = 10
    ) -> List[str]:
        """Load random image URLs from the example JSON file"""
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Collect all image URLs from all restaurants
            all_images = []
            if "restaurants" in data:
                for restaurant in data["restaurants"]:
                    if "imageUrls" in restaurant and restaurant["imageUrls"]:
                        all_images.extend(restaurant["imageUrls"])

            # Remove duplicates and filter valid URLs
            unique_images = list(set(all_images))
            valid_images = [
                url for url in unique_images if url.startswith(("http://", "https://"))
            ]

            # Randomly select the requested number of images
            if len(valid_images) < count:
                print(
                    f"⚠️  Only {len(valid_images)} valid images available, using all of them"
                )
                return valid_images

            selected_images = random.sample(valid_images, count)
            return selected_images

        except FileNotFoundError:
            raise FileNotFoundError(f"JSON file not found: {json_file}")
        except Exception as e:
            raise Exception(f"Error loading images from JSON: {str(e)}")

    def run_classification_test(
        self, json_file: str, image_count: int = 10
    ) -> List[List[ClassificationResult]]:
        """Run menu classification test on random images"""
        print("\n🎯 MENU CLASSIFICATION TEST")
        print("=" * 50)

        # Load random images
        test_images = self.load_random_images_from_json(json_file, image_count)
        print(
            f"Testing {len(test_images)} random images with {len(self.MODELS)} models..."
        )

        all_results = []

        for i, image_url in enumerate(test_images, 1):
            print(f"\n📷 Image {i}/{len(test_images)}: {image_url}")

            image_results = []
            for model_key, model_config in self.MODELS.items():
                result = self.test_model_classification(model_config, image_url)
                image_results.append(result)

                # Small delay between API calls
                time.sleep(0.5)

            all_results.append(image_results)

        return all_results

    def generate_classification_report(
        self, classification_results: List[List[ClassificationResult]]
    ) -> str:
        """Generate a detailed classification comparison report"""
        if not classification_results:
            return "No classification results available"

        report = ["", "🎯 MENU CLASSIFICATION REPORT", "=" * 60, ""]

        # Model accuracy summary
        model_stats = {}
        for image_results in classification_results:
            for result in image_results:
                if result.model_name not in model_stats:
                    model_stats[result.model_name] = {
                        "total": 0,
                        "menu_detected": 0,
                        "errors": 0,
                        "high_confidence": 0,
                        "total_cost": 0.0,
                        "total_time": 0.0,
                    }

                stats = model_stats[result.model_name]
                stats["total"] += 1

                if result.error:
                    stats["errors"] += 1
                else:
                    if result.is_menu:
                        stats["menu_detected"] += 1
                    if result.confidence_level == "high":
                        stats["high_confidence"] += 1
                    if result.cost_estimate:
                        stats["total_cost"] += result.cost_estimate
                    stats["total_time"] += result.response_time

        # Summary table
        report.append("MODEL PERFORMANCE SUMMARY:")
        report.append("-" * 60)
        for model_name, stats in model_stats.items():
            menu_rate = (
                (stats["menu_detected"] / stats["total"]) * 100
                if stats["total"] > 0
                else 0
            )
            confidence_rate = (
                (stats["high_confidence"] / stats["total"]) * 100
                if stats["total"] > 0
                else 0
            )
            avg_time = stats["total_time"] / stats["total"] if stats["total"] > 0 else 0

            report.append(
                f"{model_name:<20} | Menus detected: {stats['menu_detected']}/{stats['total']} ({menu_rate:.1f}%)"
            )
            report.append(
                f"{'':20} | High confidence: {stats['high_confidence']}/{stats['total']} ({confidence_rate:.1f}%)"
            )
            report.append(
                f"{'':20} | Avg time: {avg_time:.2f}s | Cost: ${stats['total_cost']:.4f}"
            )
            if stats["errors"] > 0:
                report.append(f"{'':20} | Errors: {stats['errors']}")
            report.append("")

        # Detailed image-by-image results
        report.append("DETAILED RESULTS BY IMAGE:")
        report.append("-" * 60)

        for i, image_results in enumerate(classification_results, 1):
            if not image_results:
                continue

            image_url = image_results[0].image_url
            report.append(f"\n📷 Image {i}: {image_url}")

            # Check for consensus
            menu_votes = sum(1 for r in image_results if r.is_menu and not r.error)
            total_valid = sum(1 for r in image_results if not r.error)
            consensus = (
                "MENU"
                if menu_votes > total_valid / 2
                else "NOT MENU" if total_valid > 0 else "UNCLEAR"
            )

            report.append(
                f"   Consensus: {consensus} ({menu_votes}/{total_valid} models say MENU)"
            )

            for result in image_results:
                if result.error:
                    report.append(
                        f"   {result.model_name:<15} ❌ ERROR: {result.error}"
                    )
                else:
                    status = "MENU" if result.is_menu else "NOT MENU"
                    report.append(
                        f"   {result.model_name:<15} {status} ({result.confidence_level} confidence)"
                    )
                    report.append(f"   {'':15} Type: {result.image_type}")
                    report.append(f"   {'':15} Reason: {result.reasoning[:50]}...")

        # Agreement analysis
        report.append("\n🤝 MODEL AGREEMENT ANALYSIS:")
        report.append("-" * 60)

        agreement_counts = {
            "unanimous_menu": 0,
            "unanimous_not_menu": 0,
            "disagreement": 0,
        }

        for image_results in classification_results:
            valid_results = [r for r in image_results if not r.error]
            if len(valid_results) < 2:
                continue

            menu_votes = sum(1 for r in valid_results if r.is_menu)

            if menu_votes == len(valid_results):
                agreement_counts["unanimous_menu"] += 1
            elif menu_votes == 0:
                agreement_counts["unanimous_not_menu"] += 1
            else:
                agreement_counts["disagreement"] += 1

        total_images = len(classification_results)
        report.append(
            f"Unanimous MENU: {agreement_counts['unanimous_menu']}/{total_images}"
        )
        report.append(
            f"Unanimous NOT MENU: {agreement_counts['unanimous_not_menu']}/{total_images}"
        )
        report.append(
            f"Disagreement: {agreement_counts['disagreement']}/{total_images}"
        )

        return "\n".join(report)


def main():
    """Main function to run the test"""
    parser = argparse.ArgumentParser(
        description="Test OpenAI models on menu extraction and classification"
    )
    parser.add_argument(
        "--image_url",
        "-u",
        help="URL of the menu image to analyze (for extraction test)",
    )
    parser.add_argument(
        "--classification_test",
        "-c",
        action="store_true",
        help="Run menu classification test using random images from example.json",
    )
    parser.add_argument(
        "--json_file",
        "-j",
        default=str(Path(__file__).parent / "example.json"),
        help="Path to JSON file with test images (default: example.json in same directory as script)",
    )
    parser.add_argument(
        "--image_count",
        "-n",
        type=int,
        default=10,
        help="Number of random images to test for classification (default: 10)",
    )
    parser.add_argument(
        "--output", "-o", help="Output file for detailed results (JSON)"
    )
    parser.add_argument(
        "--no-save", action="store_true", help="Don't save results to file"
    )

    args = parser.parse_args()

    if not args.image_url and not args.classification_test:
        print(
            "❌ Error: Must specify either --image_url for extraction test or --classification_test"
        )
        print("\nUsage examples:")
        print(
            "  Menu extraction:   python test_models.py --image_url 'https://example.com/menu.jpg'"
        )
        print("  Classification:    python test_models.py --classification_test")
        print(
            "  Both tests:        python test_models.py --image_url 'https://example.com/menu.jpg' --classification_test"
        )
        return 1

    try:
        # Initialize tester
        tester = MenuExtractionTester()

        extraction_results = None
        classification_results = None

        # Run extraction test if image URL provided
        if args.image_url:
            print("🔍 Running menu extraction test...")
            extraction_results = tester.run_comparison_test(args.image_url)

        # Run classification test if requested
        if args.classification_test:
            print("🎯 Running menu classification test...")
            classification_results = tester.run_classification_test(
                args.json_file, args.image_count
            )

        # Generate and print reports
        if extraction_results:
            extraction_report = tester.generate_comparison_report()
            print(extraction_report)

        if classification_results:
            classification_report = tester.generate_classification_report(
                classification_results
            )
            print(classification_report)

        # Save results if requested
        if not args.no_save:
            timestamp = int(time.time())

            if extraction_results and classification_results:
                # Combined results
                combined_data = {
                    "test_timestamp": time.time(),
                    "extraction_results": [
                        asdict(result) for result in extraction_results
                    ],
                    "classification_results": [
                        [asdict(result) for result in image_results]
                        for image_results in classification_results
                    ],
                }
                output_file = args.output or f"combined_test_results_{timestamp}.json"

            elif extraction_results:
                # Extraction only
                combined_data = {
                    "test_timestamp": time.time(),
                    "models_tested": len(extraction_results),
                    "results": [asdict(result) for result in extraction_results],
                }
                output_file = (
                    args.output or f"menu_extraction_test_results_{timestamp}.json"
                )

            elif classification_results:
                # Classification only
                combined_data = {
                    "test_timestamp": time.time(),
                    "images_tested": len(classification_results),
                    "models_tested": len(tester.MODELS),
                    "results": [
                        [asdict(result) for result in image_results]
                        for image_results in classification_results
                    ],
                }
                output_file = (
                    args.output or f"menu_classification_test_results_{timestamp}.json"
                )

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(combined_data, f, indent=2, ensure_ascii=False)

            print(f"\n💾 Detailed results saved to: {output_file}")

        total_tests = (len(extraction_results) if extraction_results else 0) + (
            len(classification_results) * len(tester.MODELS)
            if classification_results
            else 0
        )
        print(f"\n🎉 Test completed! Ran {total_tests} total model tests.")

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return 1

    return 0


# Example usage for direct script execution
if __name__ == "__main__":
    # You can also run tests directly without command line args for development
    if len(os.sys.argv) == 1:  # No command line arguments
        print("🔧 Development mode - using example image URL")
        print("Set OPENAI_API_KEY environment variable and provide image URL")
        print("\nUsage:")
        print("python test_models.py --image_url 'https://example.com/menu.jpg'")
        print("\nOr set up your image URL below for development:")

        # Uncomment and modify for development testing
        # example_image_url = "https://example.com/path/to/menu/image.jpg"
        # tester = MenuExtractionTester()
        # results = tester.run_comparison_test(example_image_url)
        # print(tester.generate_comparison_report())
        # tester.save_results()
    else:
        exit(main())
