"use client"

import * as React from "react"
import { Check, ChevronsUpDown, Search } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { Card } from "@/components/ui/card"

interface Instrument {
    instrument_token: number
    exchange_token: number
    tradingsymbol: string
    name: string
    last_price: number
    expiry: string
    strike: number
    tick_size: number
    lot_size: number
    instrument_type: string
    segment: string
    exchange: string
}

interface InstrumentSearchProps {
    onSelect: (instrument: Instrument) => void
    defaultExchange?: string
    hideExchangeSelector?: boolean
}

export function InstrumentSearch({ onSelect, defaultExchange, hideExchangeSelector }: InstrumentSearchProps) {
    const [open, setOpen] = React.useState(false)
    const [query, setQuery] = React.useState("")
    const [results, setResults] = React.useState<Instrument[]>([])
    const [loading, setLoading] = React.useState(false)
    const [exchange, setExchange] = React.useState(defaultExchange || "NSE")

    React.useEffect(() => {
        const fetchInstruments = async () => {
            if (query.length < 2) {
                setResults([])
                return
            }

            setLoading(true)
            try {
                const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/market-data/instruments/search?q=${query}&exchange=${exchange}`)
                if (res.ok) {
                    const data = await res.json()
                    setResults(data)
                }
            } catch (error) {
                console.error("Failed to search instruments", error)
            } finally {
                setLoading(false)
            }
        }

        const debounce = setTimeout(fetchInstruments, 300)
        return () => clearTimeout(debounce)
    }, [query, exchange])

    return (
        <div className="flex gap-2 w-full max-w-lg">
            {!hideExchangeSelector && (
                <Select value={exchange} onValueChange={setExchange}>
                    <SelectTrigger className="w-[100px]">
                        <SelectValue placeholder="Exch" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="NSE">NSE</SelectItem>
                        <SelectItem value="NFO">NFO</SelectItem>
                        <SelectItem value="BSE">BSE</SelectItem>
                        <SelectItem value="MCX">MCX</SelectItem>
                    </SelectContent>
                </Select>
            )}

            <div className="relative flex-1">
                <div className="relative">
                    <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input
                        placeholder={`Search ${exchange} instruments...`}
                        value={query}
                        onChange={(e) => {
                            setQuery(e.target.value)
                            setOpen(true)
                        }}
                        className="pl-8"
                        onFocus={() => setOpen(true)}
                    />
                </div>

                {open && results.length > 0 && (
                    <Card className="absolute top-full mt-1 w-full z-50 max-h-[300px] overflow-y-auto p-1 shadow-md">
                        {results.map((instrument) => (
                            <div
                                key={instrument.instrument_token}
                                className="flex items-center justify-between p-2 hover:bg-accent hover:text-accent-foreground cursor-pointer rounded-sm text-sm"
                                onClick={() => {
                                    onSelect(instrument)
                                    setOpen(false)
                                    setQuery(instrument.tradingsymbol)
                                }}
                            >
                                <div className="flex flex-col">
                                    <span className="font-medium">{instrument.tradingsymbol}</span>
                                    <span className="text-xs text-muted-foreground">{instrument.name}</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <span className="text-xs font-mono bg-secondary px-1 rounded">{instrument.exchange}</span>
                                </div>
                            </div>
                        ))}
                    </Card>
                )}

                {open && query.length >= 2 && results.length === 0 && !loading && (
                    <Card className="absolute top-full mt-1 w-full z-50 p-2 shadow-md text-sm text-muted-foreground text-center">
                        No results found.
                    </Card>
                )}
            </div>
        </div>
    )
}
