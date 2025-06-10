export interface Restaurant {
  id: string
  name: string
  distance: number
  location: {
    lat: number
    lng: number
  }
  rating: number
  macros: {
    protein: number
    carbs: number
    fat: number
    calories: number
  }
  bestItems: string[]
  menuItemCount: number
  priceRange: string
  popularCategories: string[]
  openNow: boolean
}
