"use client"

import { useState, useMemo, useEffect } from "react"
import { useTrades } from "@/hooks/use-trades"
import { useSyncTrades } from "@/hooks/use-sync"
import { useMarketStatus } from "@/hooks/use-market-status"
import { columns } from "./columns"
import { DataTable } from "@/components/ui/data-table"
import { SortingState, RowSelectionState } from "@tanstack/react-table"
import { Button } from "@/components/ui/button"
import { RefreshCw, TrendingUp, TrendingDown, AlertTriangle } from "lucide-react"
import { toast } from "sonner"
import { useQuery } from "@tanstack/react-query"
import api from "@/lib/api"
import { UnifiedTrade } from "@/types/trade"
import { Card, CardContent } from "@/components/ui/card"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"

export default function PositionsPage() {
    const [pagination, setPagination] = useState({
        pageIndex: 0,
        pageSize: 10000,
    })
    const [sorting, setSorting] = useState<SortingState>([])
    const [rowSelection, setRowSelection] = useState<RowSelectionState>({})
    const [isBasketDialogOpen, setIsBasketDialogOpen] = useState(false)
    const [basketName, setBasketName] = useState("")
    const [isCreatingBasket, setIsCreatingBasket] = useState(false)
    const [isSessionExpired, setIsSessionExpired] = useState(false)
    const [isAddToBasketDialogOpen, setIsAddToBasketDialogOpen] = useState(false)
    const [selectedTradeIdForBasket, setSelectedTradeIdForBasket] = useState<number | null>(null)
    const [selectedBasketId, setSelectedBasketId] = useState<string>("")
    const [isAddingToBasket, setIsAddingToBasket] = useState(false)
    const syncTrades = useSyncTrades()
    const { data: marketStatus } = useMarketStatus()

    const { data, isLoading, isError, refetch } = useTrades({
        page: 1,
        pageSize: 10000,
        sortBy: sorting.length > 0 ? sorting[0].id : 'entry_date',
        sortDesc: sorting.length > 0 ? sorting[0].desc : true,
        status: 'OPEN'
    })

    useEffect(() => {
        const handleSessionExpired = () => {
            setIsSessionExpired(true)
            toast.error("Session Expired", {
                description: "Please login to Zerodha again to fetch live data.",
                action: {
                    label: "Login",
                    onClick: () => window.location.href = '/login'
                },
                duration: Infinity
            })
        }

        window.addEventListener('session-expired', handleSessionExpired)
        return () => window.removeEventListener('session-expired', handleSessionExpired)
    }, [])


    const handleAddToBasket = (tradeId: string) => {
        // tradeId is like "OPEN_123"
        const id = parseInt(tradeId.replace('OPEN_', ''))
        setSelectedTradeIdForBasket(id)
        setIsAddToBasketDialogOpen(true)
    }

    const confirmAddToBasket = async () => {
        if (!selectedTradeIdForBasket || !selectedBasketId) return

        setIsAddingToBasket(true)
        try {
            // selectedBasketId is like "OPEN_456"
            const basketId = parseInt(selectedBasketId.replace('OPEN_', ''))

            await api.post(`/trades/basket/${basketId}/add`, {
                trade_ids: [selectedTradeIdForBasket]
            })

            toast.success("Trade added to basket successfully")
            setIsAddToBasketDialogOpen(false)
            setSelectedTradeIdForBasket(null)
            setSelectedBasketId("")
            refetch()
        } catch (error: any) {
            toast.error(error.response?.data?.detail || "Failed to add to basket")
            console.error(error)
        } finally {
            setIsAddingToBasket(false)
        }
    }

    const handleCreateBasket = async () => {
        const selectedIds = Object.keys(rowSelection).map(id => {
            if (id.startsWith('OPEN_')) {
                return parseInt(id.replace('OPEN_', ''))
            }
            return undefined
        }).filter(id => id !== undefined)

        if (selectedIds.length < 2) {
            toast.error("Please select at least 2 trades to create a basket.")
            return
        }

        setIsCreatingBasket(true)
        try {
            const response = await api.post('/trades/basket', {
                name: basketName,
                trade_ids: selectedIds,
                strategy_type: "TRENDING"
            })

            toast.success("Basket created successfully")
            setIsBasketDialogOpen(false)
            setRowSelection({})
            setBasketName("")
            refetch()
        } catch (error: any) {
            toast.error(error.response?.data?.detail || "Failed to create basket")
            console.error(error)
        } finally {
            setIsCreatingBasket(false)
        }
    }

    // Extract symbols for LTP polling
    const symbols = useMemo(() => {
        if (!data?.data) return []
        const syms: string[] = []
        data.data.forEach((t: UnifiedTrade) => {
            if (t.is_basket === 1 && t.constituents) {
                t.constituents.forEach((c: any) => {
                    syms.push(`${c.exchange}:${c.symbol}`)
                })
            } else {
                syms.push(`${t.exchange}:${t.trading_symbol}`)
            }
        })
        return syms
    }, [data?.data])

    // Poll for LTP
    const { data: ltpData, isError: isLtpError } = useQuery({
        queryKey: ['ltp', symbols],
        queryFn: async () => {
            if (symbols.length === 0) return {}
            try {
                const res = await api.post('/market-data/ltp', symbols)
                return res.data
            } catch (error: any) {
                if (error.response?.status === 401) {
                    setIsSessionExpired(true)
                }
                throw error
            }
        },
        enabled: symbols.length > 0 && !isSessionExpired,
        refetchInterval: marketStatus?.open && !isSessionExpired ? 10000 : false,
        retry: (failureCount, error: any) => {
            if (error.response?.status === 401) return false
            return failureCount < 3
        }
    })

    // Prepare items for margin calculation
    const marginItems = useMemo(() => {
        if (!data?.data) return []
        const items = data.data.map((t: UnifiedTrade) => {
            if (t.is_basket === 1 && t.constituents) {
                return {
                    type: 'BASKET',
                    id: t.id,
                    constituents: t.constituents.map((c: any) => ({
                        exchange: c.exchange,
                        tradingsymbol: c.symbol,
                        transaction_type: c.type === 'LONG' ? 'BUY' : 'SELL',
                        quantity: c.qty,
                        product: c.product || 'NRML',
                        variety: 'regular',
                        price: 0
                    }))
                }
            } else {
                return {
                    type: 'TRADE',
                    id: t.id,
                    constituents: [{
                        exchange: t.exchange,
                        tradingsymbol: t.trading_symbol,
                        transaction_type: t.type === 'LONG' ? 'BUY' : 'SELL',
                        quantity: t.qty,
                        product: t.order_type || 'NRML',
                        variety: 'regular',
                        price: 0
                    }]
                }
            }
        })
        return items
    }, [data?.data])

    // Fetch Margins
    const { data: marginData, isError: isMarginError } = useQuery({
        queryKey: ['margins', marginItems],
        queryFn: async () => {
            if (marginItems.length === 0) return {}
            try {
                const res = await api.post('/market-data/margins', marginItems)
                return res.data
            } catch (e: any) {
                console.error("Failed to fetch margins", e)
                if (e.response?.status === 401) {
                    setIsSessionExpired(true)
                }
                return {}
            }
        },
        enabled: marginItems.length > 0 && !isSessionExpired,
        staleTime: 1000 * 60 * 5,
        retry: (failureCount, error: any) => {
            if (error.response?.status === 401) return false
            return failureCount < 3
        }
    })

    // Fetch Exposure
    const { data: exposureData, isError: isExposureError } = useQuery({
        queryKey: ['exposure', marginItems],
        queryFn: async () => {
            if (marginItems.length === 0) return {}
            try {
                const res = await api.post('/market-data/exposure', marginItems)
                return res.data
            } catch (e: any) {
                console.error("Failed to fetch exposure", e)
                if (e.response?.status === 401) {
                    setIsSessionExpired(true)
                }
                return {}
            }
        },
        enabled: marginItems.length > 0 && !isSessionExpired,
        refetchInterval: marketStatus?.open && !isSessionExpired ? 10000 : false,
        retry: (failureCount, error: any) => {
            if (error.response?.status === 401) return false
            return failureCount < 3
        }
    })

    // Merge LTP and calculate PnL and Risk
    const { tableData, totalUnrealizedPnL, totalOpenRisk } = useMemo(() => {
        if (!data?.data) return { tableData: [], totalUnrealizedPnL: 0, totalOpenRisk: 0 }

        let totalPnL = 0
        let totalRisk = 0

        const processedData = data.data.map((trade: UnifiedTrade) => {
            // Margin & Exposure
            const margin = marginData ? marginData[trade.id] : undefined
            const exposure = exposureData ? exposureData[trade.id] : undefined

            // Handle Basket Trades
            if (trade.is_basket === 1) {
                let basketPnL = 0
                let basketRisk = 0
                // Exposure is now fetched from backend for baskets
                let basketExposure = exposure || 0

                const constituents = trade.constituents || []

                const updatedConstituents = constituents.map((c: any) => {
                    const instrumentKey = `${c.exchange}:${c.symbol}`
                    const ltp = ltpData ? ltpData[instrumentKey] : undefined

                    let pnl = 0
                    if (ltp) {
                        if (c.type === 'LONG') {
                            pnl = (ltp - c.avg_price) * c.qty
                        } else {
                            pnl = (c.avg_price - ltp) * c.qty
                        }
                        // Fallback exposure calculation if backend data missing? 
                        // No, backend handles it better.
                    }

                    basketPnL += pnl

                    return {
                        ...c,
                        ltp: ltp,
                        pnl: pnl
                    }
                })

                totalPnL += basketPnL

                return {
                    ...trade,
                    pnl: basketPnL,
                    open_risk: basketRisk,
                    margin_blocked: margin,
                    gross_exposure: basketExposure,
                    constituents: updatedConstituents
                }
            }

            // Handle Normal Trades
            const instrumentKey = `${trade.exchange}:${trade.trading_symbol}`
            const ltp = ltpData ? ltpData[instrumentKey] : undefined

            let pnl = trade.pnl // Default to 0 or stored PnL
            if (ltp) {
                if (trade.type === 'LONG') {
                    pnl = (ltp - trade.entry_price) * trade.qty
                } else {
                    pnl = (trade.entry_price - ltp) * trade.qty
                }
            }

            // Risk Calculation
            let risk = 0
            const sl = trade.stop_loss || 0

            if (trade.type === 'LONG') {
                if (sl < trade.entry_price) {
                    risk = (trade.entry_price - sl) * trade.qty
                }
            } else {
                if (sl > trade.entry_price) {
                    risk = (sl - trade.entry_price) * trade.qty
                }
            }

            totalRisk += risk
            totalPnL += pnl

            // Gross Exposure
            // Use backend exposure if available, else fallback to LTP * Qty
            let finalExposure = exposure
            if (finalExposure === undefined && ltp) {
                finalExposure = ltp * trade.qty
            }

            return {
                ...trade,
                ltp: ltp,
                pnl: pnl,
                open_risk: risk,
                margin_blocked: margin,
                gross_exposure: finalExposure
            }
        })

        return { tableData: processedData, totalUnrealizedPnL: totalPnL, totalOpenRisk: totalRisk }
    }, [data?.data, ltpData, marginData, exposureData])

    const handleSync = () => {
        syncTrades.mutate(undefined, {
            onSuccess: () => {
                toast.success("Sync Successful", {
                    description: "Trades have been synced with Zerodha.",
                })
            },
            onError: (error: any) => {
                if (error.response?.status === 401) {
                    setIsSessionExpired(true)
                    toast.error("Session Expired", {
                        description: "Please connect your Zerodha account again.",
                        action: {
                            label: "Connect",
                            onClick: () => window.location.href = '/login'
                        }
                    })
                } else {
                    toast.error("Sync Failed", {
                        description: "Failed to sync trades. Please check backend logs.",
                    })
                }
            }
        })
    }

    if (isLoading) {
        return <div className="flex items-center justify-center h-full p-8">Loading positions...</div>
    }

    if (isError) {
        return <div className="text-red-500 p-8">Error loading positions.</div>
    }

    return (
        <div className="container mx-auto py-10" >
            <div className="flex flex-col gap-6">
                {isSessionExpired && (
                    <Alert variant="destructive">
                        <AlertTriangle className="h-4 w-4" />
                        <AlertTitle>Session Expired</AlertTitle>
                        <AlertDescription className="flex items-center gap-2">
                            Your Zerodha session has expired. Live data (LTP, Margins) cannot be fetched.
                            <Button variant="outline" size="sm" className="h-6 text-xs bg-background text-foreground hover:bg-accent" onClick={() => window.location.href = '/login'}>
                                Login Again
                            </Button>
                        </AlertDescription>
                    </Alert>
                )}

                <div className="flex justify-between items-start">
                    <div>
                        <h1 className="text-3xl font-bold tracking-tight">Open Positions</h1>
                        <p className="text-muted-foreground mt-1">
                            Manage your active trades and monitor real-time performance.
                        </p>
                    </div>
                    <div className="flex items-center gap-4">
                        {Object.keys(rowSelection).length > 0 && (
                            <Dialog open={isBasketDialogOpen} onOpenChange={setIsBasketDialogOpen}>
                                <DialogTrigger asChild>
                                    <Button>Create Basket ({Object.keys(rowSelection).length})</Button>
                                </DialogTrigger>
                                <DialogContent className="sm:max-w-[425px]">
                                    <DialogHeader>
                                        <DialogTitle>Create Basket</DialogTitle>
                                        <DialogDescription>
                                            Group selected trades into a basket for unified tracking.
                                        </DialogDescription>
                                    </DialogHeader>
                                    <div className="grid gap-4 py-4">
                                        <div className="grid grid-cols-4 items-center gap-4">
                                            <Label htmlFor="name" className="text-right">
                                                Name
                                            </Label>
                                            <Input
                                                id="name"
                                                value={basketName}
                                                onChange={(e) => setBasketName(e.target.value)}
                                                className="col-span-3"
                                                placeholder="e.g. Iron Condor"
                                            />
                                        </div>
                                    </div>
                                    <DialogFooter>
                                        <Button onClick={handleCreateBasket} disabled={isCreatingBasket}>
                                            {isCreatingBasket ? "Creating..." : "Create"}
                                        </Button>
                                    </DialogFooter>
                                </DialogContent>
                            </Dialog>
                        )}

                        <Dialog open={isAddToBasketDialogOpen} onOpenChange={setIsAddToBasketDialogOpen}>
                            <DialogContent className="sm:max-w-[425px]">
                                <DialogHeader>
                                    <DialogTitle>Add to Basket</DialogTitle>
                                    <DialogDescription>
                                        Select a basket to add this trade to.
                                    </DialogDescription>
                                </DialogHeader>
                                <div className="grid gap-4 py-4">
                                    <div className="grid grid-cols-4 items-center gap-4">
                                        <Label htmlFor="basket" className="text-right">
                                            Basket
                                        </Label>
                                        <div className="col-span-3">
                                            <Select value={selectedBasketId} onValueChange={setSelectedBasketId}>
                                                <SelectTrigger>
                                                    <SelectValue placeholder="Select a basket" />
                                                </SelectTrigger>
                                                <SelectContent>
                                                    {data?.data?.filter((t: UnifiedTrade) => t.is_basket === 1).map((basket: UnifiedTrade) => (
                                                        <SelectItem key={basket.id} value={basket.id}>
                                                            {basket.trading_symbol}
                                                        </SelectItem>
                                                    ))}
                                                </SelectContent>
                                            </Select>
                                        </div>
                                    </div>
                                </div>
                                <DialogFooter>
                                    <Button onClick={confirmAddToBasket} disabled={isAddingToBasket || !selectedBasketId}>
                                        {isAddingToBasket ? "Adding..." : "Add"}
                                    </Button>
                                </DialogFooter>
                            </DialogContent>
                        </Dialog>
                        <div className="flex items-center gap-2 px-3 py-1 bg-muted rounded-full text-sm">
                            <div className={`w-2 h-2 rounded-full ${marketStatus?.open ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
                            {marketStatus?.open ? 'Market Open' : 'Market Closed'}
                        </div>
                        <Button onClick={handleSync} disabled={syncTrades.isPending}>
                            <RefreshCw className={`mr-2 h-4 w-4 ${syncTrades.isPending ? 'animate-spin' : ''}`} />
                            {syncTrades.isPending ? "Syncing..." : "Sync Trades"}
                        </Button>
                    </div>
                </div>

                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                    <Card>
                        <CardContent className="p-6">
                            <div className="flex items-center justify-between space-y-0 pb-2">
                                <p className="text-sm font-medium text-muted-foreground">Total Unrealized PnL</p>
                                {totalUnrealizedPnL >= 0 ? (
                                    <TrendingUp className="h-4 w-4 text-green-500" />
                                ) : (
                                    <TrendingDown className="h-4 w-4 text-red-500" />
                                )}
                            </div>
                            <div className={`text-2xl font-bold ${totalUnrealizedPnL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                {totalUnrealizedPnL >= 0 ? '+' : ''}₹{totalUnrealizedPnL.toFixed(2)}
                            </div>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardContent className="p-6">
                            <div className="flex items-center justify-between space-y-0 pb-2">
                                <p className="text-sm font-medium text-muted-foreground">Total Open Risk</p>
                                <TrendingDown className="h-4 w-4 text-red-500" />
                            </div>
                            <div className="text-2xl font-bold text-red-600">
                                ₹{totalOpenRisk.toFixed(2)}
                            </div>
                        </CardContent>
                    </Card>
                </div>

                <DataTable
                    columns={columns}
                    data={tableData}
                    hidePagination={true}
                    meta={{
                        handleAddToBasket
                    }}
                    pageCount={1}
                    pagination={pagination}
                    onPaginationChange={setPagination}
                    onSortingChange={setSorting}
                    rowSelection={rowSelection}
                    onRowSelectionChange={setRowSelection}
                    getRowId={(row) => row.id}
                    renderSubComponent={({ row }) => {
                        const constituents = row.original.constituents
                        if (!constituents || constituents.length === 0) return <div className="p-4 text-muted-foreground text-sm">No constituents</div>

                        return (
                            <div className="pl-12 pr-4 py-2 bg-muted/10 border-b border-border/50">
                                <div className="rounded-sm border border-border/20 overflow-hidden">
                                    <div className="grid grid-cols-12 gap-2 p-2 text-[10px] uppercase tracking-wider font-medium text-muted-foreground bg-muted/20 border-b border-border/20">
                                        <div className="col-span-1">Product</div>
                                        <div className="col-span-3">Instrument</div>
                                        <div className="col-span-2 text-right">Qty</div>
                                        <div className="col-span-2 text-right">Avg.</div>
                                        <div className="col-span-2 text-right">LTP</div>
                                        <div className="col-span-2 text-right">P&L</div>
                                    </div>
                                    {constituents.map((c: any) => (
                                        <div key={c.id} className="grid grid-cols-12 gap-2 p-2 text-sm items-center hover:bg-muted/10 transition-colors border-b border-border/10 last:border-0">
                                            <div className="col-span-1">
                                                <span className="text-[10px] px-1.5 py-0.5 rounded border border-blue-500/30 text-blue-400 bg-blue-500/10 uppercase">
                                                    {c.product || 'NRML'}
                                                </span>
                                            </div>
                                            <div className="col-span-3 flex items-center gap-2">
                                                <span className="font-medium text-foreground">{c.symbol}</span>
                                                <span className="text-[10px] text-muted-foreground uppercase">{c.exchange}</span>
                                            </div>
                                            <div className={`col-span-2 text-right font-mono ${c.type === 'LONG' ? 'text-blue-400' : 'text-red-400'}`}>
                                                {c.type === 'LONG' ? '+' : '-'}{c.qty}
                                            </div>
                                            <div className="col-span-2 text-right font-mono text-foreground">
                                                {c.avg_price?.toFixed(2)}
                                            </div>
                                            <div className="col-span-2 text-right font-mono text-foreground">
                                                {c.ltp ? c.ltp.toFixed(2) : '-'}
                                            </div>
                                            <div className={`col-span-2 text-right font-mono font-medium ${c.pnl > 0 ? 'text-green-500' : c.pnl < 0 ? 'text-red-500' : 'text-muted-foreground'
                                                }`}>
                                                {c.pnl ? (c.pnl > 0 ? "+" : "") + c.pnl.toFixed(2) : '-'}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )
                    }}
                />
            </div>
        </div>
    )
}
