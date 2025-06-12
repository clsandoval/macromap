import { useState, useEffect, useCallback } from "react"
import { getMenuItems, getRestaurantMenu, type GetMenuItemsParams, type GetRestaurantMenuParams, type MenuItemsResponse, type RestaurantMenuResponse, ApiError } from "@/lib/api"
import type { ApiMenuItem } from "@/types/api-response"

export interface UseMenuItemsOptions {
    latitude?: number
    longitude?: number
    radius?: number
    sort_by?: string
    sort_order?: "asc" | "desc"
    restaurant_id?: string
    limit?: number
    autoFetch?: boolean
}

export interface UseMenuItemsReturn {
    menuItems: ApiMenuItem[]
    pagination: MenuItemsResponse["pagination"] | RestaurantMenuResponse["pagination"] | null
    loading: boolean
    error: string | null
    fetchMenuItems: (page?: number) => Promise<void>
    refetch: () => Promise<void>
    hasMore: boolean
    loadMore: () => Promise<void>
    setSortBy: (sortBy: string) => void
    setSortOrder: (sortOrder: "asc" | "desc") => void
    setRadius: (radius: number) => void
    setRestaurantFilter: (restaurantId?: string) => void
    currentParams: GetMenuItemsParams | GetRestaurantMenuParams | null
    restaurantInfo?: RestaurantMenuResponse["restaurant"]
}

export function useMenuItems(options: UseMenuItemsOptions = {}): UseMenuItemsReturn {
    const {
        latitude,
        longitude,
        radius = 10,
        sort_by = "restaurant_distance",
        sort_order = "asc",
        restaurant_id,
        limit = 20,
        autoFetch = true
    } = options

    const [menuItems, setMenuItems] = useState<ApiMenuItem[]>([])
    const [pagination, setPagination] = useState<MenuItemsResponse["pagination"] | RestaurantMenuResponse["pagination"] | null>(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [currentParams, setCurrentParams] = useState<GetMenuItemsParams | GetRestaurantMenuParams | null>(null)
    const [currentSortBy, setCurrentSortBy] = useState(sort_by)
    const [currentSortOrder, setCurrentSortOrder] = useState(sort_order)
    const [currentRadius, setCurrentRadius] = useState(radius)
    const [currentRestaurantId, setCurrentRestaurantId] = useState(restaurant_id)
    const [restaurantInfo, setRestaurantInfo] = useState<RestaurantMenuResponse["restaurant"] | undefined>()

    const fetchMenuItems = useCallback(async (page: number = 1) => {
        if (!latitude || !longitude) {
            setError("Location is required")
            return
        }

        try {
            setLoading(true)
            setError(null)

            let response: MenuItemsResponse | RestaurantMenuResponse
            let params: GetMenuItemsParams | GetRestaurantMenuParams

            if (currentRestaurantId) {
                // Fetch menu for specific restaurant
                const restaurantParams: GetRestaurantMenuParams = {
                    restaurant_id: currentRestaurantId,
                    latitude,
                    longitude,
                    page,
                    limit,
                    sort_by: currentSortBy,
                    sort_order: currentSortOrder
                }
                response = await getRestaurantMenu(restaurantParams)
                params = restaurantParams

                // Set restaurant info if it's a restaurant menu response
                if ('restaurant' in response) {
                    setRestaurantInfo(response.restaurant)
                }
            } else {
                // Fetch menu items from all restaurants in radius
                const menuParams: GetMenuItemsParams = {
                    latitude,
                    longitude,
                    page,
                    limit,
                    radius: currentRadius,
                    sort_by: currentSortBy,
                    sort_order: currentSortOrder,
                    restaurant_id: currentRestaurantId
                }
                response = await getMenuItems(menuParams)
                params = menuParams
                setRestaurantInfo(undefined)
            }

            if (page === 1) {
                setMenuItems(response.data)
            } else {
                setMenuItems(prev => [...prev, ...response.data])
            }

            setPagination(response.pagination)
            setCurrentParams(params)
        } catch (err) {
            const errorMessage = err instanceof ApiError ? err.message : "Failed to fetch menu items"
            setError(errorMessage)
            console.error("Error fetching menu items:", err)
        } finally {
            setLoading(false)
        }
    }, [latitude, longitude, limit, currentRadius, currentSortBy, currentSortOrder, currentRestaurantId])

    const refetch = useCallback(() => {
        return fetchMenuItems(1)
    }, [fetchMenuItems])

    const loadMore = useCallback(async () => {
        if (!pagination?.has_next || loading) return
        await fetchMenuItems(pagination.page + 1)
    }, [pagination, loading, fetchMenuItems])

    const setSortBy = useCallback((sortBy: string) => {
        setCurrentSortBy(sortBy)
        setMenuItems([]) // Clear current data
        setPagination(null)
    }, [])

    const setSortOrder = useCallback((sortOrder: "asc" | "desc") => {
        setCurrentSortOrder(sortOrder)
        setMenuItems([]) // Clear current data
        setPagination(null)
    }, [])

    const setRadius = useCallback((newRadius: number) => {
        setCurrentRadius(newRadius)
        setMenuItems([]) // Clear current data
        setPagination(null)
    }, [])

    const setRestaurantFilter = useCallback((restaurantId?: string) => {
        setCurrentRestaurantId(restaurantId)
        setMenuItems([]) // Clear current data
        setPagination(null)
        setRestaurantInfo(undefined)
    }, [])

    // Auto-fetch when dependencies change
    useEffect(() => {
        if (autoFetch && latitude && longitude) {
            fetchMenuItems(1)
        }
    }, [autoFetch, latitude, longitude, currentSortBy, currentSortOrder, currentRadius, currentRestaurantId, fetchMenuItems])

    return {
        menuItems,
        pagination,
        loading,
        error,
        fetchMenuItems,
        refetch,
        hasMore: pagination?.has_next ?? false,
        loadMore,
        setSortBy,
        setSortOrder,
        setRadius,
        setRestaurantFilter,
        currentParams,
        restaurantInfo
    }
} 