"use client"

import { useEffect, useRef, useState } from "react"
import L from "leaflet"
import "leaflet/dist/leaflet.css"
import type { Restaurant } from "@/types/restaurant"

interface MapComponentProps {
  restaurants: Restaurant[]
  selectedRestaurant: string | null
  onSelectRestaurant: (id: string) => void
  onResetView: () => void
  searchRadius?: number
  viewMode?: "restaurants" | "items"
  menuItems?: any[]
}

export default function MapComponent({
  restaurants,
  selectedRestaurant,
  onSelectRestaurant,
  onResetView,
  searchRadius = 1,
  viewMode = "restaurants",
  menuItems = [],
}: MapComponentProps) {
  const mapRef = useRef<L.Map | null>(null)
  const markersRef = useRef<{ [key: string]: L.Marker }>({})
  const userMarkerRef = useRef<L.Marker | null>(null)
  const radiusCircleRef = useRef<L.Circle | null>(null)
  const [userLocation, setUserLocation] = useState<[number, number] | null>(null)
  const [locationError, setLocationError] = useState<string | null>(null)
  const [mapInitialized, setMapInitialized] = useState(false)

  // Add centerOnRestaurant function
  const centerOnRestaurant = (restaurantId: string) => {
    if (!mapRef.current || !mapInitialized) return

    const restaurant = restaurants.find((r) => r.id === restaurantId)
    if (!restaurant) return

    try {
      // Center map on restaurant
      mapRef.current.setView([restaurant.location.lat, restaurant.location.lng], 16, {
        animate: true,
        duration: 0.5,
      })

      // Open popup for the restaurant marker
      const marker = markersRef.current[restaurantId]
      if (marker) {
        // Small delay to ensure map has centered
        setTimeout(() => {
          marker.openPopup()
        }, 300)
      }
    } catch (error) {
      console.error("Error centering on restaurant:", error)
    }
  }

  // Expose centerOnRestaurant globally for other components to use
  useEffect(() => {
    if (mapInitialized && mapRef.current) {
      // Make sure to properly expose the function with the current restaurants data
      window.mapComponent = {
        centerOnRestaurant: (restaurantId: string) => {
          console.log("Centering on restaurant:", restaurantId)
          const restaurant = restaurants.find((r) => r.id === restaurantId)
          if (!restaurant || !mapRef.current) return

          // Center map on restaurant
          mapRef.current.setView([restaurant.location.lat, restaurant.location.lng], 16, {
            animate: true,
            duration: 0.5,
          })

          // Open popup for the restaurant marker
          const marker = markersRef.current[restaurantId]
          if (marker) {
            // Small delay to ensure map has centered
            setTimeout(() => {
              marker.openPopup()
            }, 300)
          }
        },
      }

      console.log("Map component functions exposed:", window.mapComponent)
    }

    return () => {
      if (window.mapComponent) {
        delete window.mapComponent
      }
    }
  }, [mapInitialized, restaurants])

  // Get user's location
  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude } = position.coords
          setUserLocation([latitude, longitude])
        },
        (error) => {
          console.error("Error getting location:", error)
          setLocationError("Could not access your location")
        },
        { enableHighAccuracy: true },
      )
    } else {
      setLocationError("Geolocation is not supported by your browser")
    }
  }, [])

  // Reset view to user location and deselect restaurant
  const resetMapView = () => {
    if (mapRef.current && userLocation && mapInitialized) {
      try {
        mapRef.current.setView(userLocation, 15)
        onResetView()
      } catch (error) {
        console.error("Error resetting map view:", error)
      }
    }
  }

  // Get menu item count for a restaurant
  const getMenuItemCount = (restaurantId: string) => {
    return menuItems.filter((item) => item.restaurant.id === restaurantId).length
  }

  // Initialize map
  useEffect(() => {
    if (mapRef.current || !restaurants.length) return

    try {
      // Default to first restaurant location or NYC
      const defaultLocation: [number, number] =
        userLocation ||
        (restaurants.length > 0 ? [restaurants[0].location.lat, restaurants[0].location.lng] : [40.7128, -74.006])

      // Create map
      const map = L.map("map", {
        center: defaultLocation,
        zoom: 15,
        zoomControl: true,
        attributionControl: true,
      })

      mapRef.current = map

      // Store map instance globally for drawer to access
      if (!(window as any).L._mapInstances) {
        ;(window as any).L._mapInstances = {}
      }
      ;(window as any).L._mapInstances["main"] = map

      // Add dark theme map tiles
      L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
        attribution:
          '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        maxZoom: 19,
      }).addTo(map)

      // Add reset view button
      const resetButton = L.control({ position: "bottomright" })
      resetButton.onAdd = () => {
        const div = L.DomUtil.create("div", "reset-button")
        div.innerHTML = `
          <button class="reset-view-button" title="Reset view">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/>
              <path d="M21 3v5h-5"/>
              <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/>
              <path d="M3 21v-5h5"/>
            </svg>
          </button>
        `
        div.onclick = (e) => {
          e.preventDefault()
          e.stopPropagation()
          resetMapView()
          return false
        }
        return div
      }
      resetButton.addTo(map)

      // Wait for map to be ready
      map.whenReady(() => {
        setMapInitialized(true)
      })
    } catch (error) {
      console.error("Error initializing map:", error)
    }

    // Cleanup function
    return () => {
      if (mapRef.current) {
        try {
          // Clean up global reference
          if ((window as any).L._mapInstances) {
            delete (window as any).L._mapInstances["main"]
          }

          // Clear all markers
          Object.values(markersRef.current).forEach((marker) => {
            if (marker) {
              marker.remove()
            }
          })
          markersRef.current = {}

          // Remove user marker
          if (userMarkerRef.current) {
            userMarkerRef.current.remove()
            userMarkerRef.current = null
          }

          // Remove radius circle
          if (radiusCircleRef.current) {
            radiusCircleRef.current.remove()
            radiusCircleRef.current = null
          }

          mapRef.current.remove()
          mapRef.current = null
          setMapInitialized(false)
        } catch (error) {
          console.error("Error cleaning up map:", error)
        }
      }
    }
  }, [restaurants.length > 0]) // Only depend on whether we have restaurants

  // Add/update restaurant markers
  useEffect(() => {
    if (!mapRef.current || !mapInitialized || !restaurants.length) return

    try {
      // Clear existing markers
      Object.values(markersRef.current).forEach((marker) => {
        if (marker) {
          marker.remove()
        }
      })
      markersRef.current = {}

      // Create markers for each restaurant
      restaurants.forEach((restaurant) => {
        const isSelected = restaurant.id === selectedRestaurant
        const iconHtml = `
          <div class="map-pin ${isSelected ? "selected-blue" : ""}">
            <div class="pin-body ${isSelected ? "selected-blue" : ""}">
              <div class="pin-center ${isSelected ? "selected-blue" : ""}"></div>
            </div>
            <div class="pin-tip ${isSelected ? "selected-blue" : ""}"></div>
          </div>
        `

        const icon = L.divIcon({
          className: isSelected ? "selected-pin-marker" : "custom-pin-marker",
          html: iconHtml,
          iconSize: isSelected ? [28, 38] : [24, 32], // Slightly larger when selected
          iconAnchor: isSelected ? [14, 38] : [12, 32], // Anchor at the tip
          popupAnchor: isSelected ? [0, -38] : [0, -32], // Popup above the tip
        })

        const marker = L.marker([restaurant.location.lat, restaurant.location.lng], {
          icon: icon,
        }).addTo(mapRef.current!)

        marker.on("click", () => {
          onSelectRestaurant(restaurant.id)
        })

        // Add popup with restaurant info and Google Maps button
        const getPopupContent = (restaurant: Restaurant) => {
          const reviewCount = Math.floor(Math.random() * 500) + 50
          return `
            <div class="text-slate-800 min-w-[200px] max-w-[250px]">
              <div class="mb-3">
                <div class="font-semibold text-lg text-slate-900 leading-tight mb-2">${restaurant.name}</div>
                
                <div class="flex items-center justify-between mb-2">
                  <div class="flex items-center text-amber-600">
                    <svg class="w-4 h-4 fill-current mr-1" viewBox="0 0 20 20">
                      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-.118L2.98 8.72c-.783-.57-.38-1.81.588-.181h3.461a1 1 0 00.951-.69l1.07-3.292z"/>
                    </svg>
                    <span class="text-sm font-medium">${restaurant.rating}</span>
                  </div>
                  <div class="text-slate-600 text-sm">
                    ${reviewCount} reviews
                  </div>
                </div>

                <div class="flex items-center text-slate-600 text-sm mb-3">
                  <svg class="w-4 h-4 mr-1 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/>
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/>
                  </svg>
                  <span>${restaurant.distance} mi away</span>
                </div>
              </div>
                
              <button 
                onclick="window.open('https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(restaurant.name)}&center=${restaurant.location.lat},${restaurant.location.lng}', '_blank')"
                class="w-full bg-slate-800 hover:bg-slate-700 text-white text-sm font-medium py-2.5 px-4 rounded-md transition-colors duration-200 flex items-center justify-center gap-2"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/>
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/>
                </svg>
                Open in Google Maps
              </button>
            </div>
          `
        }

        // Bind popup to marker
        marker.bindPopup(getPopupContent(restaurant), {
          autoPanPadding: L.point(50, 50), // Ensures more padding when auto-panning
        })

        // Open popup if this restaurant is selected
        if (isSelected) {
          marker.openPopup()
        }

        markersRef.current[restaurant.id] = marker

        // Update marker click handler to also trigger list filtering
        marker.on("click", () => {
          onSelectRestaurant(restaurant.id)
        })
      })
    } catch (error) {
      console.error("Error adding markers:", error)
    }
  }, [restaurants, selectedRestaurant, mapInitialized, onSelectRestaurant]) // Added onSelectRestaurant to dep array

  // Update marker icons when selection changes (This effect might be redundant if the above effect handles it)
  // Let's keep it for now to ensure icon updates are robust.
  useEffect(() => {
    if (!mapRef.current || !mapInitialized) return

    // Update marker icons based on selection
    Object.entries(markersRef.current).forEach(([id, marker]) => {
      const isSelected = id === selectedRestaurant

      const iconHtml = `
        <div class="map-pin ${isSelected ? "selected-blue" : ""}">
          <div class="pin-body ${isSelected ? "selected-blue" : ""}">
            <div class="pin-center ${isSelected ? "selected-blue" : ""}"></div>
          </div>
          <div class="pin-tip ${isSelected ? "selected-blue" : ""}"></div>
        </div>
      `
      const icon = L.divIcon({
        className: isSelected ? "selected-pin-marker" : "custom-pin-marker",
        html: iconHtml,
        iconSize: isSelected ? [28, 38] : [24, 32],
        iconAnchor: isSelected ? [14, 38] : [12, 32],
        popupAnchor: isSelected ? [0, -38] : [0, -32],
      })

      marker.setIcon(icon)

      // Open popup if this restaurant is selected and not already open
      if (isSelected && !marker.isPopupOpen()) {
        marker.openPopup()
      }
    })
  }, [selectedRestaurant, mapInitialized])

  // Add user location marker
  useEffect(() => {
    if (!mapRef.current || !mapInitialized || !userLocation) return

    try {
      // Remove existing user marker if it exists
      if (userMarkerRef.current) {
        userMarkerRef.current.remove()
      }

      // Create user location marker with pulsing effect
      const userIcon = L.divIcon({
        className: "user-marker",
        html: `
          <div class="user-marker-outer"></div>
          <div class="user-marker-inner"></div>
        `,
        iconSize: [24, 24],
        iconAnchor: [12, 12],
      })

      userMarkerRef.current = L.marker(userLocation, { icon: userIcon }).addTo(mapRef.current)
      userMarkerRef.current.bindPopup("You are here")

      // Only center map on user location if no restaurant is selected and this is the first time
      if (!selectedRestaurant && restaurants.length > 0) {
        mapRef.current.setView(userLocation, 15)
      }
    } catch (error) {
      console.error("Error adding user marker:", error)
    }
  }, [userLocation, mapInitialized])

  return (
    <>
      <div id="map" className="w-full h-full z-0"></div>
      {locationError && (
        <div className="absolute bottom-4 left-4 right-4 bg-slate-800 border border-slate-700 rounded-md p-3 text-sm text-slate-300 shadow-lg">
          <p>{locationError}</p>
          <button
            className="mt-2 text-xs text-emerald-400 hover:text-emerald-300"
            onClick={() => setLocationError(null)}
          >
            Dismiss
          </button>
        </div>
      )}
      <style jsx global>{`
        /* Classic map pin shape */
        .map-pin {
          position: relative;
          display: flex;
          flex-direction: column;
          align-items: center;
          filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
        }

        .pin-body {
          width: 20px;
          height: 20px;
          background: #10b981; /* Default: Emerald 500 */
          border: 2px solid #ffffff;
          border-radius: 50% 50% 50% 0;
          transform: rotate(-45deg);
          display: flex;
          align-items: center;
          justify-content: center;
          position: relative;
          z-index: 2;
        }
        
        .pin-body.selected-blue {
          width: 24px; /* Slightly larger when selected */
          height: 24px;
          background: #3b82f6; /* Selected: Blue 500 */
          border: 3px solid #ffffff;
        }

        .pin-center {
          width: 6px;
          height: 6px;
          background: #ffffff;
          border-radius: 50%;
          transform: rotate(45deg);
        }
        
        .pin-center.selected-blue {
          width: 8px; /* Slightly larger when selected */
          height: 8px;
        }

        .pin-tip {
          width: 0;
          height: 0;
          border-left: 4px solid transparent;
          border-right: 4px solid transparent;
          border-top: 8px solid #10b981; /* Default: Emerald 500 */
          margin-top: -2px;
          position: relative;
          z-index: 1;
        }

        .pin-tip.selected-blue {
          border-left: 5px solid transparent; /* Slightly larger when selected */
          border-right: 5px solid transparent;
          border-top: 10px solid #3b82f6; /* Selected: Blue 500 */
          margin-top: -3px;
        }
        
        .map-pin.selected-blue {
          filter: drop-shadow(0 3px 6px rgba(0, 0, 0, 0.4));
        }

        /* Remove old marker styles */
        .custom-pin-marker, .selected-pin-marker {
          display: flex;
          align-items: center;
          justify-content: center;
        }
        
        /* Popup styles */
        .leaflet-popup-content-wrapper {
          border-radius: 12px;
          padding: 0;
          box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
          border: 1px solid rgba(0, 0, 0, 0.08);
          background: white;
        }
        .leaflet-popup-content {
          margin: 16px;
          min-width: 200px;
          max-width: 250px;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
          line-height: 1.4;
        }
        .leaflet-popup-tip {
          background: white;
          border: 1px solid rgba(0, 0, 0, 0.08);
        }
        
        /* User location marker styles */
        .user-marker {
          position: relative;
        }
        .user-marker-outer {
          position: absolute;
          width: 24px;
          height: 24px;
          border-radius: 50%;
          background-color: rgba(59, 130, 246, 0.3);
          animation: pulse 2s infinite;
        }
        .user-marker-inner {
          position: absolute;
          top: 6px;
          left: 6px;
          width: 12px;
          height: 12px;
          border-radius: 50%;
          background-color: #3b82f6;
          border: 2px solid white;
          box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.5);
        }
        
        /* Reset button styles */
        .reset-view-button {
          width: 40px;
          height: 40px;
          background-color: white;
          border: none;
          border-radius: 6px;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #374151;
          transition: all 0.2s;
        }
        .reset-view-button:hover {
          background-color: #f9fafb;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }
        .reset-button {
          margin-bottom: 10px;
          margin-right: 10px;
        }
        
        @keyframes pulse {
          0% {
            transform: scale(0.8);
            opacity: 0.8;
          }
          70% {
            transform: scale(1.5);
            opacity: 0;
          }
          100% {
            transform: scale(0.8);
            opacity: 0;
          }
        }
      `}</style>
    </>
  )
}
