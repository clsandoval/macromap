import type { ApiRestaurant, ApiMenuItem } from "@/types/api-response"
import type { Restaurant } from "@/types/restaurant"
import type { MenuItem } from "@/types/menu-item"

export function transformApiRestaurant(apiRestaurant: ApiRestaurant, index: number): Restaurant {
  // Calculate average macros from menu items
  const menuItems = apiRestaurant.menuItems || []
  const avgMacros =
    menuItems.length > 0
      ? {
          protein: Math.round(menuItems.reduce((sum, item) => sum + (item.protein || 0), 0) / menuItems.length),
          carbs: Math.round(menuItems.reduce((sum, item) => sum + (item.carbs || 0), 0) / menuItems.length),
          fat: Math.round(menuItems.reduce((sum, item) => sum + (item.fat || 0), 0) / menuItems.length),
          calories: Math.round(menuItems.reduce((sum, item) => sum + (item.calories || 0), 0) / menuItems.length),
        }
      : {
          protein: 0,
          carbs: 0,
          fat: 0,
          calories: 0,
        }

  // Extract popular categories from menu items
  const categoryCount = new Map<string, number>()
  menuItems.forEach((item) => {
    if (item.category) {
      categoryCount.set(item.category, (categoryCount.get(item.category) || 0) + 1)
    }
  })

  const popularCategories = Array.from(categoryCount.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)
    .map(([category]) => category)

  // Determine if restaurant is open now - with proper error handling
  const now = new Date()
  const currentDay = now.toLocaleDateString("en-US", { weekday: "long" })
  const currentTime = now.toLocaleTimeString("en-US", { hour12: false, hour: "2-digit", minute: "2-digit" })

  let openNow = false
  try {
    if (apiRestaurant.openingHours && Array.isArray(apiRestaurant.openingHours)) {
      const todayHours = apiRestaurant.openingHours.find((hours) => {
        // Ensure hours is a string before calling toLowerCase
        if (typeof hours === "string") {
          return hours.toLowerCase().includes(currentDay.toLowerCase())
        }
        return false
      })

      if (todayHours && typeof todayHours === "string" && !todayHours.toLowerCase().includes("closed")) {
        // Simple check - in a real app you'd want more sophisticated time parsing
        openNow = true
      }
    }
  } catch (error) {
    console.warn("Error parsing opening hours:", error)
    // Default to false if we can't parse opening hours
    openNow = false
  }

  return {
    id: apiRestaurant.placeId || `restaurant-${index}`,
    name: apiRestaurant.name || "Unknown Restaurant",
    distance: Math.round((apiRestaurant.distance_km || 0) * 10) / 10,
    location: {
      lat: apiRestaurant.location?.lat || 0,
      lng: apiRestaurant.location?.lng || 0,
    },
    rating: apiRestaurant.rating || 0,
    macros: avgMacros,
    bestItems: menuItems.slice(0, 2).map((item) => item.name || "Unknown Item"),
    menuItemCount: menuItems.length,
    priceRange: apiRestaurant.priceLevel || "$",
    popularCategories,
    openNow,
  }
}

export function transformApiMenuItem(apiMenuItem: ApiMenuItem, apiRestaurant: ApiRestaurant): MenuItem {
  return {
    id: apiMenuItem.id || `item-${Date.now()}-${Math.random()}`,
    name: apiMenuItem.name || "Unknown Item",
    restaurant: {
      // Ensure this ID matches the ID system used for Restaurant objects
      id: apiRestaurant.placeId || "unknown-restaurant", // CHANGED: Use apiRestaurant.placeId
      name: apiRestaurant.name || "Unknown Restaurant",
      distance: Math.round((apiRestaurant.distance_km || 0) * 10) / 10,
      location: {
        lat: apiRestaurant.location?.lat || 0,
        lng: apiRestaurant.location?.lng || 0,
      },
    },
    price: apiMenuItem.price || 0,
    servingSize: apiMenuItem.serving_size || undefined,
    macros: {
      protein: apiMenuItem.protein || 0,
      carbs: apiMenuItem.carbs || 0,
      fat: apiMenuItem.fat || 0,
      calories: apiMenuItem.calories || 0,
    },
    description: apiMenuItem.description || "",
    category: apiMenuItem.category || "Other",
  }
}

export function transformApiResponse(apiResponse: any): { restaurants: Restaurant[]; menuItems: MenuItem[] } {
  const restaurants: Restaurant[] = []
  const menuItems: MenuItem[] = []

  try {
    // Validate API response structure
    if (!apiResponse || !apiResponse.restaurants || !Array.isArray(apiResponse.restaurants)) {
      console.error("Invalid API response structure:", apiResponse)
      throw new Error("Invalid API response: missing or invalid restaurants array")
    }

    console.log("Transforming API response with", apiResponse.restaurants.length, "restaurants")

    apiResponse.restaurants.forEach((apiRestaurant: ApiRestaurant, index: number) => {
      try {
        // Transform restaurant with error handling
        const restaurant = transformApiRestaurant(apiRestaurant, index)
        restaurants.push(restaurant)

        // Transform menu items with error handling
        if (apiRestaurant.menuItems && Array.isArray(apiRestaurant.menuItems)) {
          apiRestaurant.menuItems.forEach((apiMenuItem) => {
            try {
              const menuItem = transformApiMenuItem(apiMenuItem, apiRestaurant)
              menuItems.push(menuItem)
            } catch (error) {
              console.warn("Error transforming menu item:", error, apiMenuItem)
              // Skip this menu item but continue processing others
            }
          })
        }
      } catch (error) {
        console.warn("Error transforming restaurant:", error, apiRestaurant)
        // Skip this restaurant but continue processing others
      }
    })

    console.log("Transformation complete:", {
      restaurants: restaurants.length,
      menuItems: menuItems.length,
    })
  } catch (error) {
    console.error("Error in transformApiResponse:", error)
    throw error
  }

  return { restaurants, menuItems }
}
