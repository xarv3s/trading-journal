"use client"

import Link from "next/link"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { BarChart3, List } from "lucide-react"

export default function JournalLandingPage() {
    return (
        <div className="container mx-auto py-10">
            <h1 className="text-3xl font-bold mb-8">Trading Journal</h1>
            <div className="grid gap-6 md:grid-cols-2">
                <Link href="/journal/dashboard">
                    <Card className="hover:bg-muted/50 transition-colors cursor-pointer h-full">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <BarChart3 className="h-6 w-6" />
                                Dashboard
                            </CardTitle>
                            <CardDescription>
                                View overall statistics, equity curve, and performance metrics.
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="text-sm text-muted-foreground">
                                Analyze your trading performance with detailed charts and KPIs.
                            </div>
                        </CardContent>
                    </Card>
                </Link>

                <Link href="/journal/trades">
                    <Card className="hover:bg-muted/50 transition-colors cursor-pointer h-full">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <List className="h-6 w-6" />
                                Trades
                            </CardTitle>
                            <CardDescription>
                                View and manage your complete trade history.
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="text-sm text-muted-foreground">
                                Access detailed records of all your closed trades.
                            </div>
                        </CardContent>
                    </Card>
                </Link>
            </div>
        </div>
    )
}
