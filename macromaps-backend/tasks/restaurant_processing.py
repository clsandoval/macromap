import threading
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional
from dataclasses import dataclass

from .menu_processing import MenuProcessor
from utils.supabase_utils import supabase

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RestaurantTaskResult:
    """Result of processing a single restaurant task"""

    place_id: str
    success: bool
    menu_items_extracted: int
    processing_time: float
    error: Optional[str] = None


class RestaurantProcessor:
    """Handles restaurant processing tasks including menu extraction"""

    def __init__(self, max_concurrent_restaurants: int = 3):
        self.max_concurrent_restaurants = max_concurrent_restaurants
        self.menu_processor = MenuProcessor(
            max_workers=5, classification_workers=3, analysis_workers=2
        )

    def process_restaurant_menus(self, place_id: str) -> RestaurantTaskResult:
        """
        Process menus for a single restaurant

        Args:
            place_id: Restaurant place ID to process

        Returns:
            RestaurantTaskResult with processing details
        """
        start_time = time.time()

        try:
            logger.info(f"Starting menu processing for restaurant: {place_id}")

            # Use the menu processor to handle all menu extraction
            result = self.menu_processor.process_restaurant_images(place_id)

            processing_time = time.time() - start_time

            if result.error:
                logger.error(f"Menu processing failed for {place_id}: {result.error}")
                return RestaurantTaskResult(
                    place_id=place_id,
                    success=False,
                    menu_items_extracted=0,
                    processing_time=processing_time,
                    error=result.error,
                )

            logger.info(
                f"Menu processing completed for {place_id}: {result.total_menu_items} items extracted in {processing_time:.2f}s"
            )

            return RestaurantTaskResult(
                place_id=place_id,
                success=True,
                menu_items_extracted=result.total_menu_items,
                processing_time=processing_time,
            )

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Unexpected error processing restaurant {place_id}: {str(e)}")

            return RestaurantTaskResult(
                place_id=place_id,
                success=False,
                menu_items_extracted=0,
                processing_time=processing_time,
                error=str(e),
            )

    def update_restaurant_status(self, place_id: str, status: str) -> bool:
        """
        Update restaurant processing status in Supabase

        Args:
            place_id: Restaurant place ID
            status: New status ('pending', 'processing', 'finished', 'error')

        Returns:
            Success boolean
        """
        try:
            response = (
                supabase.table("restaurants")
                .update({"status": status})
                .eq("place_id", place_id)
                .execute()
            )
            return True
        except Exception as e:
            logger.error(f"Failed to update status for restaurant {place_id}: {str(e)}")
            return False

    def process_restaurants_batch(
        self, place_ids: List[str]
    ) -> Dict[str, RestaurantTaskResult]:
        """
        Process multiple restaurants in parallel

        Args:
            place_ids: List of restaurant place IDs to process

        Returns:
            Dictionary mapping place_id to RestaurantTaskResult
        """
        if not place_ids:
            logger.info("No restaurants to process")
            return {}

        logger.info(f"Starting parallel processing of {len(place_ids)} restaurants")
        start_time = time.time()

        results = {}

        # Update all restaurants to 'processing' status
        for place_id in place_ids:
            self.update_restaurant_status(place_id, "processing")

        # Add a small delay to ensure database writes are committed
        time.sleep(1.0)
        logger.info("Database status updates completed, starting menu processing...")

        # Process restaurants in parallel
        with ThreadPoolExecutor(
            max_workers=self.max_concurrent_restaurants
        ) as executor:
            # Submit all restaurant processing tasks
            future_to_place_id = {
                executor.submit(self.process_restaurant_menus, place_id): place_id
                for place_id in place_ids
            }

            # Collect results as they complete
            for future in as_completed(future_to_place_id):
                place_id = future_to_place_id[future]

                try:
                    result = future.result()
                    results[place_id] = result

                    # Update restaurant status based on result
                    final_status = "finished" if result.success else "error"
                    self.update_restaurant_status(place_id, final_status)

                    logger.info(
                        f"Completed processing for {place_id}: {'SUCCESS' if result.success else 'FAILED'}"
                    )

                except Exception as e:
                    logger.error(
                        f"Exception occurred processing restaurant {place_id}: {str(e)}"
                    )
                    results[place_id] = RestaurantTaskResult(
                        place_id=place_id,
                        success=False,
                        menu_items_extracted=0,
                        processing_time=0,
                        error=str(e),
                    )
                    # Update status to error
                    self.update_restaurant_status(place_id, "error")

        total_time = time.time() - start_time
        successful_count = sum(1 for r in results.values() if r.success)
        total_menu_items = sum(
            r.menu_items_extracted for r in results.values() if r.success
        )

        logger.info(
            f"Batch processing complete: {successful_count}/{len(place_ids)} restaurants processed successfully"
        )
        logger.info(f"Total menu items extracted: {total_menu_items}")
        logger.info(f"Total batch processing time: {total_time:.2f}s")

        return results


def process_restaurants_async(place_ids: List[str], max_concurrent: int = 3) -> None:
    """
    Asynchronously process restaurants in a background thread

    Args:
        place_ids: List of restaurant place IDs to process
        max_concurrent: Maximum number of concurrent restaurant processing tasks
    """

    def background_task():
        processor = RestaurantProcessor(max_concurrent_restaurants=max_concurrent)
        processor.process_restaurants_batch(place_ids)

    # Start processing in background thread
    thread = threading.Thread(target=background_task, daemon=True)
    thread.start()

    logger.info(f"Started background processing for {len(place_ids)} restaurants")


def trigger_restaurant_processing(restaurants_data: List[Dict]) -> Dict[str, any]:
    """
    Extract place IDs from restaurant data and trigger background processing
    Only processes restaurants whose status is not 'complete' or 'pending'

    Args:
        restaurants_data: List of restaurant dictionaries from Apify

    Returns:
        Summary of triggered processing
    """
    place_ids = []

    # Extract place IDs from restaurant data
    for restaurant in restaurants_data:
        place_id = restaurant.get("placeId")
        if place_id:
            place_ids.append(place_id)

    if not place_ids:
        logger.warning("No valid place IDs found in restaurant data")
        return {
            "triggered": False,
            "restaurants_count": 0,
            "restaurants_to_process": 0,
            "skipped_count": 0,
            "message": "No valid restaurants found for processing",
        }

    # Check status of all restaurants in database
    try:
        response = (
            supabase.table("restaurants")
            .select("place_id, status")
            .in_("place_id", place_ids)
            .execute()
        )

        # Create status map for existing restaurants
        status_map = {}
        if response.data:
            status_map = {row["place_id"]: row["status"] for row in response.data}

        # Filter out restaurants that are already finished or currently processing
        place_ids_to_process = []
        skipped_restaurants = []

        for place_id in place_ids:
            current_status = status_map.get(
                place_id, "new"
            )  # Default to "new" if not in DB

            # Skip restaurants that are already finished or currently being processed
            if current_status in ["finished", "processing"]:
                skipped_restaurants.append(place_id)
                logger.info(
                    f"Skipping restaurant {place_id} - status: {current_status}"
                )
            else:
                # Process restaurants with status: pending, new, error
                place_ids_to_process.append(place_id)
                logger.info(
                    f"Will process restaurant {place_id} - status: {current_status}"
                )

        if not place_ids_to_process:
            logger.info(
                "No restaurants need processing - all are finished or currently processing"
            )
            return {
                "triggered": False,
                "restaurants_count": len(place_ids),
                "restaurants_to_process": 0,
                "skipped_count": len(skipped_restaurants),
                "message": f"All {len(place_ids)} restaurants are already finished or processing",
                "skipped_statuses": {
                    pid: status_map.get(pid, "new") for pid in skipped_restaurants
                },
            }

        # Trigger background processing only for restaurants that need it
        process_restaurants_async(place_ids_to_process)

        logger.info(
            f"Triggered processing for {len(place_ids_to_process)} restaurants, skipped {len(skipped_restaurants)}"
        )

        return {
            "triggered": True,
            "restaurants_count": len(place_ids),
            "restaurants_to_process": len(place_ids_to_process),
            "skipped_count": len(skipped_restaurants),
            "message": f"Menu processing started for {len(place_ids_to_process)} restaurants (skipped {len(skipped_restaurants)} already finished/processing)",
            "skipped_statuses": {
                pid: status_map.get(pid, "new") for pid in skipped_restaurants
            },
        }

    except Exception as e:
        logger.error(f"Error checking restaurant statuses: {str(e)}")
        # Fallback to processing all restaurants if status check fails
        process_restaurants_async(place_ids)

        return {
            "triggered": True,
            "restaurants_count": len(place_ids),
            "restaurants_to_process": len(place_ids),
            "skipped_count": 0,
            "message": f"Menu processing started for {len(place_ids)} restaurants (status check failed, processing all)",
            "error": f"Status check failed: {str(e)}",
        }
