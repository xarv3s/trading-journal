"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ArrowRight, Wallet, LineChart, ShoppingCart } from "lucide-react"
import Link from "next/link"

export default function TradeManagementPage() {
    return (
        <div className="flex-1 space-y-4 p-8 pt-6">
            <div className="flex items-center justify-between space-y-2">
                <h2 className="text-3xl font-bold tracking-tight">Trade Management</h2>
            </div>
            <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-3">
                <Link href="/trade-management/positions">
                    <Card className="hover:bg-accent transition-colors cursor-pointer">
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">
                                Open Positions
                            </CardTitle>
                            <LineChart className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">Manage Trades</div>
                            <p className="text-xs text-muted-foreground">
                                View and manage your active open positions
                            </p>
                        </CardContent>
                    </Card>
                </Link>

                <Link href="/trade-management/transactions">
                    <Card className="hover:bg-accent transition-colors cursor-pointer">
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">
                                Transactions
                            </CardTitle>
                            <Wallet className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">Deposit / Withdraw</div>
                            <p className="text-xs text-muted-foreground">
                                Manage your capital and view transaction history
                            </p>
                        </CardContent>
                    </Card>
                </Link>

                <Link href="/trade-management/orders">
                    <Card className="hover:bg-accent transition-colors cursor-pointer">
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">
                                Orders
                            </CardTitle>
                            <ShoppingCart className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">Place Orders</div>
                            <p className="text-xs text-muted-foreground">
                                Buy and sell stocks, F&O, and currencies
                            </p>
                        </CardContent>
                    </Card>
                </Link>
            </div>
        </div >
    )
}
