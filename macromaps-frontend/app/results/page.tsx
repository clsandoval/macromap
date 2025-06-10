"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { ArrowLeft, Zap, AlertCircle, RefreshCw, WifiOff } from "lucide-react"
import Link from "next/link"
import dynamic from "next/dynamic"
import { useMobile } from "@/hooks/use-mobile"
import { useLocation } from "@/hooks/use-location"
import RestaurantList from "@/components/restaurant-list"
import MenuItemList from "@/components/menu-item-list"
import MobileDrawer from "@/components/mobile-drawer"
import AuthButton from "@/components/auth/auth-button"
import { scanNearby } from "@/lib/api"
import { transformApiResponse } from "@/lib/data-transformer"
import type { Restaurant } from "@/types/restaurant"
import type { MenuItem } from "@/types/menu-item"
import { Switch } from "@/components/ui/switch"

const MapComponent = dynamic(() => import("@/components/map-component"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full flex items-center justify-center bg-slate-800 rounded-lg">
      <div className="text-slate-400">Loading map...</div>
    </div>
  ),
})

export default function ResultsPage() {
  const [restaurants, setRestaurants] = useState<Restaurant[]>([])
  const [selectedRestaurant, setSelectedRestaurant] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const isMobile = useMobile()
  const [showList, setShowList] = useState(false)
  const [viewMode, setViewMode] = useState<"restaurants" | "items">("restaurants")
  const [menuItems, setMenuItems] = useState<MenuItem[]>([])
  const searchRadius = 1
  const [drawerOpenLevel, setDrawerOpenLevel] = useState<"partial" | "full">("full")
  const [isFiltered, setIsFiltered] = useState(false)
  const [apiStatus, setApiStatus] = useState<"connecting" | "connected" | "error">("connecting")
  const [retryCount, setRetryCount] = useState(0)
  const maxRetries = 3

  const {
    latitude,
    longitude,
    error: locationError,
    loading: locationLoading,
    refetch: refetchLocation,
  } = useLocation()

  useEffect(() => {
    const fetchData = async () => {
      console.log("[fetchData] Attempting to fetch data.")
      if (locationLoading) {
        console.log("[fetchData] Location is loading, aborting fetch.")
        return
      }
      if (!latitude || !longitude) {
        setError(locationError || "Location access is required.")
        setIsLoading(false)
        console.log("[fetchData] Latitude or longitude missing.", { latitude, longitude, locationError })
        return
      }
      try {
        setIsLoading(true)
        setError(null)
        setApiStatus("connecting")
        console.log("[fetchData] Calling scanNearby with:", { latitude, longitude, radius: searchRadius })
        const response = await scanNearby({ latitude, longitude, radius: searchRadius })
        console.log("[fetchData] scanNearby response received.")
        const { restaurants: transformedRestaurants, menuItems: transformedMenuItems } = transformApiResponse(response)
        console.log(
          `[fetchData] Data transformed. Restaurants: ${transformedRestaurants.length}, MenuItems: ${transformedMenuItems.length}`,
        )

        setRestaurants(transformedRestaurants)
        setMenuItems(transformedMenuItems)
        setApiStatus("connected")
        setIsLoading(false)
        setRetryCount(0)
        if (transformedRestaurants.length === 0) {
          setError("No restaurants found in your area.")
        }
      } catch (err: any) {
        console.error("[fetchData] Error:", err)
        setApiStatus("error")
        setError(err.message || "Failed to load restaurant data.")
        setIsLoading(false)
        // Retry logic can be added here if needed
      }
    }
    fetchData()
  }, [latitude, longitude, locationError, locationLoading, searchRadius, retryCount]) // Removed applySort and its deps

  useEffect(() => {
    if (!isMobile) setShowList(true)
    else setShowList(false)
  }, [isMobile])

  useEffect(() => {
    if (selectedRestaurant && window.mapComponent) {
      console.log(`[useEffect selectedRestaurant] Centering map on ${selectedRestaurant}`)
      window.mapComponent.centerOnRestaurant(selectedRestaurant)
    }
  }, [selectedRestaurant])

  const handleRestaurantSelect = (id: string) => {
    console.log(
      `[handleRestaurantSelect] Called with id: ${id}. Current viewMode: ${viewMode}, isFiltered: ${isFiltered}, selectedRestaurant: ${selectedRestaurant}`,
    )
    if (selectedRestaurant === id) {
      setSelectedRestaurant(null)
      setIsFiltered(false)
      setDrawerOpenLevel("full")
    } else {
      setSelectedRestaurant(id)
      setIsFiltered(true)
      if (isMobile) {
        setShowList(true)
        setDrawerOpenLevel("partial")
      }
      if (window.mapComponent) window.mapComponent.centerOnRestaurant(id)
    }
  }

  const handleMenuItemSelect = (menuItem: MenuItem) => {
    const restaurantId = menuItem.restaurant.id
    setSelectedRestaurant(restaurantId)
    setIsFiltered(true)
    if (isMobile) {
      setShowList(true)
      setDrawerOpenLevel("partial")
    }
    setTimeout(() => {
      if (window.mapComponent) window.mapComponent.centerOnRestaurant(restaurantId)
    }, 100)
  }

  const handleResetView = () => {
    setSelectedRestaurant(null)
    setIsFiltered(false)
  }

  const getDrawerTitle = () => {
    if (viewMode === "restaurants") return isFiltered ? "Restaurant Details" : "Nearby Restaurants"
    return isFiltered ? "Menu Items" : "All Menu Items"
  }

  const handleDrawerToggle = (open: boolean) => {
    setShowList(open)
    if (open && selectedRestaurant) setDrawerOpenLevel("partial")
    else if (open) setDrawerOpenLevel("full")
  }

  const handleDrawerExpand = () => setDrawerOpenLevel("full")
  const handleRetry = () => {
    if (locationError) refetchLocation()
    else {
      setRetryCount(0)
      setIsLoading(true)
      setError(null)
    }
  }

  const displayRestaurants =
    isFiltered && selectedRestaurant ? restaurants.filter((r) => r.id === selectedRestaurant) : restaurants

  let calculatedDisplayMenuItems: MenuItem[]
  if (isFiltered && selectedRestaurant) {
    const filteredForRestaurant = menuItems.filter((item) => item.restaurant.id === selectedRestaurant)
    console.log(
      `[ResultsPage] Filtering menu items for restaurant ${selectedRestaurant}. Found ${filteredForRestaurant.length} items. Total menu items in state: ${menuItems.length}`,
    )

    // If no items are found for the selected restaurant, log some diagnostic info
    if (menuItems.length > 0 && filteredForRestaurant.length === 0) {
      const allRestaurantIdsInMenuData = [...new Set(menuItems.map((mi) => mi.restaurant.id))]
      console.log(
        `[ResultsPage] No items found for ${selectedRestaurant}. Available restaurant IDs in menuItems state:`,
        allRestaurantIdsInMenuData,
      )
      if (!allRestaurantIdsInMenuData.includes(selectedRestaurant)) {
        console.warn(
          `[ResultsPage] The selected restaurant ID ${selectedRestaurant} does not appear in any menu item's restaurant.id field.`,
        )
      }
    }
    calculatedDisplayMenuItems = filteredForRestaurant
  } else {
    calculatedDisplayMenuItems = menuItems
    // console.log(`[ResultsPage] Not filtering. Displaying all ${menuItems.length} menu items.`); // Optional: uncomment if needed
  }
  const displayMenuItems = calculatedDisplayMenuItems

  if (error && !isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-slate-900 p-6">
        <div className="flex items-center mb-4">
          {apiStatus === "error" ? (
            <WifiOff className="h-16 w-16 text-red-500" />
          ) : (
            <AlertCircle className="h-16 w-16 text-red-500" />
          )}
        </div>
        <h1 className="text-2xl font-bold text-white mb-2">Unable to Load Data</h1>
        <p className="text-slate-300 text-center mb-6 max-w-md">{error}</p>
        <div className="flex gap-3">
          <Button onClick={handleRetry} className="bg-emerald-500 hover:bg-emerald-600">
            <RefreshCw className="h-4 w-4 mr-2" /> Try Again
          </Button>
          <Link href="/">
            <Button variant="outline" className="border-slate-600 text-slate-300">
              Go Home
            </Button>
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-screen bg-slate-900">
      <header className="sticky top-0 z-[60] flex flex-col gap-2 p-3 bg-slate-800 border-b border-slate-700 md:flex-row md:items-center md:justify-between md:gap-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <Link href="/">
              <Button variant="ghost" size="icon" className="mr-2 text-slate-300 hover:text-white h-8 w-8">
                <ArrowLeft className="h-4 w-4" />
              </Button>
            </Link>
            <h1 className="text-lg font-semibold text-white flex items-center">
              <Zap className="h-4 w-4 text-emerald-500 mr-2" />
              MacroMaps
            </h1>
            {isFiltered && (
              <span className="ml-2 text-xs bg-emerald-500 text-white px-2 py-0.5 rounded-full">Filtered</span>
            )}
            {/* API Status Indicator */}
          </div>
          <div className="md:hidden">
            <AuthButton />
          </div>
        </div>
        <div className="flex items-center justify-between gap-2 md:gap-3">
          {!isMobile && (
            <div className="flex items-center gap-1.5 text-xs">
              <span className={`text-slate-300 ${viewMode === "restaurants" ? "text-white font-medium" : ""}`}>
                Restaurants
              </span>
              <Switch
                checked={viewMode === "items"}
                onCheckedChange={(checked) => setViewMode(checked ? "items" : "restaurants")}
                className="data-[state=checked]:bg-emerald-500 scale-75"
              />
              <span className={`text-slate-300 ${viewMode === "items" ? "text-white font-medium" : ""}`}>Items</span>
            </div>
          )}
          <div className="hidden md:block">
            <AuthButton />
          </div>
        </div>
      </header>
      <div className="flex flex-1 overflow-hidden">
        {!isMobile && (
          <div className="w-80 bg-slate-800 border-r border-slate-700 overflow-y-auto">
            {viewMode === "restaurants" ? (
              <RestaurantList
                restaurants={displayRestaurants}
                isLoading={isLoading}
                selectedRestaurant={selectedRestaurant}
                onSelectRestaurant={handleRestaurantSelect}
                onLoadMore={() => {}}
                hasMore={false}
              />
            ) : (
              <MenuItemList
                menuItems={displayMenuItems}
                isLoading={isLoading}
                selectedRestaurant={selectedRestaurant}
                onSelectRestaurant={handleRestaurantSelect}
                onLoadMore={() => {}}
                hasMore={false}
                onMenuItemSelect={handleMenuItemSelect}
                pageSize={30}
              />
            )}
          </div>
        )}
        <div className="flex-1 relative">
          <MapComponent
            restaurants={restaurants}
            selectedRestaurant={selectedRestaurant}
            onSelectRestaurant={handleRestaurantSelect}
            onResetView={handleResetView}
            searchRadius={searchRadius}
            viewMode={viewMode}
            menuItems={menuItems}
          />
        </div>
        {isMobile && (
          <MobileDrawer
            title={getDrawerTitle()}
            isOpen={showList}
            onToggle={handleDrawerToggle}
            openLevel={drawerOpenLevel}
            onExpandToFull={handleDrawerExpand}
            viewMode={viewMode}
            onViewModeChange={setViewMode}
          >
            {viewMode === "restaurants" ? (
              <RestaurantList
                restaurants={displayRestaurants}
                isLoading={isLoading}
                selectedRestaurant={selectedRestaurant}
                onSelectRestaurant={handleRestaurantSelect}
                onLoadMore={() => {}}
                hasMore={false}
              />
            ) : (
              <MenuItemList
                menuItems={displayMenuItems}
                isLoading={isLoading}
                selectedRestaurant={selectedRestaurant}
                onSelectRestaurant={handleRestaurantSelect}
                onLoadMore={() => {}}
                hasMore={false}
                onMenuItemSelect={handleMenuItemSelect}
                pageSize={20}
              />
            )}
          </MobileDrawer>
        )}
      </div>
    </div>
  )
}
