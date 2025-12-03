"use client"

import { useEffect, useState } from "react"
import { usePathname, useRouter } from "next/navigation"
import api from "@/lib/api"
import { toast } from "sonner"

export function ZerodhaAuthGuard({ children }: { children: React.ReactNode }) {
    const pathname = usePathname()
    const [isChecking, setIsChecking] = useState(true)

    useEffect(() => {
        const checkStatus = async () => {
            // Skip check if we are already on the login callback or just logged in
            if (pathname?.includes('/login/callback') || window.location.search.includes('login=success')) {
                setIsChecking(false)
                return
            }

            try {
                const { data } = await api.get('/login/status')
                if (data.status !== 'connected') {
                    // Redirect to login
                    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'
                    window.location.href = `${apiUrl}/login`
                } else {
                    setIsChecking(false)
                }
            } catch (error) {
                console.error("Auth check failed", error)
                // If backend is down or error, we might want to let them stay or retry
                // For now, let's assume if check fails, we are not connected
                // But to avoid loops if backend is down, maybe just show error?
                // Let's try to redirect, but maybe add a query param to avoid loop?
                // For now, simple redirect.
                const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'
                window.location.href = `${apiUrl}/login`
            }
        }

        checkStatus()
    }, [pathname])

    if (isChecking) {
        return <div className="flex h-screen w-screen items-center justify-center">Checking Zerodha connection...</div>
    }

    return <>{children}</>
}
