import type { ScanNearbyRequest, ScanNearbyResponse, ApiRestaurant, ApiMenuItem } from "@/types/api-response"

// Update the API_BASE_URL constant to use the correct URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "https://macromap.fly.dev"

export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public code?: string,
  ) {
    super(message)
    this.name = "ApiError"
  }
}

// Mock data generators that match the API response structure
function generateMockApiRestaurants(latitude: number, longitude: number, count = 12): ApiRestaurant[] {
  const restaurants: ApiRestaurant[] = []

  const restaurantNames = [
    "Bella Italia",
    "Green Garden Cafe",
    "Protein Palace",
    "Macro Meals",
    "Fit Fuel Kitchen",
    "Clean Cuisine",
    "Muscle Bistro",
    "Lean & Mean Eatery",
    "Power Plates",
    "Healthy Harvest",
    "Nutrition Station",
    "Fresh Fuel Co",
  ]

  const categories = [
    "Italian restaurant",
    "Health food restaurant",
    "American restaurant",
    "Mediterranean restaurant",
    "Asian restaurant",
    "Mexican restaurant",
    "Cafe",
    "Fast food restaurant",
  ]

  const priceLevels = ["$", "$$", "$$$", "$$$$"]

  for (let i = 0; i < count; i++) {
    const distance = Math.random() * 4.5 + 0.2 // 0.2 to 4.7 km
    const bearing = Math.random() * 2 * Math.PI
    const latOffset = (distance / 111) * Math.cos(bearing) // Rough conversion
    const lngOffset = (distance / (111 * Math.cos((latitude * Math.PI) / 180))) * Math.sin(bearing)

    const restaurant: ApiRestaurant = {
      name: restaurantNames[i % restaurantNames.length],
      address: `${100 + i} Main St, San Francisco, CA`,
      rating: Math.round((Math.random() * 2 + 3) * 10) / 10, // 3.0 to 5.0
      reviewsCount: Math.floor(Math.random() * 500) + 50,
      category: categories[Math.floor(Math.random() * categories.length)],
      phone: `+1-555-${String(Math.floor(Math.random() * 10000)).padStart(4, "0")}`,
      website: `https://${restaurantNames[i % restaurantNames.length].toLowerCase().replace(/\s+/g, "-")}.com`,
      priceLevel: priceLevels[Math.floor(Math.random() * priceLevels.length)],
      openingHours: [
        "Monday: 11:00 AM – 10:00 PM",
        "Tuesday: 11:00 AM – 10:00 PM",
        "Wednesday: 11:00 AM – 10:00 PM",
        "Thursday: 11:00 AM – 10:00 PM",
        "Friday: 11:00 AM – 11:00 PM",
        "Saturday: 11:00 AM – 11:00 PM",
        "Sunday: 12:00 PM – 9:00 PM",
      ],
      location: {
        lat: latitude + latOffset,
        lng: longitude + lngOffset,
      },
      placeId: `ChIJd8BlQ2BZwokRAFUEcm_qrc${i}`,
      url: `https://maps.google.com/?cid=12345678${i}`,
      distance_km: Math.round(distance * 10) / 10,
      imageUrls: [
        `https://lh5.googleusercontent.com/p/restaurant-${i}-1.jpg`,
        `https://lh5.googleusercontent.com/p/restaurant-${i}-2.jpg`,
      ],
      images: {
        exterior: [`https://lh5.googleusercontent.com/p/ext-${i}-1.jpg`],
        interior: [`https://lh5.googleusercontent.com/p/int-${i}-1.jpg`],
        menu: [`https://lh5.googleusercontent.com/p/menu-${i}-1.jpg`],
      },
      processing_status: "finished",
      has_menu_items: true,
      menuItems: generateMockMenuItems(i, 3 + Math.floor(Math.random() * 8)), // 3-10 items per restaurant
    }

    restaurants.push(restaurant)
  }

  return restaurants.sort((a, b) => a.distance_km - b.distance_km)
}

function generateMockMenuItems(restaurantIndex: number, count: number): ApiMenuItem[] {
  const menuItems: ApiMenuItem[] = []

  const itemNames = [
    "Grilled Chicken Power Bowl",
    "Protein Pancakes",
    "Quinoa Power Salad",
    "Turkey & Avocado Wrap",
    "Grilled Salmon Plate",
    "Veggie Protein Burger",
    "Lean Beef Bowl",
    "Greek Yogurt Parfait",
    "Chicken Caesar Salad",
    "Tuna Poke Bowl",
    "Protein Pasta",
    "Fish Tacos",
    "Protein Burrito",
    "Chicken Stir Fry",
    "Protein Smoothie Bowl",
  ]

  const categories = ["Bowls", "Breakfast", "Salads", "Wraps", "Entrees", "Burgers", "Smoothies"]
  const subcategories = ["Classic", "Signature", "Healthy", "Premium", "Seasonal"]
  const menuSections = ["Main Courses", "Breakfast", "Appetizers", "Desserts", "Beverages"]
  const dietaryTags = [["vegetarian"], ["vegan"], ["gluten-free"], ["keto"], ["high-protein"], []]
  const allergens = [["gluten", "dairy"], ["nuts"], ["shellfish"], ["soy"], []]

  for (let i = 0; i < count; i++) {
    const hasIncompleteData = Math.random() < 0.15 // 15% chance of incomplete data
    const price = hasIncompleteData ? 0 : Math.round((Math.random() * 15 + 8) * 100) / 100

    const protein = Math.floor(Math.random() * 40 + 15)
    const carbs = Math.floor(Math.random() * 50 + 10)
    const fat = Math.floor(Math.random() * 25 + 5)
    const calories = Math.floor(protein * 4 + carbs * 4 + fat * 9 + Math.random() * 50)

    const menuItem: ApiMenuItem = {
      id: `550e8400-e29b-41d4-a716-44665544${String(restaurantIndex * 100 + i).padStart(4, "0")}`,
      restaurant_id: `550e8400-e29b-41d4-a716-44665544${String(restaurantIndex).padStart(4, "0")}`,
      name: itemNames[i % itemNames.length],
      description: `Delicious ${itemNames[i % itemNames.length].toLowerCase()} made with fresh, high-quality ingredients`,
      price,
      currency: "USD",
      calories,
      serving_size: hasIncompleteData ? 0 : Math.floor(Math.random() * 300 + 200),
      protein,
      carbs,
      fat,
      fiber: Math.floor(Math.random() * 8 + 2),
      sugar: Math.floor(Math.random() * 15 + 3),
      sodium: Math.floor(Math.random() * 800 + 200),
      dietary_tags: dietaryTags[Math.floor(Math.random() * dietaryTags.length)],
      allergens: allergens[Math.floor(Math.random() * allergens.length)],
      spice_level: Math.random() > 0.7 ? ["mild", "medium", "hot"][Math.floor(Math.random() * 3)] : null,
      category: categories[i % categories.length],
      subcategory: subcategories[Math.floor(Math.random() * subcategories.length)],
      menu_section: menuSections[Math.floor(Math.random() * menuSections.length)],
      extracted_from_image_url: `https://lh5.googleusercontent.com/p/menu-${restaurantIndex}-1.jpg`,
      confidence_score: Math.round((Math.random() * 0.3 + 0.7) * 100) / 100, // 0.7 to 1.0
      llm_processed: true,
      is_available: Math.random() > 0.1, // 90% available
      seasonal: Math.random() > 0.8, // 20% seasonal
      created_at: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString(),
      updated_at: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString(),
    }

    menuItems.push(menuItem)
  }

  return menuItems
}

// Update the scanNearby function to use the correct endpoint path
export async function scanNearby(request: ScanNearbyRequest): Promise<ScanNearbyResponse> {
  try {
    // Use /scan-nearby directly without /api prefix
    const endpoint = `${API_BASE_URL}/scan-nearby`
    console.log("Making API request to:", endpoint)
    console.log("Request payload:", request)

    const response = await fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    })

    console.log("API response status:", response.status)

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      console.error("API error response:", errorData)
      throw new ApiError(
        errorData.message || `HTTP ${response.status}: ${response.statusText}`,
        response.status,
        errorData.code,
      )
    }

    const data = await response.json()
    console.log("API response data:", data)

    if (!data.success) {
      throw new ApiError(data.message || "API request failed")
    }

    return data
  } catch (error) {
    console.error("API request failed:", error)

    if (error instanceof ApiError) {
      throw error
    }

    // Network or other errors
    if (error instanceof TypeError && error.message.includes("fetch")) {
      throw new ApiError("Network error: Unable to connect to the API. Please check your internet connection.")
    }

    throw new ApiError(error instanceof Error ? error.message : "Network error occurred")
  }
}
