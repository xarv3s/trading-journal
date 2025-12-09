"use client"

import * as React from "react"
import { InstrumentSearch } from "@/components/orders/instrument-search"
import { OrderForm } from "@/components/orders/order-form"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

interface Instrument {
    instrument_token: number
    tradingsymbol: string
    exchange: string
    last_price: number
    name: string
    expiry: string
    strike: number
    tick_size: number
    lot_size: number
    instrument_type: string
    segment: string
}

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { StrategyBuilder } from "@/components/orders/strategy-builder"

export default function OrdersPage() {
    const [selectedInstrument, setSelectedInstrument] = React.useState<Instrument | null>(null)
    const [transactionType, setTransactionType] = React.useState<"BUY" | "SELL">("BUY")

    React.useEffect(() => {
        async function fetchLTP() {
            if (!selectedInstrument) return

            try {
                const symbol = `${selectedInstrument.exchange}:${selectedInstrument.tradingsymbol}`
                const res = await fetch("http://localhost:8000/api/v1/market-data/ltp", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify([symbol])
                })

                if (res.ok) {
                    const data = await res.json()
                    const ltp = data[symbol]
                    if (ltp) {
                        setSelectedInstrument(prev => prev ? ({ ...prev, last_price: ltp }) : null)
                    }
                }
            } catch (error) {
                console.error("Failed to fetch LTP:", error)
            }
        }

        fetchLTP()
        // Set up an interval to refresh LTP every 2 seconds while selected
        const interval = setInterval(fetchLTP, 2000)
        return () => clearInterval(interval)
    }, [selectedInstrument?.instrument_token]) // Only re-run if instrument changes (using token as stable ID)

    return (
        <div className="container mx-auto py-8 space-y-8">
            <div className="flex flex-col gap-2">
                <h1 className="text-3xl font-bold tracking-tight">Orders</h1>
                <p className="text-muted-foreground">Place new orders for stocks, F&O, and currencies.</p>
            </div>

            <Tabs defaultValue="regular" className="w-full">
                <TabsList className="grid w-full max-w-[400px] grid-cols-2 mb-8">
                    <TabsTrigger value="regular">Stocks & Futures</TabsTrigger>
                    <TabsTrigger value="strategy">Options Strategy</TabsTrigger>
                </TabsList>

                <TabsContent value="regular" className="space-y-8">
                    <div className="flex flex-col items-center gap-8">
                        {/* Search Section */}
                        <Card className="w-full max-w-2xl">
                            <CardHeader>
                                <CardTitle>Search Instrument</CardTitle>
                                <CardDescription>Search for an instrument to place an order.</CardDescription>
                            </CardHeader>
                            <CardContent className="flex flex-col gap-4">
                                <InstrumentSearch onSelect={(inst) => {
                                    setSelectedInstrument(inst)
                                }} />

                                {selectedInstrument && (
                                    <div className="flex items-center gap-4 mt-4 p-4 border rounded-lg bg-secondary/10">
                                        <div className="flex-1">
                                            <div className="font-bold text-lg">{selectedInstrument.tradingsymbol}</div>
                                            <div className="text-sm text-muted-foreground">{selectedInstrument.name}</div>
                                            <div className="text-xs mt-1">
                                                <span className="bg-secondary px-1 rounded mr-2">{selectedInstrument.exchange}</span>
                                                <span>₹{selectedInstrument.last_price}</span>
                                            </div>
                                        </div>
                                        <div className="flex gap-2">
                                            <Button
                                                className="bg-teal-600 hover:bg-teal-700 text-white min-w-[80px]"
                                                onClick={() => setTransactionType("BUY")}
                                            >
                                                Buy
                                            </Button>
                                            <Button
                                                className="bg-rose-900 hover:bg-rose-950 text-white min-w-[80px]"
                                                onClick={() => setTransactionType("SELL")}
                                            >
                                                Sell
                                            </Button>
                                        </div>
                                    </div>
                                )}
                            </CardContent>
                        </Card>

                        {/* Order Form Section */}
                        {selectedInstrument && (
                            <div className="w-full max-w-2xl animate-in fade-in slide-in-from-bottom-4 duration-500">
                                <OrderForm
                                    instrument={selectedInstrument}
                                    transactionType={transactionType}
                                    onClose={() => setSelectedInstrument(null)}
                                />
                            </div>
                        )}
                    </div>
                </TabsContent>

                <TabsContent value="strategy">
                    <StrategyBuilder />
                </TabsContent>
            </Tabs>
        </div>
    )
}
