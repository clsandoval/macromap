import os
import math
from supabase import create_client, Client

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "your-supabase-url-here")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "your-supabase-key-here")
# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points on Earth
    using the Haversine formula

    Args:
        lat1, lon1: Latitude and longitude of first point
        lat2, lon2: Latitude and longitude of second point

    Returns:
        float: Distance in kilometers
    """
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))

    # Earth's radius in kilometers
    earth_radius = 6371
    distance = earth_radius * c

    return distance


def get_finished_restaurants_within_radius(latitude, longitude, radius_km):
    """
    Get restaurants with status 'finished' within specified radius of given coordinates

    Args:
        latitude (float): Latitude of the query point
        longitude (float): Longitude of the query point
        radius_km (float): Radius in kilometers to search within

    Returns:
        tuple: (restaurants, error)
            restaurants (list): List of restaurant records within radius
            error (str): Error message if query fails, None otherwise
    """
    try:
        # First, get all restaurants with status 'finished'
        response = (
            supabase.table("restaurants").select("*").eq("status", "finished").execute()
        )

        if not response.data:
            return [], None

        # Filter restaurants by distance
        restaurants_within_radius = []
        for restaurant in response.data:
            # Ensure the restaurant has location data
            if (
                "latitude" in restaurant
                and "longitude" in restaurant
                and restaurant["latitude"] is not None
                and restaurant["longitude"] is not None
            ):

                # Calculate distance from query point
                distance = calculate_distance(
                    latitude,
                    longitude,
                    float(restaurant["latitude"]),
                    float(restaurant["longitude"]),
                )

                # If within radius, add to results
                if distance <= radius_km:
                    restaurant["distance_km"] = round(distance, 2)
                    restaurants_within_radius.append(restaurant)

        # Sort by distance (closest first)
        restaurants_within_radius.sort(key=lambda x: x["distance_km"])

        return restaurants_within_radius, None

    except Exception as e:
        print(f"Error querying Supabase: {str(e)}")
        return [], f"Database query failed: {str(e)}"


def get_menu_items_for_restaurants(restaurant_ids):
    """
    Get all menu items for a list of restaurant UUIDs

    Args:
        restaurant_ids (list): List of restaurant UUIDs to get menu items for

    Returns:
        tuple: (menu_items, error)
            menu_items (list): List of menu item records
            error (str): Error message if query fails, None otherwise
    """
    try:
        if not restaurant_ids:
            return [], None

        # Query the menu_items table for items belonging to the specified restaurants
        response = (
            supabase.table("menu_items")
            .select("*")
            .in_("restaurant_id", restaurant_ids)
            .execute()
        )

        if response.data:
            return response.data, None
        else:
            return [], None

    except Exception as e:
        print(f"Error querying menu items from Supabase: {str(e)}")
        return [], f"Menu items query failed: {str(e)}"


def get_menu_items_grouped_by_restaurant(restaurant_ids):
    """
    Get menu items for a list of restaurant UUIDs, grouped by restaurant

    Args:
        restaurant_ids (list): List of restaurant UUIDs to get menu items for

    Returns:
        tuple: (grouped_menu_items, error)
            grouped_menu_items (dict): Dictionary mapping restaurant_id to list of menu items
            error (str): Error message if query fails, None otherwise
    """
    try:
        menu_items, error = get_menu_items_for_restaurants(restaurant_ids)

        if error:
            return {}, error

        # Group menu items by restaurant_id
        grouped_items = {}
        for item in menu_items:
            restaurant_id = item.get("restaurant_id")
            if restaurant_id not in grouped_items:
                grouped_items[restaurant_id] = []
            grouped_items[restaurant_id].append(item)

        return grouped_items, None

    except Exception as e:
        print(f"Error grouping menu items: {str(e)}")
        return {}, f"Menu items grouping failed: {str(e)}"


def get_menu_items_for_place_ids(place_ids):
    """
    Get all menu items for a list of restaurant place IDs (convenience function)

    Args:
        place_ids (list): List of restaurant place IDs to get menu items for

    Returns:
        tuple: (menu_items, error)
            menu_items (list): List of menu item records
            error (str): Error message if query fails, None otherwise
    """
    try:
        if not place_ids:
            return [], None

        # First get restaurant UUIDs from place_ids
        restaurants_response = (
            supabase.table("restaurants")
            .select("id, place_id")
            .in_("place_id", place_ids)
            .execute()
        )

        if not restaurants_response.data:
            return [], None

        # Extract restaurant UUIDs
        restaurant_ids = [r["id"] for r in restaurants_response.data]

        # Get menu items using restaurant UUIDs
        menu_items, error = get_menu_items_for_restaurants(restaurant_ids)

        if error:
            return [], error

        # Add place_id to each menu item for backward compatibility
        place_id_map = {r["id"]: r["place_id"] for r in restaurants_response.data}
        for item in menu_items:
            item["place_id"] = place_id_map.get(item["restaurant_id"])

        return menu_items, None

    except Exception as e:
        print(f"Error querying menu items by place_ids from Supabase: {str(e)}")
        return [], f"Menu items query failed: {str(e)}"


def get_restaurants_by_place_ids(place_ids):
    """
    Get restaurant records by place IDs

    Args:
        place_ids (list): List of place IDs to get restaurants for

    Returns:
        tuple: (restaurants, error)
            restaurants (list): List of restaurant records
            error (str): Error message if query fails, None otherwise
    """
    try:
        if not place_ids:
            return [], None

        response = (
            supabase.table("restaurants")
            .select("*")
            .in_("place_id", place_ids)
            .execute()
        )

        if response.data:
            return response.data, None
        else:
            return [], None

    except Exception as e:
        print(f"Error querying restaurants from Supabase: {str(e)}")
        return [], f"Restaurants query failed: {str(e)}"


def get_image_processing_logs(restaurant_ids=None, status_filter=None):
    """
    Get image processing logs

    Args:
        restaurant_ids (list): Optional list of restaurant UUIDs to filter by
        status_filter (str): Optional status to filter by

    Returns:
        tuple: (logs, error)
            logs (list): List of image processing log records
            error (str): Error message if query fails, None otherwise
    """
    try:
        query = supabase.table("image_processing_log").select("*")

        if restaurant_ids:
            query = query.in_("restaurant_id", restaurant_ids)

        if status_filter:
            query = query.eq("processing_status", status_filter)

        response = query.execute()

        if response.data:
            return response.data, None
        else:
            return [], None

    except Exception as e:
        print(f"Error querying image processing logs from Supabase: {str(e)}")
        return [], f"Image processing logs query failed: {str(e)}"


def get_processing_queue(status_filter=None, task_type=None, limit=None):
    """
    Get processing queue items

    Args:
        status_filter (str): Optional status to filter by
        task_type (str): Optional task type to filter by
        limit (int): Optional limit on number of results

    Returns:
        tuple: (queue_items, error)
            queue_items (list): List of processing queue records
            error (str): Error message if query fails, None otherwise
    """
    try:
        query = (
            supabase.table("processing_queue")
            .select("*")
            .order("priority", desc=False)
            .order("created_at", desc=False)
        )

        if status_filter:
            query = query.eq("status", status_filter)

        if task_type:
            query = query.eq("task_type", task_type)

        if limit:
            query = query.limit(limit)

        response = query.execute()

        if response.data:
            return response.data, None
        else:
            return [], None

    except Exception as e:
        print(f"Error querying processing queue from Supabase: {str(e)}")
        return [], f"Processing queue query failed: {str(e)}"


def get_restaurants_pending_processing(limit=None):
    """
    Get restaurants that are pending menu processing

    Args:
        limit (int): Optional limit on number of results

    Returns:
        tuple: (restaurants, error)
            restaurants (list): List of restaurant records with status 'pending'
            error (str): Error message if query fails, None otherwise
    """
    try:
        query = supabase.table("restaurants").select("*").eq("status", "pending")

        if limit:
            query = query.limit(limit)

        response = query.execute()

        if response.data:
            return response.data, None
        else:
            return [], None

    except Exception as e:
        print(f"Error querying pending restaurants from Supabase: {str(e)}")
        return [], f"Pending restaurants query failed: {str(e)}"


def check_restaurant_processing_status(place_ids):
    """
    Check processing status for multiple restaurants

    Args:
        place_ids (list): List of place IDs to check

    Returns:
        tuple: (status_map, error)
            status_map (dict): Dictionary mapping place_id to status
            error (str): Error message if query fails, None otherwise
    """
    try:
        if not place_ids:
            return {}, None

        # Query the restaurants table for place IDs and their status
        response = (
            supabase.table("restaurants")
            .select("place_id, status")
            .in_("place_id", place_ids)
            .execute()
        )

        if response.data:
            # Create a dictionary mapping place_id to status
            status_map = {row["place_id"]: row["status"] for row in response.data}
            return status_map, None
        else:
            return {}, None

    except Exception as e:
        print(f"Error querying Supabase: {str(e)}")
        return {}, f"Database query failed: {str(e)}"
