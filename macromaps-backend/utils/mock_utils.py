import random
import math


def generate_mock_restaurants(user_lat, user_lng, count=10, radius_km=2):
    """Generate mock restaurant data scattered within radius_km of user location"""

    # Mock restaurant names and types
    restaurant_names = [
        "Bella Vista Italian",
        "Dragon Palace Chinese",
        "Taco Fiesta",
        "Burger Junction",
        "Sushi Zen",
        "Mediterranean Grill",
        "Thai Garden",
        "Pizza Corner",
        "French Bistro",
        "Indian Spice",
        "BBQ Smokehouse",
        "Healthy Greens",
        "Seafood Bay",
        "Steakhouse Prime",
        "Vegan Delight",
        "Coffee & More",
        "Noodle House",
        "Greek Taverna",
        "Mexican Cantina",
        "Sandwich Shop",
    ]

    categories = [
        "Italian restaurant",
        "Chinese restaurant",
        "Mexican restaurant",
        "Fast food restaurant",
        "Sushi restaurant",
        "Mediterranean restaurant",
        "Thai restaurant",
        "Pizza restaurant",
        "French restaurant",
        "Indian restaurant",
        "Barbecue restaurant",
        "Health food restaurant",
        "Seafood restaurant",
        "Steak house",
        "Vegan restaurant",
        "Coffee shop",
        "Asian noodle restaurant",
        "Greek restaurant",
        "Mexican restaurant",
        "Sandwich shop",
    ]

    addresses = [
        "Main St",
        "Oak Ave",
        "Pine Rd",
        "Maple Dr",
        "Cedar Ln",
        "Elm St",
        "Park Ave",
        "1st St",
        "2nd Ave",
        "Broadway",
        "Market St",
        "Church St",
    ]

    mock_restaurants = []

    for i in range(min(count, len(restaurant_names))):
        # Generate random coordinates within radius
        lat, lng = generate_random_coordinates_in_radius(user_lat, user_lng, radius_km)

        # Generate mock data
        restaurant = {
            "title": restaurant_names[i],
            "address": f"{random.randint(100, 9999)} {random.choice(addresses)}, City, State {random.randint(10000, 99999)}",
            "totalScore": round(random.uniform(3.0, 5.0), 1),
            "reviewsCount": random.randint(15, 500),
            "categoryName": categories[i % len(categories)],
            "phone": f"+1-{random.randint(100, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
            "website": (
                f"https://www.{restaurant_names[i].lower().replace(' ', '').replace('&', 'and')}.com"
                if random.random() > 0.3
                else ""
            ),
            "priceLevel": random.choice(["$", "$$", "$$$", "$$$$", ""]),
            "openingHours": generate_mock_hours(),
            "location": {"lat": lat, "lng": lng},
            "placeId": f"ChIJ{random.randint(100000, 999999)}_{i}",
            "url": f"https://maps.google.com/?cid={random.randint(1000000000, 9999999999)}",
            "menuItems": generate_mock_menu_items(
                restaurant_names[i], categories[i % len(categories)]
            ),
        }
        mock_restaurants.append(restaurant)

    return mock_restaurants


def generate_random_coordinates_in_radius(center_lat, center_lng, radius_km):
    """Generate random lat/lng within radius_km of center point"""
    # Convert radius from kilometers to degrees (rough approximation)
    radius_deg = radius_km / 111.0  # 1 degree ≈ 111 km

    # Generate random angle and distance
    angle = random.uniform(0, 2 * math.pi)
    distance = random.uniform(0, radius_deg)

    # Calculate new coordinates
    lat = center_lat + distance * math.cos(angle)
    lng = center_lng + distance * math.sin(angle) / math.cos(math.radians(center_lat))

    return round(lat, 6), round(lng, 6)


def generate_mock_hours():
    """Generate mock opening hours"""
    days = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    hours = []

    for day in days:
        if random.random() > 0.1:  # 90% chance restaurant is open
            open_time = random.choice(
                ["7:00 AM", "8:00 AM", "9:00 AM", "10:00 AM", "11:00 AM"]
            )
            close_time = random.choice(
                ["8:00 PM", "9:00 PM", "10:00 PM", "11:00 PM", "12:00 AM"]
            )
            hours.append(f"{day}: {open_time}–{close_time}")
        else:
            hours.append(f"{day}: Closed")

    return hours


def generate_mock_menu_items(restaurant_name, category):
    """Generate mock menu items with nutritional data for a restaurant"""

    # Menu items by category
    menu_templates = {
        "Italian restaurant": [
            {
                "name": "Margherita Pizza",
                "base_calories": 280,
                "base_protein": 12,
                "base_carbs": 36,
                "base_fat": 10,
                "base_price": 14.99,
            },
            {
                "name": "Chicken Parmigiana",
                "base_calories": 520,
                "base_protein": 45,
                "base_carbs": 28,
                "base_fat": 24,
                "base_price": 18.99,
            },
            {
                "name": "Caesar Salad",
                "base_calories": 190,
                "base_protein": 8,
                "base_carbs": 12,
                "base_fat": 14,
                "base_price": 12.99,
            },
            {
                "name": "Spaghetti Carbonara",
                "base_calories": 580,
                "base_protein": 25,
                "base_carbs": 55,
                "base_fat": 28,
                "base_price": 16.99,
            },
            {
                "name": "Grilled Salmon",
                "base_calories": 380,
                "base_protein": 42,
                "base_carbs": 8,
                "base_fat": 18,
                "base_price": 22.99,
            },
        ],
        "Chinese restaurant": [
            {
                "name": "Kung Pao Chicken",
                "base_calories": 420,
                "base_protein": 32,
                "base_carbs": 18,
                "base_fat": 24,
                "base_price": 15.99,
            },
            {
                "name": "Vegetable Fried Rice",
                "base_calories": 340,
                "base_protein": 8,
                "base_carbs": 58,
                "base_fat": 12,
                "base_price": 11.99,
            },
            {
                "name": "Sweet & Sour Pork",
                "base_calories": 480,
                "base_protein": 28,
                "base_carbs": 42,
                "base_fat": 22,
                "base_price": 16.99,
            },
            {
                "name": "Steamed Dumplings",
                "base_calories": 220,
                "base_protein": 12,
                "base_carbs": 28,
                "base_fat": 8,
                "base_price": 9.99,
            },
            {
                "name": "Beef Broccoli",
                "base_calories": 320,
                "base_protein": 35,
                "base_carbs": 12,
                "base_fat": 15,
                "base_price": 17.99,
            },
        ],
        "Mexican restaurant": [
            {
                "name": "Chicken Burrito Bowl",
                "base_calories": 450,
                "base_protein": 38,
                "base_carbs": 45,
                "base_fat": 16,
                "base_price": 13.99,
            },
            {
                "name": "Fish Tacos (2pc)",
                "base_calories": 320,
                "base_protein": 24,
                "base_carbs": 28,
                "base_fat": 14,
                "base_price": 12.99,
            },
            {
                "name": "Carne Asada",
                "base_calories": 380,
                "base_protein": 42,
                "base_carbs": 8,
                "base_fat": 20,
                "base_price": 19.99,
            },
            {
                "name": "Veggie Quesadilla",
                "base_calories": 520,
                "base_protein": 18,
                "base_carbs": 48,
                "base_fat": 28,
                "base_price": 11.99,
            },
            {
                "name": "Chicken Fajitas",
                "base_calories": 420,
                "base_protein": 36,
                "base_carbs": 22,
                "base_fat": 22,
                "base_price": 16.99,
            },
        ],
        "Fast food restaurant": [
            {
                "name": "Grilled Chicken Sandwich",
                "base_calories": 380,
                "base_protein": 32,
                "base_carbs": 38,
                "base_fat": 12,
                "base_price": 8.99,
            },
            {
                "name": "Turkey Club Wrap",
                "base_calories": 420,
                "base_protein": 28,
                "base_carbs": 35,
                "base_fat": 18,
                "base_price": 9.99,
            },
            {
                "name": "Garden Salad",
                "base_calories": 150,
                "base_protein": 6,
                "base_carbs": 18,
                "base_fat": 8,
                "base_price": 7.99,
            },
            {
                "name": "Protein Bowl",
                "base_calories": 380,
                "base_protein": 42,
                "base_carbs": 28,
                "base_fat": 14,
                "base_price": 11.99,
            },
            {
                "name": "Veggie Burger",
                "base_calories": 320,
                "base_protein": 18,
                "base_carbs": 42,
                "base_fat": 10,
                "base_price": 9.99,
            },
        ],
        "Sushi restaurant": [
            {
                "name": "Salmon Teriyaki Bowl",
                "base_calories": 420,
                "base_protein": 38,
                "base_carbs": 45,
                "base_fat": 12,
                "base_price": 16.99,
            },
            {
                "name": "California Roll (8pc)",
                "base_calories": 280,
                "base_protein": 18,
                "base_carbs": 32,
                "base_fat": 8,
                "base_price": 12.99,
            },
            {
                "name": "Chirashi Bowl",
                "base_calories": 380,
                "base_protein": 42,
                "base_carbs": 38,
                "base_fat": 8,
                "base_price": 22.99,
            },
            {
                "name": "Miso Soup",
                "base_calories": 80,
                "base_protein": 6,
                "base_carbs": 8,
                "base_fat": 3,
                "base_price": 4.99,
            },
            {
                "name": "Poke Bowl",
                "base_calories": 350,
                "base_protein": 32,
                "base_carbs": 35,
                "base_fat": 10,
                "base_price": 15.99,
            },
        ],
        "Thai restaurant": [
            {
                "name": "Pad Thai",
                "base_calories": 480,
                "base_protein": 22,
                "base_carbs": 58,
                "base_fat": 18,
                "base_price": 14.99,
            },
            {
                "name": "Green Curry Chicken",
                "base_calories": 420,
                "base_protein": 35,
                "base_carbs": 28,
                "base_fat": 22,
                "base_price": 16.99,
            },
            {
                "name": "Tom Yum Soup",
                "base_calories": 180,
                "base_protein": 18,
                "base_carbs": 12,
                "base_fat": 8,
                "base_price": 9.99,
            },
            {
                "name": "Massaman Beef",
                "base_calories": 520,
                "base_protein": 38,
                "base_carbs": 32,
                "base_fat": 28,
                "base_price": 18.99,
            },
            {
                "name": "Papaya Salad",
                "base_calories": 120,
                "base_protein": 4,
                "base_carbs": 28,
                "base_fat": 2,
                "base_price": 8.99,
            },
        ],
    }

    # Default menu for unknown categories
    default_menu = [
        {
            "name": "Grilled Chicken Breast",
            "base_calories": 380,
            "base_protein": 42,
            "base_carbs": 8,
            "base_fat": 18,
            "base_price": 16.99,
        },
        {
            "name": "House Salad",
            "base_calories": 180,
            "base_protein": 8,
            "base_carbs": 15,
            "base_fat": 12,
            "base_price": 9.99,
        },
        {
            "name": "Pasta Primavera",
            "base_calories": 450,
            "base_protein": 15,
            "base_carbs": 65,
            "base_fat": 16,
            "base_price": 13.99,
        },
        {
            "name": "Fish & Chips",
            "base_calories": 620,
            "base_protein": 32,
            "base_carbs": 48,
            "base_fat": 32,
            "base_price": 15.99,
        },
    ]

    menu_template = menu_templates.get(category, default_menu)
    menu_items = []

    # Generate 3-5 menu items per restaurant
    num_items = random.randint(3, min(5, len(menu_template)))
    selected_items = random.sample(menu_template, num_items)

    for item in selected_items:
        # Add some variation to the base values
        calories_variation = random.uniform(0.9, 1.1)
        price_variation = random.uniform(0.85, 1.15)

        menu_item = {
            "id": f"{restaurant_name.lower().replace(' ', '_')}_{item['name'].lower().replace(' ', '_')}",
            "name": item["name"],
            "description": f"Fresh {item['name'].lower()} prepared with quality ingredients",
            "price": round(item["base_price"] * price_variation, 2),
            "nutrition": {
                "calories": int(item["base_calories"] * calories_variation),
                "protein": round(item["base_protein"] * calories_variation, 1),
                "carbs": round(item["base_carbs"] * calories_variation, 1),
                "fat": round(item["base_fat"] * calories_variation, 1),
                "fiber": round(random.uniform(2, 8), 1),
                "sugar": round(random.uniform(1, 12), 1),
                "sodium": random.randint(300, 1200),
            },
            "dietary_tags": generate_dietary_tags(item["name"], category),
            "spice_level": (
                random.choice([None, "Mild", "Medium", "Hot"])
                if "Thai" in category or "Mexican" in category or "Indian" in category
                else None
            ),
            "portion_size": random.choice(["Regular", "Large"]),
            "available": random.choice(
                [True, True, True, False]
            ),  # 75% chance available
        }
        menu_items.append(menu_item)

    return menu_items


def generate_dietary_tags(item_name, category):
    """Generate dietary restriction tags for menu items"""
    tags = []

    # Vegetarian/Vegan detection
    veggie_keywords = ["vegetable", "veggie", "salad", "tofu", "quinoa", "rice"]
    meat_keywords = ["chicken", "beef", "pork", "fish", "salmon", "turkey", "duck"]

    item_lower = item_name.lower()

    if any(keyword in item_lower for keyword in veggie_keywords) and not any(
        keyword in item_lower for keyword in meat_keywords
    ):
        tags.append("Vegetarian")
        if "cheese" not in item_lower and "egg" not in item_lower:
            tags.append("Vegan")

    # Gluten-free detection
    if "salad" in item_lower or "bowl" in item_lower or "grilled" in item_lower:
        if random.random() > 0.5:  # 50% chance for applicable items
            tags.append("Gluten-Free")

    # High protein
    protein_keywords = ["chicken", "beef", "salmon", "protein", "grilled"]
    if any(keyword in item_lower for keyword in protein_keywords):
        tags.append("High-Protein")

    # Low carb
    if "salad" in item_lower or (
        "grilled" in item_lower
        and "rice" not in item_lower
        and "pasta" not in item_lower
    ):
        tags.append("Low-Carb")

    return tags
