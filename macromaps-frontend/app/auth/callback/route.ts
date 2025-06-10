import { createServerComponentClient } from "@/lib/supabase"
import { cookies } from "next/headers"
import { type NextRequest, NextResponse } from "next/server"

export async function GET(request: NextRequest) {
  const requestUrl = new URL(request.url)
  const code = requestUrl.searchParams.get("code")
  const next = requestUrl.searchParams.get("next") ?? "/"

  if (code) {
    const cookieStore = cookies()
    const supabase = await createServerComponentClient()

    try {
      const { error } = await supabase.auth.exchangeCodeForSession(code)
      if (error) {
        console.error("Error exchanging code for session:", error)
        return NextResponse.redirect(new URL("/auth/auth-code-error", requestUrl.origin))
      }
    } catch (error) {
      console.error("Exception during auth:", error)
      return NextResponse.redirect(new URL("/auth/auth-code-error", requestUrl.origin))
    }
  }

  // Redirect to home page after successful authentication
  return NextResponse.redirect(new URL(next, requestUrl.origin))
}
