"use client"

import * as React from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { cn } from "@/lib/utils"
import { RefreshCw, Info } from "lucide-react"
import { toast } from "sonner"

interface Instrument {
    instrument_token: number
    tradingsymbol: string
    exchange: string
    last_price: number
    lot_size?: number
}

interface OrderFormProps {
    instrument: Instrument | null
    transactionType: "BUY" | "SELL"
    onClose: () => void
}

export function OrderForm({ instrument, transactionType, onClose }: OrderFormProps) {
    if (!instrument) {
        return (
            <div className="p-8 text-center text-muted-foreground">
                Select an instrument to place an order.
            </div>
        )
    }
    const [qty, setQty] = React.useState<number | string>(1)
    const [price, setPrice] = React.useState<number | string>(instrument?.last_price || "")
    const [stopLoss, setStopLoss] = React.useState<number | string>("")
    const [maxRisk, setMaxRisk] = React.useState<number | string>(1000)
    const [existingTrade, setExistingTrade] = React.useState<any>(null)
    const [product, setProduct] = React.useState("MIS") // MIS, CNC, MTF
    const [orderType, setOrderType] = React.useState("LIMIT") // MARKET, LIMIT, SL, SL-M

    // Fetch existing trade
    React.useEffect(() => {
        async function fetchExistingTrade() {
            if (!instrument) return
            try {
                const res = await fetch(`http://localhost:8000/api/v1/trades/open?symbol=${instrument.tradingsymbol}`)
                if (res.ok) {
                    const data = await res.json()
                    if (data && data.length > 0) {
                        setExistingTrade(data[0])
                    } else {
                        setExistingTrade(null)
                    }
                }
            } catch (e) {
                console.error("Error fetching existing trade", e)
            }
        }
        fetchExistingTrade()
    }, [instrument?.instrument_token])

    const isBuy = transactionType === "BUY"
    // Dull greenish blue for Buy, Dull darker red for Sell
    const themeColor = isBuy ? "bg-teal-600 hover:bg-teal-700" : "bg-rose-900 hover:bg-rose-950"
    const textColor = isBuy ? "text-teal-500" : "text-rose-500"

    const [margin, setMargin] = React.useState<number | null>(null)
    const [isFetchingMargin, setIsFetchingMargin] = React.useState(false)

    // Lot Size Logic
    const isLotBased = (instrument.lot_size || 1) > 1
    const [lots, setLots] = React.useState<number | string>(1)

    // Calculate effective quantity
    const effectiveQty = isLotBased ? Number(lots) * (instrument.lot_size || 1) : Number(qty)

    // Calculate Exposure
    const exposure = Number(price) * effectiveQty

    // Calculate Suggested Quantity
    let suggestedQty = 0
    let suggestedLots = 0

    if (price && stopLoss && maxRisk) {
        const riskPerShare = Math.abs(Number(price) - Number(stopLoss))

        if (riskPerShare > 0) {
            let availableRisk = Number(maxRisk)

            if (existingTrade) {
                const existingRisk = existingTrade.qty * Math.abs(existingTrade.avg_price - Number(stopLoss))
                availableRisk = Number(maxRisk) - existingRisk
            }

            if (availableRisk > 0) {
                const rawQty = Math.floor(availableRisk / riskPerShare)
                if (isLotBased) {
                    suggestedLots = Math.floor(rawQty / (instrument.lot_size || 1))
                    suggestedQty = suggestedLots * (instrument.lot_size || 1)
                } else {
                    suggestedQty = rawQty
                }
            }
        }
    }

    React.useEffect(() => {
        const timer = setTimeout(async () => {
            if (!instrument || !effectiveQty || !price) return

            setIsFetchingMargin(true)
            try {
                const payload = [{
                    type: "TRADE",
                    id: "margin_check",
                    constituents: [{
                        exchange: instrument.exchange,
                        tradingsymbol: instrument.tradingsymbol,
                        transaction_type: transactionType,
                        quantity: effectiveQty,
                        product: product,
                        order_type: orderType,
                        price: Number(price),
                        variety: "regular"
                    }]
                }]

                const res = await fetch("http://localhost:8000/api/v1/market-data/margins", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                })

                if (res.ok) {
                    const data = await res.json()
                    setMargin(data["margin_check"])
                }
            } catch (error) {
                console.error("Failed to fetch margin:", error)
            } finally {
                setIsFetchingMargin(false)
            }
        }, 500)

        return () => clearTimeout(timer)
    }, [lots, qty, price, product, transactionType, orderType, instrument?.instrument_token])

    return (
        <div className="w-full max-w-2xl bg-card border rounded-lg shadow-lg overflow-hidden">
            {/* Header */}
            <div className={cn("p-4 flex items-center justify-between text-white", isBuy ? "bg-teal-600" : "bg-rose-900")}>
                <div className="flex flex-col">
                    <div className="flex items-center gap-2">
                        <span className="font-semibold text-lg">{transactionType} {instrument.tradingsymbol}</span>
                        <span className="text-xs opacity-80">{instrument.exchange} x {effectiveQty} Qty</span>
                    </div>
                    <div className="flex items-center gap-4 text-xs mt-1 opacity-90">
                        <div className="flex items-center gap-1">
                            <input type="radio" checked readOnly className="accent-white" />
                            <span>{instrument.exchange}: ₹{instrument.last_price}</span>
                        </div>
                        {isLotBased && (
                            <div className="bg-black/20 px-2 py-0.5 rounded">
                                Lot Size: {instrument.lot_size}
                            </div>
                        )}
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <Info className="h-4 w-4" />
                </div>
            </div>

            {/* Body */}
            <div className="p-4 space-y-6">
                {/* Product Type */}
                {/* Product Type */}
                <div className="flex items-center gap-8">
                    {/* MIS is always available */}
                    <div className="flex items-center space-x-2">
                        <input
                            type="radio"
                            id="mis"
                            name="product"
                            value="MIS"
                            checked={product === "MIS"}
                            onChange={(e) => setProduct(e.target.value)}
                            className="accent-teal-500 h-4 w-4"
                        />
                        <Label htmlFor="mis" className="cursor-pointer">Intraday <span className="text-muted-foreground text-xs uppercase">MIS</span></Label>
                    </div>

                    {/* Equity Options: CNC, MTF */}
                    {(instrument.exchange === "NSE" || instrument.exchange === "BSE") && (
                        <>
                            <div className="flex items-center space-x-2">
                                <input
                                    type="radio"
                                    id="cnc"
                                    name="product"
                                    value="CNC"
                                    checked={product === "CNC"}
                                    onChange={(e) => setProduct(e.target.value)}
                                    className="accent-teal-500 h-4 w-4"
                                />
                                <Label htmlFor="cnc" className="cursor-pointer">Longterm <span className="text-muted-foreground text-xs uppercase">CNC</span></Label>
                            </div>
                            <div className="flex items-center space-x-2">
                                <input
                                    type="radio"
                                    id="mtf"
                                    name="product"
                                    value="MTF"
                                    checked={product === "MTF"}
                                    onChange={(e) => setProduct(e.target.value)}
                                    className="accent-teal-500 h-4 w-4"
                                />
                                <Label htmlFor="mtf" className="cursor-pointer">Margin <span className="text-muted-foreground text-xs uppercase">MTF</span></Label>
                            </div>
                        </>
                    )}

                    {/* F&O Options: NRML */}
                    {(instrument.exchange === "NFO" || instrument.exchange === "MCX" || instrument.exchange === "CDS") && (
                        <div className="flex items-center space-x-2">
                            <input
                                type="radio"
                                id="nrml"
                                name="product"
                                value="NRML"
                                checked={product === "NRML"}
                                onChange={(e) => setProduct(e.target.value)}
                                className="accent-teal-500 h-4 w-4"
                            />
                            <Label htmlFor="nrml" className="cursor-pointer">Overnight <span className="text-muted-foreground text-xs uppercase">NRML</span></Label>
                        </div>
                    )}
                </div>

                {/* Inputs */}
                <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-1">
                        <Label className="text-xs text-muted-foreground">Price</Label>
                        <Input
                            type="number"
                            value={price}
                            onChange={(e) => setPrice(e.target.value === "" ? "" : Number(e.target.value))}
                            disabled={orderType === "MARKET"}
                            className="bg-secondary/50"
                        />
                    </div>
                    <div className="space-y-1">
                        <Label className="text-xs text-muted-foreground">Stop Loss</Label>
                        <Input
                            type="number"
                            value={stopLoss}
                            onChange={(e) => setStopLoss(e.target.value === "" ? "" : Number(e.target.value))}
                            className="bg-secondary/50"
                        />
                    </div>
                    <div className="space-y-1">
                        <Label className="text-xs text-muted-foreground">Max Risk (₹)</Label>
                        <Input
                            type="number"
                            value={maxRisk}
                            onChange={(e) => setMaxRisk(e.target.value === "" ? "" : Number(e.target.value))}
                            className="bg-secondary/50"
                        />
                    </div>
                    <div className="space-y-1">
                        <Label className="text-xs text-muted-foreground">{isLotBased ? "Lots" : "Qty."}</Label>
                        <div className="flex flex-col gap-1">
                            <Input
                                type="number"
                                value={isLotBased ? lots : qty}
                                onChange={(e) => {
                                    const val = e.target.value === "" ? "" : Number(e.target.value)
                                    if (isLotBased) setLots(val)
                                    else setQty(val)
                                }}
                                className="bg-secondary/50"
                            />
                            {isLotBased && (
                                <span className="text-[10px] text-muted-foreground">
                                    Total Qty: {effectiveQty}
                                </span>
                            )}
                        </div>
                    </div>
                </div>

                {/* Order Type */}
                <div className="flex items-center gap-6 pt-2">
                    {["MARKET", "LIMIT", "SL", "SL-M"].map((type) => (
                        <div key={type} className="flex items-center space-x-2">
                            <input
                                type="radio"
                                id={type}
                                name="orderType"
                                value={type}
                                checked={orderType === type}
                                onChange={(e) => setOrderType(e.target.value)}
                                className="accent-teal-500 h-4 w-4"
                            />
                            <Label htmlFor={type} className="cursor-pointer capitalize text-sm">{type === "SL-M" ? "SL-M" : type.toLowerCase()}</Label>
                        </div>
                    ))}
                </div>
            </div>

            {/* Footer */}
            <div className="p-4 bg-secondary/20 border-t flex items-center justify-between">
                <div className="flex flex-col gap-1">
                    <div className="flex items-center gap-2 text-sm">
                        <span className="text-muted-foreground">Margin required</span>
                        <Info className="h-3 w-3 text-muted-foreground" />
                        <span className="font-mono">
                            {isFetchingMargin ? (
                                <span className="animate-pulse">...</span>
                            ) : (
                                `₹${margin?.toLocaleString('en-IN', { maximumFractionDigits: 2 }) || '0.00'}`
                            )}
                        </span>
                        <RefreshCw
                            className={cn("h-3 w-3 text-teal-500 cursor-pointer", isFetchingMargin && "animate-spin")}
                            onClick={() => {
                                // Trigger re-fetch manually if needed, though useEffect handles it
                                setMargin(null) // Clear to show loading
                            }}
                        />
                    </div>
                    <div className="flex items-center gap-4 text-xs">
                        <div className="flex items-center gap-2">
                            <span className="text-muted-foreground">Exposure</span>
                            <span className="font-mono text-muted-foreground">
                                ₹{exposure.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                            </span>
                        </div>
                        {(price && stopLoss && maxRisk) && (
                            <div
                                className="flex items-center gap-2 cursor-pointer hover:bg-secondary/50 px-2 py-0.5 rounded transition-colors"
                                onClick={() => {
                                    if (suggestedQty > 0) {
                                        if (isLotBased) setLots(suggestedLots)
                                        else setQty(suggestedQty)
                                    }
                                }}
                            >
                                <span className="text-muted-foreground">Suggested:</span>
                                {suggestedQty > 0 ? (
                                    <span className="font-mono text-teal-500 font-bold">
                                        {isLotBased ? `${suggestedLots} Lots` : suggestedQty}
                                    </span>
                                ) : (
                                    <span className="font-mono text-rose-500 font-bold">
                                        0 (Risk too high)
                                    </span>
                                )}
                            </div>
                        )}
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <Button variant="outline" onClick={onClose}>Cancel</Button>
                    <Button
                        className={cn("min-w-[100px]", themeColor)}
                        onClick={async () => {
                            try {
                                const payload = {
                                    tradingsymbol: instrument.tradingsymbol,
                                    exchange: instrument.exchange,
                                    transaction_type: transactionType,
                                    quantity: effectiveQty,
                                    price: (orderType === "MARKET" || orderType === "SL-M") ? 0 : Number(price),
                                    product: product,
                                    order_type: orderType,
                                    variety: "regular",
                                    trigger_price: (orderType === "SL" || orderType === "SL-M") ? Number(stopLoss) : 0
                                }

                                const res = await fetch("http://localhost:8000/api/v1/orders/place", {
                                    method: "POST",
                                    headers: { "Content-Type": "application/json" },
                                    body: JSON.stringify(payload)
                                })

                                if (!res.ok) {
                                    const error = await res.json()
                                    throw new Error(error.detail || "Failed to place order")
                                }

                                const data = await res.json()
                                toast.success(`Order placed successfully! ID: ${data.order_id}`)
                                onClose()
                            } catch (error: any) {
                                toast.error(error.message)
                                console.error("Order placement failed:", error)
                            }
                        }}
                        disabled={effectiveQty <= 0}
                    >
                        {transactionType === "BUY" ? "Buy" : "Sell"}
                    </Button>
                </div>
            </div>
        </div>
    )
}
