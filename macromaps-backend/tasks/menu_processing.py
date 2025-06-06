import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from queue import Queue
import logging

from utils.supabase_utils import supabase
from utils.llm_utils import (
    classify_menu_image,
    analyze_menu_image,
    aggregate_menu_items,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Model pricing per 1 million tokens (in USD)
MODEL_PRICING = {
    "gpt-4.1": 2.00,
    "gpt-4.1-mini": 0.40,
    "gpt-4.1-nano": 0.10,
    "gpt-4o": 2.00,  # Default fallback
}


def calculate_estimated_cost(tokens_used: int, model: str) -> float:
    """
    Calculate estimated cost based on token usage and model pricing

    Args:
        tokens_used: Number of tokens used
        model: Model name (e.g., "gpt-4.1-nano")

    Returns:
        Estimated cost in USD
    """
    if not tokens_used or tokens_used <= 0:
        return 0.0

    # Get cost per 1M tokens, default to gpt-4o pricing if model not found
    cost_per_1m = MODEL_PRICING.get(model, MODEL_PRICING["gpt-4o"])

    # Calculate cost: (tokens_used / 1,000,000) * cost_per_1m
    estimated_cost = (tokens_used / 1_000_000) * cost_per_1m

    return round(estimated_cost, 10)  # Round to 10 decimal places for precision


@dataclass
class ImageClassificationResult:
    """Result of menu image classification"""

    image_url: str
    is_menu: bool
    confidence_level: str
    reasoning: str
    image_type: str
    tokens_used: int = 0
    model_used: str = ""
    estimated_cost: float = 0.0
    error: Optional[str] = None


@dataclass
class MenuAnalysisResult:
    """Result of menu analysis"""

    image_url: str
    menu_items: List[Dict]
    tokens_used: int = 0
    model_used: str = ""
    estimated_cost: float = 0.0
    error: Optional[str] = None


@dataclass
class RestaurantProcessingResult:
    """Result of processing a single restaurant"""

    place_id: str
    total_images: int
    menu_images_found: int
    total_menu_items: int
    processing_time: float
    error: Optional[str] = None


class MenuProcessor:
    """Main class for processing restaurant menu images with threading"""

    def __init__(
        self,
        max_workers: int = 10,
        classification_workers: int = 5,
        analysis_workers: int = 3,
    ):
        self.max_workers = max_workers
        self.classification_workers = classification_workers
        self.analysis_workers = analysis_workers
        self.results_lock = threading.Lock()

    def get_restaurant_images(self, place_id: str) -> Tuple[List[str], Optional[str]]:
        """
        Retrieve all image URLs for a given restaurant from Supabase

        Args:
            place_id: Restaurant place ID

        Returns:
            Tuple of (image_urls, error_message)
        """
        try:
            response = (
                supabase.table("restaurants")
                .select("id, image_urls, images")
                .eq("place_id", place_id)
                .execute()
            )

            if not response.data:
                return [], f"No restaurant found with place_id: {place_id}"

            restaurant = response.data[0]

            # Get image URLs from both possible sources
            image_urls = []

            # From image_urls array field
            if restaurant.get("image_urls"):
                image_urls.extend(restaurant["image_urls"])

            # From images JSONB field (if it contains URLs)
            images_json = restaurant.get("images")
            if images_json:
                if isinstance(images_json, dict):
                    # If images is a dict with an items array
                    if "items" in images_json and isinstance(
                        images_json["items"], list
                    ):
                        image_urls.extend(images_json["items"])
                elif isinstance(images_json, list):
                    # If images is directly a list
                    image_urls.extend(images_json)

            if not image_urls:
                return [], f"No images found for restaurant: {place_id}"

            # Remove duplicates while preserving order
            unique_urls = list(dict.fromkeys(image_urls))

            return unique_urls, None

        except Exception as e:
            logger.error(f"Error retrieving images for restaurant {place_id}: {str(e)}")
            return [], f"Database error: {str(e)}"

    def sort_images_by_menu_likelihood(self, image_urls: List[str]) -> List[str]:
        """
        Sort image URLs by likelihood of containing a menu.
        URLs with /p/ are prioritized as they're more likely to have menus.

        Args:
            image_urls: List of image URLs to sort

        Returns:
            Sorted list of image URLs
        """

        def get_priority(url: str) -> int:
            """Return priority score (lower = higher priority)"""
            if "/p/" in url:
                return 0  # Highest priority - most likely to have menus
            elif "/gps-cs-s/" in url:
                return 1  # Lower priority
            else:
                return 2  # Lowest priority - other URL types

        return sorted(image_urls, key=get_priority)

    def classify_single_image(self, image_url: str) -> ImageClassificationResult:
        """
        Classify a single image to determine if it's a menu

        Args:
            image_url: URL of the image to classify

        Returns:
            ImageClassificationResult object
        """
        try:
            logger.info(f"Classifying image: {image_url}")

            # Specify the model to use
            model = "gpt-4.1-mini"

            # Call LLM classification function
            classification = classify_menu_image(image_url, model=model)

            # Get tokens used and calculate cost
            tokens_used = classification.get("tokens_used", 0)
            estimated_cost = calculate_estimated_cost(tokens_used, model)

            return ImageClassificationResult(
                image_url=image_url,
                is_menu=classification.get("is_menu", False),
                confidence_level=classification.get("confidence_level", "low"),
                reasoning=classification.get("reasoning", ""),
                image_type=classification.get("image_type", "unknown"),
                tokens_used=tokens_used,
                model_used=model,
                estimated_cost=estimated_cost,
            )

        except Exception as e:
            logger.error(f"Error classifying image {image_url}: {str(e)}")
            return ImageClassificationResult(
                image_url=image_url,
                is_menu=False,
                confidence_level="low",
                reasoning="",
                image_type="unknown",
                tokens_used=0,
                model_used="gpt-4.1-nano",
                estimated_cost=0.0,
                error=str(e),
            )

    def analyze_menu_image(
        self, image_url: str, restaurant_data: Dict = None
    ) -> MenuAnalysisResult:
        """
        Analyze a menu image to extract menu items

        Args:
            image_url: URL of the menu image to analyze
            restaurant_data: Restaurant data including location and name

        Returns:
            MenuAnalysisResult object
        """
        try:
            logger.info(f"Analyzing menu image: {image_url}")

            # Specify the model to use for analysis (can be different from classification)
            model = "gpt-4.1"  # Use higher quality model for menu analysis

            # Extract location data if available
            latitude = restaurant_data.get("latitude") if restaurant_data else None
            longitude = restaurant_data.get("longitude") if restaurant_data else None
            restaurant_name = restaurant_data.get("name") if restaurant_data else None

            # Call LLM analysis function with location context
            analysis = analyze_menu_image(
                image_url,
                model=model,
                latitude=latitude,
                longitude=longitude,
                restaurant_name=restaurant_name,
            )

            # Get tokens used and calculate cost
            tokens_used = analysis.get("tokens_used", 0)
            estimated_cost = calculate_estimated_cost(tokens_used, model)

            return MenuAnalysisResult(
                image_url=image_url,
                menu_items=analysis.get("menu_items", []),
                tokens_used=tokens_used,
                model_used=model,
                estimated_cost=estimated_cost,
            )

        except Exception as e:
            logger.error(f"Error analyzing menu image {image_url}: {str(e)}")
            return MenuAnalysisResult(
                image_url=image_url,
                menu_items=[],
                tokens_used=0,
                model_used="gpt-4.1",
                estimated_cost=0.0,
                error=str(e),
            )

    def process_restaurant_images(self, place_id: str) -> RestaurantProcessingResult:
        """
        Process all images for a single restaurant

        Args:
            place_id: Restaurant place ID to process

        Returns:
            RestaurantProcessingResult object
        """
        start_time = time.time()
        logger.info(f"Processing restaurant: {place_id}")

        try:
            # Get restaurant ID, location, and images
            restaurant_response = (
                supabase.table("restaurants")
                .select("id, name, latitude, longitude, image_urls, images")
                .eq("place_id", place_id)
                .execute()
            )

            if not restaurant_response.data:
                return RestaurantProcessingResult(
                    place_id=place_id,
                    total_images=0,
                    menu_images_found=0,
                    total_menu_items=0,
                    processing_time=time.time() - start_time,
                    error=f"No restaurant found with place_id: {place_id}",
                )

            restaurant = restaurant_response.data[0]
            restaurant_id = restaurant["id"]

            # Add to processing queue
            self.add_to_processing_queue(restaurant_id)
            self.update_processing_queue_status(restaurant_id, "processing")

            # Get all images for the restaurant
            image_urls, error = self.get_restaurant_images(place_id)

            if error or not image_urls:
                self.update_processing_queue_status(
                    restaurant_id, "failed", error or "No images to process"
                )
                return RestaurantProcessingResult(
                    place_id=place_id,
                    total_images=0,
                    menu_images_found=0,
                    total_menu_items=0,
                    processing_time=time.time() - start_time,
                    error=error or "No images to process",
                )

            # Sort images by menu likelihood
            sorted_image_urls = self.sort_images_by_menu_likelihood(image_urls)

            # Step 1: Classify all images in parallel
            classification_results = []
            with ThreadPoolExecutor(
                max_workers=self.classification_workers
            ) as executor:
                classification_futures = {
                    executor.submit(self.classify_single_image, url): url
                    for url in sorted_image_urls
                }

                for future in as_completed(classification_futures):
                    result = future.result()
                    classification_results.append(result)

                    # Log each image classification
                    confidence = 0.5  # Default confidence
                    if result.confidence_level == "high":
                        confidence = 0.8
                    elif result.confidence_level == "medium":
                        confidence = 0.6
                    elif result.confidence_level == "low":
                        confidence = 0.3

                    self.log_image_processing(
                        restaurant_id=restaurant_id,
                        image_url=result.image_url,
                        is_menu=result.is_menu,
                        confidence=confidence,
                        status="completed" if not result.error else "failed",
                        extracted_items_count=0,
                        tokens_used=result.tokens_used,
                        estimated_cost=result.estimated_cost,
                    )

            # Step 2: Filter menu images and analyze them in parallel
            menu_image_urls = [
                result.image_url
                for result in classification_results
                if result.is_menu and not result.error
            ]

            logger.info(
                f"Found {len(menu_image_urls)} menu images out of {len(image_urls)} total images for restaurant {place_id}"
            )

            if not menu_image_urls:
                self.update_processing_queue_status(restaurant_id, "completed")
                return RestaurantProcessingResult(
                    place_id=place_id,
                    total_images=len(image_urls),
                    menu_images_found=0,
                    total_menu_items=0,
                    processing_time=time.time() - start_time,
                )

            # Step 3: Analyze menu images in parallel
            analysis_results = []
            with ThreadPoolExecutor(max_workers=self.analysis_workers) as executor:
                analysis_futures = {
                    executor.submit(self.analyze_menu_image, url, restaurant): url
                    for url in menu_image_urls
                }

                for future in as_completed(analysis_futures):
                    result = future.result()
                    if not result.error:
                        analysis_results.append(result)

                        # Update log with extracted items count, tokens, and cost
                        try:
                            supabase.table("image_processing_log").update(
                                {
                                    "extracted_items_count": len(result.menu_items),
                                    "image_token_count": result.tokens_used,
                                    "estimated_cost": result.estimated_cost,  # Use calculated cost
                                }
                            ).eq("restaurant_id", restaurant_id).eq(
                                "image_url", result.image_url
                            ).execute()
                        except Exception as e:
                            logger.error(
                                f"Error updating image processing log for {result.image_url}: {str(e)}"
                            )
                    else:
                        # Log analysis failure
                        try:
                            supabase.table("image_processing_log").update(
                                {
                                    "processing_status": "failed",
                                    "extracted_items_count": 0,
                                    "image_token_count": result.tokens_used,
                                    "estimated_cost": result.estimated_cost,  # Use calculated cost
                                }
                            ).eq("restaurant_id", restaurant_id).eq(
                                "image_url", result.image_url
                            ).execute()
                        except Exception as e:
                            logger.error(
                                f"Error updating failed analysis log for {result.image_url}: {str(e)}"
                            )

            # Step 4: Aggregate all menu items
            all_menu_items = []
            for analysis in analysis_results:
                # Add source image URL to each menu item
                for item in analysis.menu_items:
                    item["extracted_from_image_url"] = analysis.image_url
                all_menu_items.extend(analysis.menu_items)

            if all_menu_items:
                # Use LLM to consolidate and clean up the menu items with location context
                final_menu_items = aggregate_menu_items(
                    all_menu_items,
                    place_id,
                    latitude=restaurant.get("latitude"),
                    longitude=restaurant.get("longitude"),
                    restaurant_name=restaurant.get("name"),
                )

                # Step 5: Save to Supabase
                success = self.save_menu_items_to_supabase(place_id, final_menu_items)

                if success:
                    self.update_processing_queue_status(restaurant_id, "completed")

                    # Log processing summary with costs and tokens
                    processing_summary = self.log_restaurant_processing_summary(
                        restaurant_id, place_id
                    )

                    logger.info(
                        f"Successfully processed restaurant {place_id}: {len(final_menu_items)} menu items saved"
                    )

                    return RestaurantProcessingResult(
                        place_id=place_id,
                        total_images=len(image_urls),
                        menu_images_found=len(menu_image_urls),
                        total_menu_items=len(final_menu_items),
                        processing_time=time.time() - start_time,
                    )
                else:
                    error_msg = "Failed to save menu items to database"
                    self.update_processing_queue_status(
                        restaurant_id, "failed", error_msg
                    )
                    return RestaurantProcessingResult(
                        place_id=place_id,
                        total_images=len(image_urls),
                        menu_images_found=len(menu_image_urls),
                        total_menu_items=0,
                        processing_time=time.time() - start_time,
                        error=error_msg,
                    )
            else:
                error_msg = "No menu items could be extracted"
                self.update_processing_queue_status(restaurant_id, "completed")
                return RestaurantProcessingResult(
                    place_id=place_id,
                    total_images=len(image_urls),
                    menu_images_found=len(menu_image_urls),
                    total_menu_items=0,
                    processing_time=time.time() - start_time,
                    error=error_msg,
                )

        except Exception as e:
            logger.error(f"Error processing restaurant {place_id}: {str(e)}")

            # Try to update processing queue status if we have restaurant_id
            try:
                if "restaurant_id" in locals():
                    self.update_processing_queue_status(restaurant_id, "failed", str(e))
            except:
                pass  # Ignore if we can't update the queue

            return RestaurantProcessingResult(
                place_id=place_id,
                total_images=0,
                menu_images_found=0,
                total_menu_items=0,
                processing_time=time.time() - start_time,
                error=str(e),
            )

    def save_menu_items_to_supabase(
        self, place_id: str, menu_items: List[Dict]
    ) -> bool:
        """
        Save menu items to Supabase

        Args:
            place_id: Restaurant place ID
            menu_items: List of menu item dictionaries

        Returns:
            Success boolean
        """
        try:
            # First, get the restaurant UUID from place_id
            restaurant_response = (
                supabase.table("restaurants")
                .select("id")
                .eq("place_id", place_id)
                .execute()
            )

            if not restaurant_response.data:
                logger.error(f"Restaurant not found with place_id: {place_id}")
                return False

            restaurant_id = restaurant_response.data[0]["id"]

            # Prepare data for insertion
            items_to_insert = []
            for item in menu_items:
                menu_item = {
                    "restaurant_id": restaurant_id,  # Use restaurant UUID
                    "name": item.get("name", ""),
                    "description": item.get("description", ""),
                    "price": float(item.get("price")) if item.get("price") else None,
                    "currency": item.get("currency", "USD"),
                    # Nutritional Information
                    "calories": (
                        int(item.get("calories")) if item.get("calories") else None
                    ),
                    "serving_size": (
                        float(item.get("serving_size"))
                        if item.get("serving_size")
                        else None
                    ),
                    "protein": (
                        float(item.get("protein")) if item.get("protein") else None
                    ),
                    "carbs": float(item.get("carbs")) if item.get("carbs") else None,
                    "fat": float(item.get("fat")) if item.get("fat") else None,
                    "fiber": float(item.get("fiber")) if item.get("fiber") else None,
                    "sugar": float(item.get("sugar")) if item.get("sugar") else None,
                    "sodium": float(item.get("sodium")) if item.get("sodium") else None,
                    # Dietary Classifications
                    "dietary_tags": item.get("dietary_tags", []),
                    "allergens": item.get("allergens", []),
                    "spice_level": item.get("spice_level", ""),
                    # Menu Organization
                    "category": item.get("category", ""),
                    "subcategory": item.get("subcategory", ""),
                    "menu_section": item.get("menu_section", ""),
                    # Processing Metadata
                    "extracted_from_image_url": item.get(
                        "extracted_from_image_url", ""
                    ),
                    "confidence_score": (
                        float(item.get("confidence_score"))
                        if item.get("confidence_score")
                        else None
                    ),
                    "llm_processed": True,  # Since we're using LLM to process
                    # Availability
                    "is_available": item.get("is_available", True),
                    "seasonal": item.get("seasonal", False),
                }

                # Only add non-None values to avoid database errors
                clean_item = {
                    k: v for k, v in menu_item.items() if v is not None and v != ""
                }
                items_to_insert.append(clean_item)

            # Insert into menu_items table
            if items_to_insert:
                response = (
                    supabase.table("menu_items").insert(items_to_insert).execute()
                )
                logger.info(
                    f"Inserted {len(items_to_insert)} menu items for restaurant {place_id}"
                )

                # Update restaurant status to 'finished'
                supabase.table("restaurants").update({"status": "finished"}).eq(
                    "place_id", place_id
                ).execute()

                return True

            return False

        except Exception as e:
            logger.error(f"Error saving menu items for restaurant {place_id}: {str(e)}")
            return False

    def get_restaurants_to_process(self, status_filter: str = "pending") -> List[str]:
        """
        Get list of restaurant place IDs that need processing

        Args:
            status_filter: Status to filter by (default: "pending")

        Returns:
            List of place IDs
        """
        try:
            response = (
                supabase.table("restaurants")
                .select("place_id")
                .eq("status", status_filter)
                .execute()
            )

            if response.data:
                return [restaurant["place_id"] for restaurant in response.data]

            return []

        except Exception as e:
            logger.error(f"Error getting restaurants to process: {str(e)}")
            return []

    def process_all_restaurants(
        self, restaurant_ids: Optional[List[str]] = None
    ) -> Dict[str, RestaurantProcessingResult]:
        """
        Process all restaurants with threading

        Args:
            restaurant_ids: Optional list of specific restaurant IDs to process.
                          If None, will process all pending restaurants.

        Returns:
            Dictionary mapping place_id to RestaurantProcessingResult
        """
        start_time = time.time()

        # Get restaurants to process
        if restaurant_ids is None:
            restaurant_ids = self.get_restaurants_to_process()

        if not restaurant_ids:
            logger.info("No restaurants to process")
            return {}

        logger.info(f"Starting processing of {len(restaurant_ids)} restaurants")

        results = {}

        # Process restaurants in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            restaurant_futures = {
                executor.submit(self.process_restaurant_images, place_id): place_id
                for place_id in restaurant_ids
            }

            for future in as_completed(restaurant_futures):
                place_id = restaurant_futures[future]
                try:
                    result = future.result()
                    results[place_id] = result

                    # Log progress
                    if result.error:
                        logger.error(
                            f"Failed to process restaurant {place_id}: {result.error}"
                        )
                    else:
                        logger.info(
                            f"Completed restaurant {place_id}: {result.menu_images_found} menus, {result.total_menu_items} items"
                        )

                except Exception as e:
                    logger.error(
                        f"Unexpected error processing restaurant {place_id}: {str(e)}"
                    )
                    results[place_id] = RestaurantProcessingResult(
                        place_id=place_id,
                        total_images=0,
                        menu_images_found=0,
                        total_menu_items=0,
                        processing_time=0,
                        error=str(e),
                    )

        total_time = time.time() - start_time
        successful_restaurants = sum(1 for r in results.values() if not r.error)
        total_menu_items = sum(
            r.total_menu_items for r in results.values() if not r.error
        )

        logger.info(
            f"Processing complete: {successful_restaurants}/{len(restaurant_ids)} restaurants processed successfully"
        )
        logger.info(f"Total menu items extracted: {total_menu_items}")
        logger.info(f"Total processing time: {total_time:.2f} seconds")

        return results

    def log_image_processing(
        self,
        restaurant_id: str,
        image_url: str,
        is_menu: bool,
        confidence: float,
        status: str,
        extracted_items_count: int = 0,
        tokens_used: int = 0,
        estimated_cost: float = 0.0,
    ) -> bool:
        """
        Log image processing results to the image_processing_log table

        Args:
            restaurant_id: Restaurant UUID
            image_url: URL of the processed image
            is_menu: Whether the image was classified as a menu
            confidence: Classification confidence (0.00-1.00)
            status: Processing status (pending, processing, completed, failed)
            extracted_items_count: Number of items extracted from this image
            tokens_used: Number of tokens used for processing this image
            estimated_cost: Estimated cost in USD for processing this image

        Returns:
            Success boolean
        """
        try:
            log_entry = {
                "restaurant_id": restaurant_id,
                "image_url": image_url,
                "is_menu_image": is_menu,
                "classification_confidence": min(
                    max(confidence, 0.00), 1.00
                ),  # Ensure 0-1 range
                "processing_status": status,
                "extracted_items_count": extracted_items_count,
                "image_token_count": tokens_used,
                "estimated_cost": estimated_cost,  # Already rounded in calculate_estimated_cost
            }

            response = (
                supabase.table("image_processing_log").insert(log_entry).execute()
            )
            return True

        except Exception as e:
            logger.error(f"Error logging image processing for {image_url}: {str(e)}")
            return False

    def add_to_processing_queue(
        self, restaurant_id: str, task_type: str = "menu_extraction", priority: int = 5
    ) -> bool:
        """
        Add a restaurant to the processing queue

        Args:
            restaurant_id: Restaurant UUID
            task_type: Type of task (menu_extraction, nutrition_analysis)
            priority: Task priority (1-10, lower is higher priority)

        Returns:
            Success boolean
        """
        try:
            queue_entry = {
                "restaurant_id": restaurant_id,
                "task_type": task_type,
                "priority": priority,
                "status": "pending",
                "attempts": 0,
                "max_attempts": 3,
            }

            response = supabase.table("processing_queue").insert(queue_entry).execute()
            return True

        except Exception as e:
            logger.error(
                f"Error adding restaurant {restaurant_id} to processing queue: {str(e)}"
            )
            return False

    def update_processing_queue_status(
        self, restaurant_id: str, status: str, error_message: str = None
    ) -> bool:
        """
        Update processing queue status for a restaurant

        Args:
            restaurant_id: Restaurant UUID
            status: New status (processing, completed, failed)
            error_message: Optional error message if failed

        Returns:
            Success boolean
        """
        try:
            update_data = {"status": status}

            if status == "processing":
                update_data["started_at"] = "NOW()"
            elif status in ["completed", "failed"]:
                update_data["completed_at"] = "NOW()"

            if error_message:
                update_data["error_message"] = error_message

            response = (
                supabase.table("processing_queue")
                .update(update_data)
                .eq("restaurant_id", restaurant_id)
                .eq("task_type", "menu_extraction")
                .execute()
            )
            return True

        except Exception as e:
            logger.error(
                f"Error updating processing queue for restaurant {restaurant_id}: {str(e)}"
            )
            return False

    def log_restaurant_processing_summary(
        self, restaurant_id: str, place_id: str
    ) -> Dict[str, float]:
        """
        Calculate and log summary statistics for restaurant processing

        Args:
            restaurant_id: Restaurant UUID
            place_id: Restaurant place ID for logging

        Returns:
            Dictionary with processing statistics
        """
        try:
            # Get all processing logs for this restaurant
            logs_response = (
                supabase.table("image_processing_log")
                .select(
                    "image_token_count, estimated_cost, is_menu_image, extracted_items_count"
                )
                .eq("restaurant_id", restaurant_id)
                .execute()
            )

            if not logs_response.data:
                return {}

            # Calculate totals
            total_tokens = sum(
                log.get("image_token_count", 0) for log in logs_response.data
            )
            total_cost = sum(
                log.get("estimated_cost", 0.0) for log in logs_response.data
            )
            total_menu_images = sum(
                1 for log in logs_response.data if log.get("is_menu_image")
            )
            total_items_extracted = sum(
                log.get("extracted_items_count", 0) for log in logs_response.data
            )

            summary = {
                "total_tokens": total_tokens,
                "total_cost": round(total_cost, 4),
                "total_images_processed": len(logs_response.data),
                "menu_images_found": total_menu_images,
                "total_items_extracted": total_items_extracted,
                "avg_cost_per_image": (
                    round(total_cost / len(logs_response.data), 4)
                    if logs_response.data
                    else 0
                ),
                "avg_tokens_per_image": (
                    round(total_tokens / len(logs_response.data), 2)
                    if logs_response.data
                    else 0
                ),
            }

            logger.info(
                f"Processing summary for restaurant {place_id}: "
                f"{summary['total_tokens']} tokens, ${summary['total_cost']}, "
                f"{summary['menu_images_found']} menu images, "
                f"{summary['total_items_extracted']} items extracted "
                f"(Classification: gpt-4.1-nano, Analysis: gpt-4.1)"
            )

            return summary

        except Exception as e:
            logger.error(
                f"Error calculating processing summary for restaurant {restaurant_id}: {str(e)}"
            )
            return {}


def run_menu_processing_pipeline(
    restaurant_ids: Optional[List[str]] = None, max_workers: int = 10
):
    """
    Convenience function to run the full menu processing pipeline

    Args:
        restaurant_ids: Optional list of specific restaurant IDs to process
        max_workers: Maximum number of worker threads

    Returns:
        Processing results dictionary
    """
    processor = MenuProcessor(max_workers=max_workers)
    return processor.process_all_restaurants(restaurant_ids)
