"use client"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ArrowLeft, Check, Zap, MapPin, Ruler, Camera, Filter, BarChart3, Users, Shield, Sparkles } from "lucide-react"
import Link from "next/link"
import AuthButton from "@/components/auth/auth-button"

export default function UpgradePage() {
  // Prices in Philippine Pesos
  const monthlyPrice = 99
  const yearlyPrice = 999
  const savings = monthlyPrice * 12 - yearlyPrice

  // Format currency as PHP
  const formatPHP = (amount: number) => {
    return new Intl.NumberFormat("en-PH", {
      style: "currency",
      currency: "PHP",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount)
  }

  const features = [
    {
      icon: MapPin,
      title: "Scan Anywhere",
      description: "Search any location worldwide, not just your current area",
      free: false,
    },
    {
      icon: Ruler,
      title: "Extended Radius",
      description: "Search up to 25km radius instead of just 1km",
      free: false,
    },
    {
      icon: Camera,
      title: "Food Photos",
      description: "See high-quality photos of every menu item",
      free: false,
    },
    {
      icon: Filter,
      title: "Advanced Filters",
      description: "Filter by dietary restrictions, allergens, and more",
      free: false,
    },
    {
      icon: BarChart3,
      title: "Detailed Analytics",
      description: "Track your macro intake and dining patterns over time",
      free: false,
    },
    {
      icon: Users,
      title: "Team Features",
      description: "Share lists and coordinate meals with friends",
      free: false,
    },
    {
      icon: Shield,
      title: "Ad-free Experience",
      description: "Enjoy MacroMaps without any advertisements",
      free: false,
    },
  ]

  const freeFeatures = [
    "Search within 1km of current location",
    "Basic restaurant and menu item listings",
    "Standard macro information",
    "Distance-based sorting",
  ]

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Header */}
      <header className="sticky top-0 z-50 flex items-center justify-between p-4 bg-slate-800 border-b border-slate-700">
        <div className="flex items-center">
          <Link href="/results">
            <Button variant="ghost" size="icon" className="mr-3 text-slate-300 hover:text-white h-8 w-8">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <h1 className="text-lg font-semibold text-white flex items-center">
            <Zap className="h-4 w-4 text-emerald-500 mr-2" />
            MacroMaps Pro
          </h1>
        </div>
        <AuthButton />
      </header>

      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/20 rounded-full px-4 py-2 mb-6">
            <Sparkles className="h-4 w-4 text-emerald-400" />
            <span className="text-emerald-400 text-sm font-medium">Unlock Premium Features</span>
          </div>
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">
            Supercharge Your
            <br />
            <span className="text-emerald-400">Macro Tracking</span>
          </h1>
          <p className="text-xl text-slate-300 mb-8 max-w-2xl mx-auto">
            Get unlimited access to advanced features that help you find the perfect meals anywhere in the world.
          </p>
        </div>

        {/* Pricing Cards */}
        <div className="grid md:grid-cols-3 gap-6 mb-16 max-w-5xl mx-auto">
          {/* Free Plan */}
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader className="text-center pb-4">
              <CardTitle className="text-slate-300 text-lg">Free</CardTitle>
              <div className="text-3xl font-bold text-white">{formatPHP(0)}</div>
              <p className="text-slate-400 text-sm">Perfect for getting started</p>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                {freeFeatures.map((feature, index) => (
                  <div key={index} className="flex items-start gap-3">
                    <Check className="h-4 w-4 text-slate-400 mt-0.5 flex-shrink-0" />
                    <span className="text-slate-300 text-sm">{feature}</span>
                  </div>
                ))}
              </div>
              <Button variant="outline" className="w-full bg-slate-700 border-slate-600 text-slate-300" disabled>
                Current Plan
              </Button>
            </CardContent>
          </Card>

          {/* Monthly Pro Plan */}
          <Card className="bg-slate-800 border-emerald-500/50 relative ring-2 ring-emerald-500/20">
            <CardHeader className="text-center pb-4">
              <CardTitle className="text-white text-lg">Pro Monthly</CardTitle>
              <div className="text-3xl font-bold text-white">
                {formatPHP(monthlyPrice)}
                <span className="text-lg text-slate-300 font-normal">/month</span>
              </div>
              <p className="text-slate-300 text-sm">Billed monthly</p>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <div className="text-slate-300 text-xs font-medium uppercase tracking-wide mb-2">
                  Everything in Free, plus:
                </div>
                {features.map((feature, index) => (
                  <div key={index} className="flex items-start gap-3">
                    <Check className="h-4 w-4 text-emerald-400 mt-0.5 flex-shrink-0" />
                    <div>
                      <div className="text-white text-sm font-medium">{feature.title}</div>
                      <div className="text-slate-300 text-xs">{feature.description}</div>
                    </div>
                  </div>
                ))}
              </div>
              <Button className="w-full bg-emerald-500 hover:bg-emerald-600 text-white font-medium">
                Start Free Trial
              </Button>
              <p className="text-center text-xs text-slate-300">7-day free trial • Cancel anytime</p>
            </CardContent>
          </Card>

          {/* Annual Pro Plan */}
          <Card className="bg-slate-800 border-emerald-500/50 relative ring-2 ring-emerald-500/20">
            <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
              <div className="bg-emerald-500 text-white text-xs font-medium px-3 py-1 rounded-full">Best Value</div>
            </div>
            <CardHeader className="text-center pb-4">
              <CardTitle className="text-white text-lg">Pro Annual</CardTitle>
              <div className="text-3xl font-bold text-white">
                {formatPHP(yearlyPrice)}
                <span className="text-lg text-slate-300 font-normal">/year</span>
              </div>
              <p className="text-emerald-400 text-sm">Save {formatPHP(savings)} per year</p>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <div className="text-slate-300 text-xs font-medium uppercase tracking-wide mb-2">
                  Everything in Free, plus:
                </div>
                {features.map((feature, index) => (
                  <div key={index} className="flex items-start gap-3">
                    <Check className="h-4 w-4 text-emerald-400 mt-0.5 flex-shrink-0" />
                    <div>
                      <div className="text-white text-sm font-medium">{feature.title}</div>
                      <div className="text-slate-300 text-xs">{feature.description}</div>
                    </div>
                  </div>
                ))}
              </div>
              <Button className="w-full bg-emerald-500 hover:bg-emerald-600 text-white font-medium">
                Start Free Trial
              </Button>
              <p className="text-center text-xs text-slate-300">7-day free trial • Cancel anytime</p>
            </CardContent>
          </Card>
        </div>

        {/* Feature Showcase */}
        <div className="mb-16">
          <h2 className="text-3xl font-bold text-white text-center mb-12">
            Powerful Features for Serious Macro Tracking
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            {features.slice(0, 6).map((feature, index) => (
              <div key={index} className="text-center">
                <div className="w-16 h-16 bg-emerald-500/10 border border-emerald-500/20 rounded-2xl flex items-center justify-center mx-auto mb-4">
                  <feature.icon className="h-8 w-8 text-emerald-400" />
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">{feature.title}</h3>
                <p className="text-slate-400 text-sm">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Disclaimer */}
        <div className="mb-16 max-w-3xl mx-auto">
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-white mb-2">About Our Macro Data</h3>
            <p className="text-slate-400 text-sm">
              MacroMaps uses AI to approximate nutritional information when exact data isn't available from restaurants.
              While we strive for accuracy, please note that these values are estimates and may not be 100% accurate in
              all cases. For precise nutritional information, we recommend consulting the restaurant directly.
            </p>
          </div>
        </div>

        {/* FAQ Section */}
        <div className="mb-16">
          <h2 className="text-3xl font-bold text-white text-center mb-12">Frequently Asked Questions</h2>
          <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            <div>
              <h3 className="text-lg font-semibold text-white mb-2">Can I cancel anytime?</h3>
              <p className="text-slate-400 text-sm">
                Yes! You can cancel your subscription at any time. You'll continue to have access to Pro features until
                the end of your billing period.
              </p>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white mb-2">What's included in the free trial?</h3>
              <p className="text-slate-400 text-sm">
                You get full access to all Pro features for 7 days. No credit card required to start your trial.
              </p>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white mb-2">How accurate is the macro information?</h3>
              <p className="text-slate-400 text-sm">
                We use AI to approximate nutritional values when exact data isn't available. These are estimates and may
                vary from actual values. For precise information, please check with the restaurant directly.
              </p>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white mb-2">How is my data used?</h3>
              <p className="text-slate-400 text-sm">
                We only use your data to provide and improve the MacroMaps service. We never sell your personal
                information to third parties. See our privacy policy for more details.
              </p>
            </div>
          </div>
        </div>

        {/* Final CTA */}
        <div className="text-center bg-slate-800 border border-slate-700 rounded-2xl p-8">
          <h2 className="text-2xl font-bold text-white mb-4">Ready to upgrade your nutrition game?</h2>
          <p className="text-slate-300 mb-6 max-w-2xl mx-auto">
            Join thousands of users who have transformed their eating habits with MacroMaps Pro.
          </p>
          <Button size="lg" className="bg-emerald-500 hover:bg-emerald-600 text-white font-medium px-8">
            Start Free Trial
          </Button>
        </div>
      </div>
    </div>
  )
}
