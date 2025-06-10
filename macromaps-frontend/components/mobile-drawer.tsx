"use client"

import type React from "react"
import { useEffect, useRef, useState } from "react"
import { useMobile } from "@/hooks/use-mobile"
import { Switch } from "@/components/ui/switch"

interface MobileDrawerProps {
  children: React.ReactNode
  title: string
  isOpen: boolean
  onToggle: (open: boolean) => void
  openLevel?: "partial" | "full"
  onExpandToFull?: () => void
  // Sorting props
  viewMode?: "restaurants" | "items"
  onViewModeChange?: (mode: "restaurants" | "items") => void
}

export default function MobileDrawer({
  children,
  title,
  isOpen,
  onToggle,
  openLevel = "full",
  onExpandToFull,
  viewMode = "restaurants",
  onViewModeChange,
}: MobileDrawerProps) {
  const isMobile = useMobile()
  const [isDragging, setIsDragging] = useState(false)
  const [startY, setStartY] = useState(0)
  const [currentY, setCurrentY] = useState(0)
  const [drawerHeight, setDrawerHeight] = useState(0)
  const drawerRef = useRef<HTMLDivElement>(null)
  const handleRef = useRef<HTMLDivElement>(null)
  const contentRef = useRef<HTMLDivElement>(null)
  const handleRestaurantSelect = (restaurant) => {} // Declare handleRestaurantSelect
  const handleMenuItemSelect = (menuItem) => {} // Declare handleMenuItemSelect

  const COLLAPSED_HEIGHT = 80 // Height when collapsed (showing just the handle bar)
  const SNAP_THRESHOLD = 100 // Pixels to drag before snapping

  // Invalidate map size when drawer state changes
  useEffect(() => {
    const invalidateMapSize = () => {
      // Small delay to ensure the drawer animation has started
      setTimeout(() => {
        const mapContainer = document.getElementById("map")
        if (mapContainer && (window as any).L) {
          // Find the Leaflet map instance and invalidate its size
          const maps = (window as any).L._mapInstances
          if (maps) {
            Object.values(maps).forEach((map: any) => {
              if (map && map.invalidateSize) {
                map.invalidateSize(false)
              }
            })
          }
        }
      }, 50)
    }

    invalidateMapSize()
  }, [isOpen, openLevel])

  // Prevent pull-to-refresh globally when drawer is visible
  useEffect(() => {
    if (!isMobile) return

    // Prevent overscroll behavior
    const originalBodyOverscrollBehavior = document.body.style.overscrollBehavior
    const originalHtmlOverscrollBehavior = document.documentElement.style.overscrollBehavior
    document.body.style.overscrollBehavior = "none"
    document.documentElement.style.overscrollBehavior = "none"

    return () => {
      document.body.style.overscrollBehavior = originalBodyOverscrollBehavior
      document.documentElement.style.overscrollBehavior = originalHtmlOverscrollBehavior
    }
  }, [isMobile])

  useEffect(() => {
    if (!isMobile) return

    const updateHeight = () => {
      if (drawerRef.current) {
        const windowHeight = window.innerHeight
        const headerHeight = 60 // Approximate header height
        const topMargin = 40 // Leave 40px from the top for visual balance
        // Set max height to almost full screen minus header and top margin
        const maxHeight = windowHeight - headerHeight - topMargin
        setDrawerHeight(maxHeight)
      }
    }

    updateHeight()
    window.addEventListener("resize", updateHeight)
    return () => window.removeEventListener("resize", updateHeight)
  }, [isMobile])

  const isInHandleArea = (target: EventTarget | null): boolean => {
    if (!handleRef.current || !target) return false
    return handleRef.current.contains(target as Node)
  }

  const handleTouchStart = (e: React.TouchEvent) => {
    // Only handle touches on the handle area for dragging
    if (!isInHandleArea(e.target)) return

    // Only prevent default on handle area
    e.preventDefault()
    setIsDragging(true)
    setStartY(e.touches[0].clientY)
    setCurrentY(e.touches[0].clientY)
  }

  const handleTouchMove = (e: React.TouchEvent) => {
    if (!isDragging) return

    // Only prevent default when actively dragging the handle
    e.preventDefault()
    setCurrentY(e.touches[0].clientY)
  }

  const handleTouchEnd = (e: React.TouchEvent) => {
    if (!isDragging) return

    e.preventDefault()
    setIsDragging(false)

    const deltaY = startY - currentY

    if (isOpen && openLevel === "partial" && deltaY > SNAP_THRESHOLD) {
      // If currently partial and dragging up, expand to full
      onExpandToFull?.()
    } else if (!isOpen && deltaY > SNAP_THRESHOLD) {
      // If closed and dragging up, open
      onToggle(true)
    } else if (isOpen && deltaY < -SNAP_THRESHOLD) {
      // If open and dragging down, close
      onToggle(false)
    }

    setCurrentY(0)
    setStartY(0)
  }

  const handleMouseDown = (e: React.MouseEvent) => {
    if (!isInHandleArea(e.target)) return

    e.preventDefault()
    setIsDragging(true)
    setStartY(e.clientY)
    setCurrentY(e.clientY)
  }

  const handleMouseMove = (e: MouseEvent) => {
    if (!isDragging) return
    e.preventDefault()
    setCurrentY(e.clientY)
  }

  const handleMouseUp = (e: MouseEvent) => {
    if (!isDragging) return
    e.preventDefault()
    setIsDragging(false)

    const deltaY = startY - currentY

    if (isOpen && openLevel === "partial" && deltaY > SNAP_THRESHOLD) {
      // If currently partial and dragging up, expand to full
      onExpandToFull?.()
    } else if (!isOpen && deltaY > SNAP_THRESHOLD) {
      // If closed and dragging up, open
      onToggle(true)
    } else if (isOpen && deltaY < -SNAP_THRESHOLD) {
      // If open and dragging down, close
      onToggle(false)
    }

    setCurrentY(0)
    setStartY(0)
  }

  useEffect(() => {
    if (isDragging) {
      document.addEventListener("mousemove", handleMouseMove, { passive: false })
      document.addEventListener("mouseup", handleMouseUp, { passive: false })
      return () => {
        document.removeEventListener("mousemove", handleMouseMove)
        document.removeEventListener("mouseup", handleMouseUp)
      }
    }
  }, [isDragging, isOpen, openLevel, onExpandToFull, onToggle])

  if (!isMobile) {
    return null
  }

  const dragOffset = isDragging ? startY - currentY : 0

  const getTargetHeight = () => {
    if (!isOpen) return COLLAPSED_HEIGHT
    if (openLevel === "partial") {
      // Show about half the screen
      return Math.min(drawerHeight * 0.5, drawerHeight)
    }
    return drawerHeight
  }

  const targetHeight = getTargetHeight()
  const currentHeight = Math.max(COLLAPSED_HEIGHT, Math.min(drawerHeight, targetHeight + dragOffset))

  return (
    <>
      {/* Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 transition-opacity duration-300"
          onClick={() => onToggle(false)}
        />
      )}

      {/* Drawer */}
      <div
        ref={drawerRef}
        className="fixed bottom-0 left-0 right-0 bg-slate-800 border-t border-slate-700 z-50 transition-all duration-300 ease-out rounded-t-xl shadow-2xl"
        style={{
          height: `${currentHeight}px`,
          transform: isDragging ? "none" : undefined,
        }}
      >
        {/* Handle bar */}
        <div
          ref={handleRef}
          className="flex flex-col items-center py-3 px-4 cursor-grab active:cursor-grabbing select-none"
          onTouchStart={handleTouchStart}
          onTouchMove={handleTouchMove}
          onTouchEnd={handleTouchEnd}
          onMouseDown={handleMouseDown}
          style={{
            touchAction: "none",
            userSelect: "none",
            WebkitUserSelect: "none",
          }}
        >
          {/* Drag handle */}
          <div className="w-12 h-1 bg-slate-600 rounded-full mb-2" />

          {/* Title */}
          <div className="text-white font-medium text-sm">{title}</div>

          {/* Subtitle when collapsed or partial */}
          {(!isOpen || openLevel === "partial") && (
            <div className="text-slate-400 text-xs mt-1">{!isOpen ? "Drag up to see more" : "Drag up to expand"}</div>
          )}
        </div>

        {/* View Mode Toggle - only show when drawer is open */}
        {isOpen && viewMode !== undefined && onViewModeChange && (
          <div className="px-4 pb-3 border-b border-slate-700">
            <div className="flex items-center justify-center gap-3">
              <span className={`text-sm ${viewMode === "restaurants" ? "text-white font-medium" : "text-slate-400"}`}>
                Restaurants
              </span>
              <Switch
                checked={viewMode === "items"}
                onCheckedChange={(checked) => onViewModeChange(checked ? "items" : "restaurants")}
                className="data-[state=checked]:bg-emerald-500"
              />
              <span className={`text-sm ${viewMode === "items" ? "text-white font-medium" : "text-slate-400"}`}>
                Items
              </span>
            </div>
          </div>
        )}

        {/* Content */}
        <div
          ref={contentRef}
          className="flex-1 overflow-hidden"
          style={{
            opacity: isOpen ? 1 : 0,
            transition: "opacity 0.3s ease-out",
            height: `${currentHeight - (isOpen && onViewModeChange ? 120 : 80)}px`, // Account for view toggle
          }}
        >
          <div
            className="h-full overflow-y-auto pb-safe"
            style={{
              WebkitOverflowScrolling: "touch",
              overscrollBehavior: "contain",
              touchAction: "pan-y",
            }}
          >
            {children}
          </div>
        </div>
      </div>
    </>
  )
}
