import { Button } from './components/ui/button';
import { Zap, Search } from "lucide-react"

export default function MacroMapPage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-slate-50 p-6 selection:bg-emerald-200 selection:text-emerald-900">
      <main className="w-full max-w-md text-center">
        <Zap className="mx-auto h-16 w-16 text-emerald-500 mb-6" strokeWidth={1.5} />
        <h1 className="text-5xl md:text-6xl font-bold text-slate-800 mb-4 tracking-tight">MacroMap</h1>
        <p className="text-lg text-slate-600 mb-10 leading-relaxed">
          Discover local restaurant meals tailored to your macros. <br />
          Tap to scan your area.
        </p>

        <div className="flex justify-center mb-6">
          <Button
            size="lg"
            className="h-14 bg-emerald-500 hover:bg-emerald-600 text-white font-semibold px-8 py-4 text-lg transition-colors duration-200 ease-in-out shadow-md hover:shadow-lg"
            aria-label="Scan nearby restaurants for menu items"
          >
            <Search className="mr-2.5 h-6 w-6" />
            Scan Nearby
          </Button>
        </div>

        {/* Removed the example search query text */}
      </main>

      <footer className="absolute bottom-6 text-center w-full">
        <p className="text-xs text-slate-400">&copy; {new Date().getFullYear()} MacroMap. Find your fit.</p>
      </footer>
    </div>
  )
}
