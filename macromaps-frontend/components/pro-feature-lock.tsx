import type React from "react"
import { LockIcon } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import Link from "next/link"

interface ProFeatureLockProps {
  children: React.ReactNode
  featureName: string
}

export default function ProFeatureLock({ children, featureName }: ProFeatureLockProps) {
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className="relative group">
            {children}
            <div className="absolute inset-0 bg-slate-900 bg-opacity-50 flex items-center justify-center rounded-md">
              <div className="flex items-center gap-1.5 text-xs font-medium text-white">
                <LockIcon className="h-3 w-3 text-emerald-400" />
                <span>Pro</span>
              </div>
            </div>
          </div>
        </TooltipTrigger>
        <TooltipContent side="bottom" className="bg-slate-800 border-slate-700 text-white text-xs">
          <div className="flex flex-col gap-2 p-1">
            <p>Upgrade to Pro to unlock {featureName}</p>
            <Link href="/upgrade">
              <Button size="sm" className="bg-emerald-500 hover:bg-emerald-600 text-white text-xs h-7">
                Upgrade to Pro
              </Button>
            </Link>
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}
