import { Button } from "@/components/ui/button"
import { AlertCircle } from "lucide-react"
import Link from "next/link"

export default function AuthCodeError() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-slate-900 p-6">
      <div className="w-full max-w-md text-center">
        <AlertCircle className="mx-auto h-16 w-16 text-red-500 mb-6" />
        <h1 className="text-2xl font-bold text-white mb-4">Authentication Error</h1>
        <p className="text-slate-300 mb-8">There was a problem signing you in. Please try again.</p>
        <Link href="/">
          <Button className="bg-emerald-500 hover:bg-emerald-600 text-white">Return Home</Button>
        </Link>
      </div>
    </div>
  )
}
