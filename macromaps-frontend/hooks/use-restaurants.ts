import { useState, useEffect, useCallback } from "react"
import { getRestaurants, type GetRestaurantsParams, type RestaurantsResponse, ApiError } from "@/lib/api"
import type { ApiRestaurant } from "@/types/api-response"

export interface UseRestaurantsOptions {
    latitude?: number
    longitude?: number
    radius?: number
    sort_by?: "distance" | "rating" | "reviews_count" | "name"
    limit?: number
    autoFetch?: boolean
}

export interface UseRestaurantsReturn {
    restaurants: ApiRestaurant[]
    pagination: RestaurantsResponse["pagination"] | null
    loading: boolean
    error: string | null
    fetchRestaurants: (page?: number) => Promise<void>
    refetch: () => Promise<void>
    hasMore: boolean
    loadMore: () => Promise<void>
    setSortBy: (sortBy: "distance" | "rating" | "reviews_count" | "name") => void
    setRadius: (radius: number) => void
    currentParams: GetRestaurantsParams | null
}

export function useRestaurants(options: UseRestaurantsOptions = {}): UseRestaurantsReturn {
    const {
        latitude,
        longitude,
        radius = 10,
        sort_by = "distance",
        limit = 20,
        autoFetch = true
    } = options

    const [restaurants, setRestaurants] = useState<ApiRestaurant[]>([])
    const [pagination, setPagination] = useState<RestaurantsResponse["pagination"] | null>(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [currentParams, setCurrentParams] = useState<GetRestaurantsParams | null>(null)
    const [currentSortBy, setCurrentSortBy] = useState(sort_by)
    const [currentRadius, setCurrentRadius] = useState(radius)

    const fetchRestaurants = useCallback(async (page: number = 1) => {
        if (!latitude || !longitude) {
            setError("Location is required")
            return
        }

        const params: GetRestaurantsParams = {
            latitude,
            longitude,
            page,
            limit,
            radius: currentRadius,
            sort_by: currentSortBy
        }

        try {
            setLoading(true)
            setError(null)

            const response = await getRestaurants(params)

            if (page === 1) {
                setRestaurants(response.data)
            } else {
                setRestaurants(prev => [...prev, ...response.data])
            }

            setPagination(response.pagination)
            setCurrentParams(params)
        } catch (err) {
            const errorMessage = err instanceof ApiError ? err.message : "Failed to fetch restaurants"
            setError(errorMessage)
            console.error("Error fetching restaurants:", err)
        } finally {
            setLoading(false)
        }
    }, [latitude, longitude, limit, currentRadius, currentSortBy])

    const refetch = useCallback(() => {
        return fetchRestaurants(1)
    }, [fetchRestaurants])

    const loadMore = useCallback(async () => {
        if (!pagination?.has_next || loading) return
        await fetchRestaurants(pagination.page + 1)
    }, [pagination, loading, fetchRestaurants])

    const setSortBy = useCallback((sortBy: "distance" | "rating" | "reviews_count" | "name") => {
        setCurrentSortBy(sortBy)
        setRestaurants([]) // Clear current data
        setPagination(null)
    }, [])

    const setRadius = useCallback((newRadius: number) => {
        setCurrentRadius(newRadius)
        setRestaurants([]) // Clear current data
        setPagination(null)
    }, [])

    // Auto-fetch when dependencies change
    useEffect(() => {
        if (autoFetch && latitude && longitude) {
            fetchRestaurants(1)
        }
    }, [autoFetch, latitude, longitude, currentSortBy, currentRadius, fetchRestaurants])

    return {
        restaurants,
        pagination,
        loading,
        error,
        fetchRestaurants,
        refetch,
        hasMore: pagination?.has_next ?? false,
        loadMore,
        setSortBy,
        setRadius,
        currentParams
    }
} 