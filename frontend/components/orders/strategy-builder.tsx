"use client"

import * as React from "react"
import { InstrumentSearch } from "@/components/orders/instrument-search"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Trash2, Plus, Play } from "lucide-react"
import { toast } from "sonner"
import { cn } from "@/lib/utils"

interface Instrument {
    instrument_token: number
    tradingsymbol: string
    exchange: string
    last_price: number
    lot_size?: number
}

interface Leg {
    id: string
    instrument: Instrument
    transactionType: "BUY" | "SELL"
    product: string
    orderType: string
    quantity: number
    price: number
    triggerPrice: number
}

import { OptionChain } from "@/components/orders/option-chain"

// ... (interfaces remain same)

export function StrategyBuilder() {
    const [legs, setLegs] = React.useState<Leg[]>([])
    const [margin, setMargin] = React.useState<number>(0)
    const [calculatingMargin, setCalculatingMargin] = React.useState(false)

    // ... (remove unused state: selectedInstrument, transactionType, etc.)
    // Actually, we might want to keep some state if we want to edit legs later, but for now let's simplify.

    React.useEffect(() => {
        const calculateMargin = async () => {
            if (legs.length === 0) {
                setMargin(0)
                return
            }

            setCalculatingMargin(true)
            try {
                const payload = [{
                    type: 'BASKET',
                    id: 'preview',
                    constituents: legs.map(leg => ({
                        exchange: leg.instrument.exchange,
                        tradingsymbol: leg.instrument.tradingsymbol,
                        transaction_type: leg.transactionType,
                        quantity: leg.quantity,
                        product: leg.product,
                        order_type: leg.orderType,
                        price: leg.price,
                        variety: "regular"
                    }))
                }]

                const res = await fetch("http://localhost:8000/api/v1/market-data/margins", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                })

                if (res.ok) {
                    const data = await res.json()
                    setMargin(data['preview'] || 0)
                }
            } catch (error) {
                console.error("Margin calculation failed:", error)
            } finally {
                setCalculatingMargin(false)
            }
        }

        const timeoutId = setTimeout(calculateMargin, 500) // Debounce
        return () => clearTimeout(timeoutId)
    }, [legs])

    const handleAddLegFromChain = (option: any) => {
        const lots = option.lots || 1
        const quantity = lots * option.lot_size

        const newLeg: Leg = {
            id: Math.random().toString(36).substr(2, 9),
            instrument: {
                instrument_token: option.token,
                tradingsymbol: option.symbol,
                exchange: "NFO",
                last_price: option.ltp,
                lot_size: option.lot_size
            },
            transactionType: option.transactionType, // Passed from OptionChain button
            product: "NRML", // Default for options
            orderType: "MARKET",
            quantity: quantity,
            price: option.ltp,
            triggerPrice: 0
        }

        setLegs([...legs, newLeg])
        toast.success(`${option.transactionType} ${option.symbol} added`)
    }

    const removeLeg = (id: string) => {
        setLegs(legs.filter(l => l.id !== id))
    }

    const updateLegQuantity = (id: string, newQty: number) => {
        setLegs(legs.map(l => l.id === id ? { ...l, quantity: newQty } : l))
    }

    const executeStrategy = async () => {
        // ... (same execution logic)
        if (legs.length === 0) return

        try {
            const payload = legs.map(leg => ({
                tradingsymbol: leg.instrument.tradingsymbol,
                exchange: leg.instrument.exchange,
                transaction_type: leg.transactionType,
                quantity: leg.quantity,
                price: leg.orderType === "MARKET" ? 0 : leg.price,
                product: leg.product,
                order_type: leg.orderType,
                variety: "regular",
                trigger_price: 0
            }))

            const res = await fetch("http://localhost:8000/api/v1/orders/place-basket", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            })

            const data = await res.json()

            if (data.failure === 0) {
                toast.success(`Strategy executed! ${data.success} orders placed.`)
                setLegs([])
            } else {
                toast.error(`Partial execution: ${data.success} success, ${data.failure} failed.`)
            }
        } catch (error) {
            console.error("Strategy execution failed:", error)
            toast.error("Failed to execute strategy")
        }
    }

    return (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Left: Option Chain (Takes up 2 cols) */}
            <div className="lg:col-span-2 space-y-6">
                <Card>
                    <CardHeader>
                        <CardTitle>Option Chain</CardTitle>
                        <CardDescription>Select underlying and expiry to build your strategy.</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <OptionChain onAddLeg={handleAddLegFromChain} />
                    </CardContent>
                </Card>
            </div>

            {/* Right: Strategy Legs List (Takes up 1 col) */}
            <div className="space-y-6">
                <Card className="h-fit flex flex-col">
                    <CardHeader className="pb-3">
                        <div className="flex items-center justify-between">
                            <CardTitle>Strategy Legs</CardTitle>
                            {legs.length > 0 && (
                                <div className="text-right">
                                    <div className="text-xs text-muted-foreground">Margin Required</div>
                                    <div className={cn("font-bold", calculatingMargin && "opacity-50")}>
                                        ₹{margin.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                                    </div>
                                </div>
                            )}
                        </div>
                        <CardDescription>{legs.length} legs added</CardDescription>
                    </CardHeader>
                    <CardContent className="flex flex-col gap-4">
                        {legs.length === 0 ? (
                            <div className="min-h-[200px] flex items-center justify-center text-muted-foreground border-2 border-dashed rounded-lg">
                                No legs added yet
                            </div>
                        ) : (
                            <div className="space-y-2">
                                {legs.map((leg, i) => (
                                    <div key={leg.id} className="flex items-center justify-between p-3 border rounded-lg bg-card hover:bg-secondary/10 transition-colors">
                                        <div className="flex items-center gap-3">
                                            <div className={cn(
                                                "px-2 py-1 rounded text-xs font-bold text-white",
                                                leg.transactionType === "BUY" ? "bg-teal-600" : "bg-rose-900"
                                            )}>
                                                {leg.transactionType}
                                            </div>
                                            <div>
                                                <div className="font-semibold text-sm">{leg.instrument.tradingsymbol}</div>
                                                <div className="text-xs text-muted-foreground flex items-center gap-2 mt-1">
                                                    {leg.product} •
                                                    <div className="flex items-center gap-1">
                                                        Qty:
                                                        <Input
                                                            type="number"
                                                            className="h-6 w-16 text-xs px-1"
                                                            value={leg.quantity}
                                                            onChange={(e) => updateLegQuantity(leg.id, parseInt(e.target.value) || 0)}
                                                        />
                                                    </div>
                                                    • {leg.orderType === "MARKET" ? "MKT" : `₹${leg.price}`}
                                                </div>
                                            </div>
                                        </div>
                                        <Button variant="ghost" size="icon" onClick={() => removeLeg(leg.id)}>
                                            <Trash2 className="h-4 w-4 text-muted-foreground hover:text-destructive" />
                                        </Button>
                                    </div>
                                ))}
                            </div>
                        )}

                        {legs.length > 0 && (
                            <div className="mt-auto pt-4 border-t space-y-4">
                                <Button className="w-full" size="lg" onClick={executeStrategy}>
                                    <Play className="mr-2 h-4 w-4" /> Execute Strategy
                                </Button>
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}
