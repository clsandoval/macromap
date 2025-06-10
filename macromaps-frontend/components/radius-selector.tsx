"use client"
import { Button } from "@/components/ui/button"
import { Ruler } from "lucide-react"
import ProFeatureLock from "@/components/pro-feature-lock"

interface RadiusSelectorProps {
  value: number
  onChange: (radius: number) => void
}

export default function RadiusSelector({ value, onChange }: RadiusSelectorProps) {
  const radiusOptions = [1, 2, 5, 10, 25]
  const freeLimit = 1

  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center gap-1.5 text-xs text-slate-400">
        <Ruler className="h-3 w-3" />
        <span>Search radius</span>
      </div>
      <div className="flex gap-1">
        {radiusOptions.map((radius) => {
          const isProFeature = radius > freeLimit
          const isActive = value === radius

          if (isProFeature) {
            return (
              <ProFeatureLock key={radius} featureName={`${radius}km radius`}>
                <Button
                  size="sm"
                  variant="outline"
                  className={`text-xs h-7 px-2 border-slate-700 ${
                    isActive ? "bg-slate-700 text-white" : "bg-slate-800 text-slate-400"
                  }`}
                  disabled
                >
                  {radius} km
                </Button>
              </ProFeatureLock>
            )
          }

          return (
            <Button
              key={radius}
              size="sm"
              variant="outline"
              className={`text-xs h-7 px-2 border-slate-700 ${
                isActive
                  ? "bg-emerald-500 hover:bg-emerald-600 text-white border-emerald-500"
                  : "bg-slate-800 text-slate-300 hover:bg-slate-700"
              }`}
              onClick={() => onChange(radius)}
            >
              {radius} km
            </Button>
          )
        })}
      </div>
    </div>
  )
}
