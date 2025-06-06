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


@dataclass
class ImageClassificationResult:
    """Result of menu image classification"""

    image_url: str
    is_menu: bool
    confidence_level: str
    reasoning: str
    image_type: str
    error: Optional[str] = None


@dataclass
class MenuAnalysisResult:
    """Result of menu analysis"""

    image_url: str
    menu_items: List[Dict]
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
                .select("images")
                .eq("place_id", place_id)
                .execute()
            )

            if not response.data:
                return [], f"No restaurant found with place_id: {place_id}"

            restaurant = response.data[0]
            images = restaurant.get("images", [])

            if not images:
                return [], f"No images found for restaurant: {place_id}"

            return images, None

        except Exception as e:
            logger.error(f"Error retrieving images for restaurant {place_id}: {str(e)}")
            return [], f"Database error: {str(e)}"

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

            # Call LLM classification function
            classification = classify_menu_image(image_url)

            return ImageClassificationResult(
                image_url=image_url,
                is_menu=classification.get("is_menu", False),
                confidence_level=classification.get("confidence_level", "low"),
                reasoning=classification.get("reasoning", ""),
                image_type=classification.get("image_type", "unknown"),
            )

        except Exception as e:
            logger.error(f"Error classifying image {image_url}: {str(e)}")
            return ImageClassificationResult(
                image_url=image_url,
                is_menu=False,
                confidence_level="low",
                reasoning="",
                image_type="unknown",
                error=str(e),
            )

    def analyze_menu_image(self, image_url: str) -> MenuAnalysisResult:
        """
        Analyze a menu image to extract menu items

        Args:
            image_url: URL of the menu image to analyze

        Returns:
            MenuAnalysisResult object
        """
        try:
            logger.info(f"Analyzing menu image: {image_url}")

            # Call LLM analysis function
            analysis = analyze_menu_image(image_url)

            return MenuAnalysisResult(
                image_url=image_url, menu_items=analysis.get("menu_items", [])
            )

        except Exception as e:
            logger.error(f"Error analyzing menu image {image_url}: {str(e)}")
            return MenuAnalysisResult(image_url=image_url, menu_items=[], error=str(e))

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
            # Get all images for the restaurant
            image_urls, error = self.get_restaurant_images(place_id)

            if error:
                return RestaurantProcessingResult(
                    place_id=place_id,
                    total_images=0,
                    menu_images_found=0,
                    total_menu_items=0,
                    processing_time=time.time() - start_time,
                    error=error,
                )

            if not image_urls:
                return RestaurantProcessingResult(
                    place_id=place_id,
                    total_images=0,
                    menu_images_found=0,
                    total_menu_items=0,
                    processing_time=time.time() - start_time,
                    error="No images to process",
                )

            # Step 1: Classify all images in parallel
            classification_results = []
            with ThreadPoolExecutor(
                max_workers=self.classification_workers
            ) as executor:
                classification_futures = {
                    executor.submit(self.classify_single_image, url): url
                    for url in image_urls
                }

                for future in as_completed(classification_futures):
                    result = future.result()
                    classification_results.append(result)

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
                    executor.submit(self.analyze_menu_image, url): url
                    for url in menu_image_urls
                }

                for future in as_completed(analysis_futures):
                    result = future.result()
                    if not result.error:
                        analysis_results.append(result)

            # Step 4: Aggregate all menu items
            all_menu_items = []
            for analysis in analysis_results:
                all_menu_items.extend(analysis.menu_items)

            if all_menu_items:
                # Use LLM to consolidate and clean up the menu items
                final_menu_items = aggregate_menu_items(all_menu_items, place_id)

                # Step 5: Save to Supabase
                self.save_menu_items_to_supabase(place_id, final_menu_items)

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
                return RestaurantProcessingResult(
                    place_id=place_id,
                    total_images=len(image_urls),
                    menu_images_found=len(menu_image_urls),
                    total_menu_items=0,
                    processing_time=time.time() - start_time,
                    error="No menu items could be extracted",
                )

        except Exception as e:
            logger.error(f"Error processing restaurant {place_id}: {str(e)}")
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
            # Prepare data for insertion
            items_to_insert = []
            for item in menu_items:
                items_to_insert.append(
                    {
                        "place_id": place_id,
                        "name": item.get("name", ""),
                        "description": item.get("description", ""),
                        "price": item.get("price"),
                        "calories": item.get("calories"),
                        "protein": item.get("protein"),
                        "carbs": item.get("carbs"),
                        "fat": item.get("fat"),
                        "category": item.get("category", ""),
                    }
                )

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
