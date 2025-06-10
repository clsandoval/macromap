"use client"
import { ExternalLink } from "lucide-react"
import type React from "react"

import { useEffect, useState, useRef } from "react"
import type { Restaurant } from "@/types/restaurant"

interface RestaurantListProps {
  restaurants: Restaurant[]
  isLoading: boolean
  selectedRestaurant: string | null
  onSelectRestaurant: (id: string) => void
  onLoadMore: () => void
  hasMore: boolean
}

export default function RestaurantList({
  restaurants,
  isLoading,
  selectedRestaurant,
  onSelectRestaurant,
  onLoadMore,
  hasMore,
}: RestaurantListProps) {
  const [loadingMore, setLoadingMore] = useState(false)
  const observerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !loadingMore && !isLoading) {
          setLoadingMore(true)
          onLoadMore()
          setTimeout(() => setLoadingMore(false), 1000) // Simulate loading delay
        }
      },
      { threshold: 0.1 },
    )

    if (observerRef.current) {
      observer.observe(observerRef.current)
    }

    return () => observer.disconnect()
  }, [hasMore, loadingMore, isLoading, onLoadMore])

  // Open restaurant in Google Maps
  const openInGoogleMaps = (restaurant: Restaurant, event: React.MouseEvent) => {
    event.stopPropagation() // Prevent triggering the restaurant selection
    const url = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(restaurant.name)}&center=${restaurant.location.lat},${restaurant.location.lng}`
    window.open(url, "_blank")
  }

  if (isLoading && restaurants.length === 0) {
    return (
      <div className="p-3">
        <div className="animate-pulse space-y-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="bg-slate-700 h-12 rounded-lg"></div>
          ))}
        </div>
      </div>
    )
  }

  if (restaurants.length === 0 && !isLoading) {
    return (
      <div className="p-6 text-center text-slate-400">
        <p className="text-sm">No restaurants found nearby.</p>
      </div>
    )
  }

  return (
    <div className="divide-y divide-slate-700">
      {restaurants.map((restaurant) => (
        <div
          key={restaurant.id}
          className={`p-4 cursor-pointer transition-colors duration-200 ${
            selectedRestaurant === restaurant.id ? "bg-slate-700" : "hover:bg-slate-750"
          }`}
          onClick={() => onSelectRestaurant(restaurant.id)}
        >
          <div className="flex justify-between items-center">
            <h3 className="font-medium text-white text-base leading-tight">{restaurant.name}</h3>
            <button
              onClick={(e) => openInGoogleMaps(restaurant, e)}
              className="p-2 text-slate-400 hover:text-blue-400 hover:bg-slate-600 rounded transition-colors duration-200"
              title="Open in Google Maps"
            >
              <ExternalLink className="h-4 w-4" />
            </button>
          </div>
        </div>
      ))}

      {/* Loading more indicator */}
      {loadingMore && (
        <div className="p-3">
          <div className="animate-pulse space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-slate-700 h-12 rounded-lg"></div>
            ))}
          </div>
        </div>
      )}

      {/* Intersection observer target */}
      <div ref={observerRef} className="h-4" />

      {/* End of list indicator */}
      {!hasMore && restaurants.length > 0 && (
        <div className="p-3 text-center text-slate-500 text-xs">
          <p>You've reached the end</p>
        </div>
      )}
    </div>
  )
}
