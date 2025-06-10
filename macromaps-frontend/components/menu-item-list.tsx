"use client"
import { MapPin, Dumbbell, Flame, Wheat, AlertCircle, Eye, EyeOff } from "lucide-react"
import { useEffect, useState, useRef, useMemo, useCallback } from "react"
import { Button } from "@/components/ui/button"
import type { MenuItem } from "@/types/menu-item"

interface MenuItemListProps {
  menuItems: MenuItem[]
  isLoading: boolean
  selectedRestaurant: string | null
  onSelectRestaurant: (id: string) => void
  onLoadMore: () => void
  hasMore: boolean
  onMenuItemSelect?: (menuItem: MenuItem) => void
  pageSize?: number
}

export default function MenuItemList({
  menuItems,
  isLoading,
  selectedRestaurant,
  onSelectRestaurant,
  onLoadMore,
  hasMore,
  onMenuItemSelect,
  pageSize = 20,
}: MenuItemListProps) {
  const [loadingMore, setLoadingMore] = useState(false)
  const [showItemsWithoutPrice, setShowItemsWithoutPrice] = useState(false)
  const [visibleItems, setVisibleItems] = useState<MenuItem[]>([])
  const [currentPage, setCurrentPage] = useState(1)
  const observerRef = useRef<HTMLDivElement>(null)

  // Memoize filtered items to prevent unnecessary recalculations
  const filteredMenuItems = useMemo(() => {
    return showItemsWithoutPrice ? menuItems : menuItems.filter((item) => item.price > 0)
  }, [menuItems, showItemsWithoutPrice])

  const hiddenItemsCount = useMemo(() => {
    return menuItems.length - filteredMenuItems.length
  }, [menuItems.length, filteredMenuItems.length])

  // Reset pagination when filtered items change (with proper dependencies)
  useEffect(() => {
    setCurrentPage(1)
    const initialItems = filteredMenuItems.slice(0, pageSize)
    setVisibleItems(initialItems)
    console.log(`Loaded initial batch of ${initialItems.length} items out of ${filteredMenuItems.length} total`)
  }, [filteredMenuItems.length, pageSize]) // Only depend on length to avoid infinite loops

  // Memoize the load more function to prevent recreating it on every render
  const handleLoadMore = useCallback(() => {
    if (loadingMore || isLoading) return

    setLoadingMore(true)

    setTimeout(() => {
      const nextPage = currentPage + 1
      const nextBatch = filteredMenuItems.slice(0, nextPage * pageSize)

      if (nextBatch.length > visibleItems.length) {
        console.log(`Loading more items: ${visibleItems.length} → ${nextBatch.length}`)
        setVisibleItems(nextBatch)
        setCurrentPage(nextPage)
      }

      setLoadingMore(false)
    }, 300)
  }, [currentPage, filteredMenuItems, isLoading, loadingMore, pageSize, visibleItems.length])

  // Handle intersection observer for infinite scrolling
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          handleLoadMore()
        }
      },
      { threshold: 0.1 },
    )

    if (observerRef.current) {
      observer.observe(observerRef.current)
    }

    return () => observer.disconnect()
  }, [handleLoadMore])

  if (isLoading && menuItems.length === 0) {
    return (
      <div className="p-3">
        <div className="animate-pulse space-y-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="bg-slate-700 h-32 rounded-lg"></div>
          ))}
        </div>
      </div>
    )
  }

  if (menuItems.length === 0 && !isLoading) {
    return (
      <div className="p-6 text-center text-slate-400">
        <p className="text-sm">No menu items found nearby.</p>
      </div>
    )
  }

  return (
    <div>
      {/* Price filter toggle */}
      {hiddenItemsCount > 0 && (
        <div className="p-3 border-b border-slate-700">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowItemsWithoutPrice(!showItemsWithoutPrice)}
            className="w-full text-slate-300 hover:text-white hover:bg-slate-700 text-xs h-7"
          >
            {showItemsWithoutPrice ? (
              <>
                <EyeOff className="h-3 w-3 mr-2" />
                Hide items without price ({hiddenItemsCount} hidden)
              </>
            ) : (
              <>
                <Eye className="h-3 w-3 mr-2" />
                Show items without price ({hiddenItemsCount} hidden)
              </>
            )}
          </Button>
        </div>
      )}

      {/* Display total count */}
      <div className="px-3 py-2 text-xs text-slate-400 border-b border-slate-700">
        Showing {visibleItems.length} of {filteredMenuItems.length} items
      </div>

      <div className="divide-y divide-slate-700">
        {visibleItems.map((item) => {
          const isIncomplete = item.price === 0 || !item.servingSize
          const canCalculateRatio = item.price > 0

          return (
            <div
              key={item.id}
              className={`p-3 cursor-pointer transition-colors duration-200 ${
                selectedRestaurant === item.restaurant.id ? "bg-slate-700" : "hover:bg-slate-750"
              } ${isIncomplete ? "opacity-60" : ""}`}
              onClick={() => {
                // Always select the restaurant first to ensure the map updates
                onSelectRestaurant(item.restaurant.id)

                // If we have a menu item select handler, use it for additional functionality
                if (onMenuItemSelect) {
                  onMenuItemSelect(item)
                }
              }}
            >
              <div className="flex justify-between items-start mb-1.5">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5">
                    <h3 className="font-medium text-white text-sm leading-tight truncate">{item.name}</h3>
                    {isIncomplete && (
                      <AlertCircle className="h-3 w-3 text-amber-400 flex-shrink-0" title="Incomplete data" />
                    )}
                  </div>
                  <p className="text-xs text-slate-400 truncate">{item.restaurant.name}</p>
                  {item.servingSize && <p className="text-xs text-slate-500">{item.servingSize}g</p>}
                </div>
                <div className="text-right flex-shrink-0 ml-2">
                  <div className={`font-medium text-sm ${item.price > 0 ? "text-emerald-400" : "text-slate-500"}`}>
                    {item.price > 0 ? `$${item.price}` : "N/A"}
                  </div>
                  <div className="flex items-center text-slate-400 text-xs">
                    <MapPin className="h-2.5 w-2.5 mr-0.5" />
                    {item.restaurant.distance} mi
                  </div>
                </div>
              </div>

              <div className="text-xs text-slate-300 mb-2 line-clamp-2">{item.description}</div>

              {/* Macro breakdown */}
              <div className="grid grid-cols-2 gap-1.5 text-xs mb-2">
                <div className="flex items-center text-emerald-400">
                  <Dumbbell className="h-3 w-3 mr-1" />
                  <span>{item.macros.protein}g protein</span>
                </div>

                <div className="flex items-center text-amber-400">
                  <Flame className="h-3 w-3 mr-1" />
                  <span>{item.macros.calories} cal</span>
                </div>

                <div className="flex items-center text-blue-400">
                  <Wheat className="h-3 w-3 mr-1" />
                  <span>{item.macros.carbs}g carbs</span>
                </div>

                <div className="flex items-center text-purple-400">
                  <div className="w-3 h-3 mr-1 flex items-center justify-center">
                    <div className="w-1.5 h-1.5 rounded-full bg-purple-400"></div>
                  </div>
                  <span>{item.macros.fat}g fat</span>
                </div>
              </div>

              <div className="flex items-center justify-between text-xs text-slate-400">
                <span className="bg-slate-700 text-slate-300 px-1.5 py-0.5 rounded-full text-xs">{item.category}</span>
              </div>
            </div>
          )
        })}

        {/* Loading more indicator */}
        {loadingMore && (
          <div className="p-3">
            <div className="animate-pulse space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="bg-slate-700 h-28 rounded-lg"></div>
              ))}
            </div>
          </div>
        )}

        {/* Intersection observer target */}
        <div ref={observerRef} className="h-4" />

        {/* End of list indicator */}
        {visibleItems.length >= filteredMenuItems.length && filteredMenuItems.length > 0 && (
          <div className="p-3 text-center text-slate-500 text-xs">
            <p>You've reached the end</p>
          </div>
        )}
      </div>
    </div>
  )
}
