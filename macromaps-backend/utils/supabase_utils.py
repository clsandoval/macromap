import os
from supabase import create_client, Client


# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "your-supabase-url-here")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "your-supabase-key-here")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_finished_restaurant_place_ids(place_ids):
    """
    Query Supabase table to get place IDs where status is 'finished'

    Args:
        place_ids (list): List of place IDs to check

    Returns:
        tuple: (finished_place_ids, error)
            finished_place_ids (list): List of place IDs with status 'finished'
            error (str): Error message if query fails, None otherwise
    """
    try:
        if not place_ids:
            return [], None

        # Query the restaurants table for place IDs with status 'finished'
        response = (
            supabase.table("restaurants")
            .select("place_id")
            .in_("place_id", place_ids)
            .eq("status", "finished")
            .execute()
        )

        if response.data:
            # Extract just the place_id values from the response
            finished_place_ids = [row["place_id"] for row in response.data]
            return finished_place_ids, None
        else:
            return [], None

    except Exception as e:
        print(f"Error querying Supabase: {str(e)}")
        return [], f"Database query failed: {str(e)}"


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
