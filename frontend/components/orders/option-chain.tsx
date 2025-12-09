"use client"

import * as React from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Input } from "@/components/ui/input"
import { Search, RefreshCw } from "lucide-react"
import { toast } from "sonner"
import { cn } from "@/lib/utils"

interface OptionChainProps {
    onAddLeg: (leg: any) => void
}

interface ChainData {
    underlying: string
    underlying_ltp: number
    expiries: string[]
    current_expiry: string
    chain: StrikeData[]
}

interface StrikeData {
    strike: number
    ce?: OptionData
    pe?: OptionData
}

interface OptionData {
    symbol: string
    ltp: number
    delta: number
    token: number
    lot_size: number
}

const COMMON_INSTRUMENTS = [
    "NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY",
    "RELIANCE", "HDFCBANK", "INFY", "TCS", "ICICIBANK",
    "SBIN", "AXISBANK", "KOTAKBANK", "ITC", "LT"
]

export function OptionChain({ onAddLeg }: OptionChainProps) {
    const [query, setQuery] = React.useState("NIFTY")
    const [loading, setLoading] = React.useState(false)
    const [data, setData] = React.useState<ChainData | null>(null)
    const [selectedExpiry, setSelectedExpiry] = React.useState<string>("")
    const [defaultLots, setDefaultLots] = React.useState<number>(1)

    React.useEffect(() => {
        const saved = localStorage.getItem("optionChainDefaultLots")
        if (saved) setDefaultLots(parseInt(saved))
    }, [])

    React.useEffect(() => {
        localStorage.setItem("optionChainDefaultLots", defaultLots.toString())
    }, [defaultLots])

    const fetchChain = async (symbol: string) => {
        setLoading(true)
        try {
            const res = await fetch(`http://localhost:8000/api/v1/market-data/option-chain/${symbol.toUpperCase()}`)
            if (res.ok) {
                const chainData = await res.json()
                if (chainData.error) {
                    toast.error(chainData.error)
                    setData(null)
                } else {
                    setData(chainData)
                    setSelectedExpiry(chainData.current_expiry)
                }
            } else {
                toast.error("Failed to fetch option chain")
            }
        } catch (error) {
            console.error("Option chain fetch error:", error)
            toast.error("Failed to fetch option chain")
        } finally {
            setLoading(false)
        }
    }

    React.useEffect(() => {
        // Initial fetch for NIFTY
        fetchChain("NIFTY")
    }, [])

    const handleSymbolChange = (value: string) => {
        setQuery(value)
        fetchChain(value)
    }

    const handleRefresh = () => {
        fetchChain(query)
    }

    // Filter chain for selected expiry
    // Note: The backend currently returns data for the nearest expiry only in the 'chain' array
    // If we want to support multiple expiries, we need to update backend or filter here if backend returns all.
    // Current backend implementation: returns chain for 'nearest_expiry' but lists all 'expiries'.
    // So changing expiry in dropdown won't update the table unless we fetch again with expiry param (which we didn't implement yet).
    // For now, let's just show the current expiry data.

    return (
        <div className="space-y-4">
            <div className="flex flex-col md:flex-row gap-4 items-end justify-between">
                <div className="flex gap-4 items-end">
                    <div className="grid w-full max-w-sm items-center gap-1.5">
                        <div className="text-xs text-muted-foreground">Underlying</div>
                        <Select value={query} onValueChange={handleSymbolChange}>
                            <SelectTrigger className="w-[140px]">
                                <SelectValue placeholder="Select Symbol" />
                            </SelectTrigger>
                            <SelectContent>
                                {COMMON_INSTRUMENTS.map(inst => (
                                    <SelectItem key={inst} value={inst}>{inst}</SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>

                    <Button variant="outline" size="icon" onClick={handleRefresh} disabled={loading}>
                        {loading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
                    </Button>

                    <div className="grid w-full max-w-sm items-center gap-1.5">
                        <div className="text-xs text-muted-foreground">Lots</div>
                        <Input
                            type="number"
                            min={1}
                            value={defaultLots}
                            onChange={(e) => setDefaultLots(parseInt(e.target.value) || 1)}
                            className="w-20"
                        />
                    </div>
                </div>

                {data && (
                    <div className="flex gap-4 items-center">
                        <div className="text-sm">
                            <span className="text-muted-foreground">Spot:</span>
                            <span className="ml-2 font-bold text-lg">{data.underlying_ltp.toFixed(2)}</span>
                        </div>

                        <Select value={selectedExpiry} onValueChange={setSelectedExpiry}>
                            <SelectTrigger className="w-[140px]">
                                <SelectValue placeholder="Expiry" />
                            </SelectTrigger>
                            <SelectContent>
                                {data.expiries.map(exp => (
                                    <SelectItem key={exp} value={exp}>{exp}</SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>
                )}
            </div>

            {data ? (
                <div className="border rounded-md overflow-hidden">
                    <Table>
                        <TableHeader>
                            <TableRow className="bg-secondary/50">
                                <TableHead className="text-center w-[100px] text-xs">Call Delta</TableHead>
                                <TableHead className="text-center w-[100px] text-xs">LTP</TableHead>
                                <TableHead className="text-center w-[80px] text-xs">Buy/Sell</TableHead>
                                <TableHead className="text-center font-bold bg-secondary text-xs">Strike</TableHead>
                                <TableHead className="text-center w-[80px] text-xs">Buy/Sell</TableHead>
                                <TableHead className="text-center w-[100px] text-xs">LTP</TableHead>
                                <TableHead className="text-center w-[100px] text-xs">Put Delta</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {data.chain.map((row) => (
                                <TableRow key={row.strike} className="hover:bg-secondary/20 h-8">
                                    {/* CALL SIDE */}
                                    <TableCell className="text-center text-xs text-muted-foreground py-1">
                                        {row.ce?.delta.toFixed(2) || "-"}
                                    </TableCell>
                                    <TableCell className="text-center font-medium text-xs py-1">
                                        {row.ce?.ltp.toFixed(2) || "-"}
                                    </TableCell>
                                    <TableCell className="text-center p-1 py-1">
                                        {row.ce && (
                                            <div className="flex gap-1 justify-center">
                                                <Button
                                                    size="sm"
                                                    variant="outline"
                                                    className="h-5 w-5 p-0 bg-teal-600/10 hover:bg-teal-600 hover:text-white border-teal-600/20 text-teal-600 text-[10px]"
                                                    onClick={() => onAddLeg({ ...row.ce, type: 'CE', strike: row.strike, transactionType: 'BUY', lots: defaultLots })}
                                                >
                                                    B
                                                </Button>
                                                <Button
                                                    size="sm"
                                                    variant="outline"
                                                    className="h-5 w-5 p-0 bg-rose-600/10 hover:bg-rose-600 hover:text-white border-rose-600/20 text-rose-600 text-[10px]"
                                                    onClick={() => onAddLeg({ ...row.ce, type: 'CE', strike: row.strike, transactionType: 'SELL', lots: defaultLots })}
                                                >
                                                    S
                                                </Button>
                                            </div>
                                        )}
                                    </TableCell>

                                    {/* STRIKE */}
                                    <TableCell className="text-center font-bold bg-secondary/30 text-xs py-1">
                                        {row.strike}
                                    </TableCell>

                                    {/* PUT SIDE */}
                                    <TableCell className="text-center p-1 py-1">
                                        {row.pe && (
                                            <div className="flex gap-1 justify-center">
                                                <Button
                                                    size="sm"
                                                    variant="outline"
                                                    className="h-5 w-5 p-0 bg-teal-600/10 hover:bg-teal-600 hover:text-white border-teal-600/20 text-teal-600 text-[10px]"
                                                    onClick={() => onAddLeg({ ...row.pe, type: 'PE', strike: row.strike, transactionType: 'BUY', lots: defaultLots })}
                                                >
                                                    B
                                                </Button>
                                                <Button
                                                    size="sm"
                                                    variant="outline"
                                                    className="h-5 w-5 p-0 bg-rose-600/10 hover:bg-rose-600 hover:text-white border-rose-600/20 text-rose-600 text-[10px]"
                                                    onClick={() => onAddLeg({ ...row.pe, type: 'PE', strike: row.strike, transactionType: 'SELL', lots: defaultLots })}
                                                >
                                                    S
                                                </Button>
                                            </div>
                                        )}
                                    </TableCell>
                                    <TableCell className="text-center font-medium text-xs py-1">
                                        {row.pe?.ltp.toFixed(2) || "-"}
                                    </TableCell>
                                    <TableCell className="text-center text-xs text-muted-foreground py-1">
                                        {row.pe?.delta.toFixed(2) || "-"}
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </div>
            ) : (
                <div className="text-center p-8 text-muted-foreground border rounded-lg border-dashed">
                    Search for a symbol to view Option Chain
                </div>
            )}
        </div>
    )
}
