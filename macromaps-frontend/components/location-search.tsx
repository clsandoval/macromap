import { Search } from "lucide-react"
import { Input } from "@/components/ui/input"
import ProFeatureLock from "@/components/pro-feature-lock"

export default function LocationSearch() {
  return (
    <ProFeatureLock featureName="location search">
      <div className="relative">
        <Search className="absolute left-2.5 top-1/2 transform -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
        <Input
          type="text"
          placeholder="Search any location..."
          className="pl-8 bg-slate-800 border-slate-700 text-slate-400 text-xs h-8"
          disabled
        />
      </div>
    </ProFeatureLock>
  )
}
