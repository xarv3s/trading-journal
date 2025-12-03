"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { BookOpen, Activity } from "lucide-react"
import Link from "next/link"
import api from "@/lib/api"

export default function Home() {
    const [status, setStatus] = useState<'loading' | 'connected' | 'disconnected'>('loading')

    useEffect(() => {
        checkStatus()
    }, [])

    const checkStatus = async () => {
        try {
            const res = await api.get('/login/status')
            if (res.data.status === 'connected') {
                setStatus('connected')
            } else {
                setStatus('disconnected')
            }
        } catch (error) {
            console.error("Failed to check login status", error)
            setStatus('disconnected')
        }
    }

    const handleLogin = () => {
        window.location.href = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/login`
    }

    if (status === 'loading') {
        return <div className="flex items-center justify-center h-screen">Checking connection...</div>
    }

    return (
        <div className="container mx-auto py-20">
            <div className="text-center mb-12">
                <h1 className="text-4xl font-bold mb-4">Trading Platform</h1>
                <p className="text-muted-foreground">Your personal trading command center</p>
            </div>

            <div className="flex justify-center">
                {status === 'disconnected' ? (
                    <Card className="w-[350px]">
                        <CardHeader>
                            <CardTitle>Connect Account</CardTitle>
                            <CardDescription>Connect your Zerodha account to access the platform.</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <Button className="w-full" onClick={handleLogin}>
                                Connect Zerodha
                            </Button>
                        </CardContent>
                    </Card>
                ) : (
                    <div className="grid gap-6 md:grid-cols-2">
                        <Link href="/journal">
                            <Card className="w-[350px] hover:bg-muted/50 transition-colors cursor-pointer h-full">
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2">
                                        <BookOpen className="h-6 w-6" />
                                        Journal
                                    </CardTitle>
                                    <CardDescription>
                                        Access your trading journal, dashboard, and trade history.
                                    </CardDescription>
                                </CardHeader>
                            </Card>
                        </Link>

                        <Link href="/trade-management">
                            <Card className="w-[350px] hover:bg-muted/50 transition-colors cursor-pointer h-full">
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2">
                                        <Activity className="h-6 w-6" />
                                        Trade Management
                                    </CardTitle>
                                    <CardDescription>
                                        Manage your open positions and active trades.
                                    </CardDescription>
                                </CardHeader>
                            </Card>
                        </Link>
                    </div>
                )}
            </div>
        </div>
    )
}
