export interface MenuItem {
  id: string
  name: string
  restaurant: {
    id: string
    name: string
    distance: number
    location: {
      lat: number
      lng: number
    }
  }
  price: number
  servingSize?: number // in grams
  macros: {
    protein: number
    carbs: number
    fat: number
    calories: number
  }
  description: string
  category: string
}
