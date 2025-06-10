"use client"

import { Button } from "@/components/ui/button"
import { Zap, Search, Settings } from "lucide-react"
import Link from "next/link"
import AuthButton from "@/components/auth/auth-button"
import { useAuth } from "@/components/auth/auth-provider"
import { useEffect } from "react"

export default function MacroMapPage() {
  const { user, loading } = useAuth()

  // Debug auth state
  useEffect(() => {
    console.log("Auth state:", { user: user?.email, loading })
  }, [user, loading])

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-slate-900 p-6 selection:bg-emerald-500 selection:text-white">
      {/* Auth button in top right */}
      <div className="absolute top-6 right-6">
        <AuthButton />
      </div>

      <main className="w-full max-w-md text-center">
        <Zap className="mx-auto h-16 w-16 text-emerald-500 mb-6" strokeWidth={1.5} />
        <h1 className="text-5xl md:text-6xl font-bold text-white mb-4 tracking-tight">MacroMaps</h1>
        <p className="text-lg text-slate-300 mb-10 leading-relaxed">
          Discover local restaurant meals tailored to your macros. <br />
          Tap to scan your area.
        </p>

        {/* Show welcome message if user is signed in */}
        {user && (
          <div className="mb-6 p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-lg">
            <p className="text-emerald-400 text-sm">Welcome back, {user.user_metadata?.full_name || user.email}! 👋</p>
          </div>
        )}

        <div className="flex flex-col items-center gap-4 mb-6">
          <Link href="/results">
            <Button
              size="lg"
              className="h-14 bg-emerald-500 hover:bg-emerald-600 text-white font-semibold px-8 py-4 text-lg transition-colors duration-200 ease-in-out shadow-md hover:shadow-lg"
              aria-label="Scan nearby restaurants for menu items"
            >
              <Search className="mr-2.5 h-6 w-6" />
              Scan Nearby
            </Button>
          </Link>

          <Button
            variant="outline"
            size="sm"
            className="bg-slate-800 border-slate-700 text-slate-300 hover:bg-slate-700 hover:text-white transition-colors duration-200 px-4 py-2"
            onClick={() => {
              const modal = document.getElementById("search-settings-modal")
              if (modal) modal.classList.remove("hidden")
            }}
          >
            <Settings className="mr-2 h-4 w-4" />
            Search Settings
          </Button>
        </div>
      </main>

      {/* Search Settings Modal */}
      <div
        id="search-settings-modal"
        className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4 hidden"
        onClick={(e) => {
          if (e.target === e.currentTarget) {
            e.currentTarget.classList.add("hidden")
          }
        }}
      >
        <div className="bg-slate-800 rounded-lg border border-slate-700 p-6 w-full max-w-md">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-white">Search Settings</h2>
            <Button
              variant="ghost"
              size="sm"
              className="text-slate-400 hover:text-white"
              onClick={() => {
                const modal = document.getElementById("search-settings-modal")
                if (modal) modal.classList.add("hidden")
              }}
            >
              ✕
            </Button>
          </div>

          <div className="space-y-6">
            {/* Location Search */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Location</label>
              <div className="relative">
                <input
                  type="text"
                  placeholder="Use current location"
                  className="w-full bg-slate-700 border border-slate-600 rounded-md px-3 py-2 text-slate-400 text-sm"
                  disabled
                />
                <div className="absolute inset-0 bg-slate-900 bg-opacity-50 flex items-center justify-center rounded-md">
                  <div className="flex items-center gap-1.5 text-xs font-medium text-white">
                    <Zap className="h-3 w-3 text-emerald-400" />
                    <span>Pro</span>
                  </div>
                </div>
              </div>
              <p className="text-xs text-slate-500 mt-1">Search any location with Pro</p>
            </div>

            {/* Radius Selector */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Search Radius</label>
              <div className="grid grid-cols-5 gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  className="bg-emerald-500 hover:bg-emerald-600 text-white border-emerald-500 text-xs"
                >
                  1 km
                </Button>
                {[2, 5, 10, 25].map((radius) => (
                  <div key={radius} className="relative">
                    <Button
                      size="sm"
                      variant="outline"
                      className="w-full bg-slate-700 text-slate-400 border-slate-600 text-xs"
                      disabled
                    >
                      {radius} km
                    </Button>
                    <div className="absolute inset-0 bg-slate-900 bg-opacity-50 flex items-center justify-center rounded-md">
                      <Zap className="h-2.5 w-2.5 text-emerald-400" />
                    </div>
                  </div>
                ))}
              </div>
              <p className="text-xs text-slate-500 mt-1">Expand your search radius with Pro</p>
            </div>

            {/* Pro Upgrade CTA */}
            <div className="bg-gradient-to-r from-emerald-500/10 to-emerald-600/10 border border-emerald-500/20 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <Zap className="h-4 w-4 text-emerald-400" />
                <span className="text-sm font-medium text-white">Upgrade to Pro</span>
              </div>
              <p className="text-xs text-slate-400 mb-3">
                Unlock custom locations, extended radius, and advanced filters
              </p>
              <Link href="/upgrade">
                <Button size="sm" className="w-full bg-emerald-500 hover:bg-emerald-600 text-white">
                  Start Free Trial
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </div>

      <footer className="absolute bottom-6 text-center w-full">
        <p className="text-xs text-slate-500">&copy; {new Date().getFullYear()} MacroMaps. Find your fit.</p>
      </footer>
    </div>
  )
}
