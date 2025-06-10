export interface ApiRestaurant {
  name: string
  address: string
  rating: number
  reviewsCount: number
  category: string
  phone: string
  website: string
  priceLevel: string
  openingHours: string[]
  location: {
    lat: number
    lng: number
  }
  placeId: string
  url: string
  distance_km: number
  imageUrls: string[]
  images: {
    exterior: string[]
    interior: string[]
    menu: string[]
  }
  processing_status: string
  has_menu_items: boolean
  menuItems: ApiMenuItem[]
}

export interface ApiMenuItem {
  id: string
  restaurant_id: string
  name: string
  description: string
  price: number
  currency: string
  calories: number
  serving_size: number
  protein: number
  carbs: number
  fat: number
  fiber: number
  sugar: number
  sodium: number
  dietary_tags: string[]
  allergens: string[]
  spice_level: string | null
  category: string
  subcategory: string
  menu_section: string
  extracted_from_image_url: string
  confidence_score: number
  llm_processed: boolean
  is_available: boolean
  seasonal: boolean
  created_at: string
  updated_at: string
}

export interface ScanNearbyRequest {
  latitude: number
  longitude: number
  radius?: number
  mock?: boolean
}

export interface ScanNearbyResponse {
  success: boolean
  message: string
  restaurants: ApiRestaurant[]
  searchLocation: {
    latitude: number
    longitude: number
    radius_km: number
  }
  processing_summary: {
    total_restaurants: number
    completed: number
    pending: number
    processing: number
    new: number
    restaurants_with_menu: number
  }
  background_processing: {
    status: string
    message: string
  }
  data_source: string
}
