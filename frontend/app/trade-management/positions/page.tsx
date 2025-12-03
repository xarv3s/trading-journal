"use client"

import { useState, useMemo } from "react"
import { useTrades } from "@/hooks/use-trades"
import { useSyncTrades } from "@/hooks/use-sync"
import { useMarketStatus } from "@/hooks/use-market-status"
import { columns } from "./columns"
import { DataTable } from "@/components/ui/data-table"
import { SortingState } from "@tanstack/react-table"
import { Button } from "@/components/ui/button"
import { RefreshCw, TrendingUp, TrendingDown } from "lucide-react"
import { toast } from "sonner"
import { useQuery } from "@tanstack/react-query"
import api from "@/lib/api"
import { UnifiedTrade } from "@/types/trade"
import { Card, CardContent } from "@/components/ui/card"

export default function PositionsPage() {
    const [pagination, setPagination] = useState({
        pageIndex: 0,
        pageSize: 10,
    })
    const [sorting, setSorting] = useState<SortingState>([])
    const syncTrades = useSyncTrades()
    const { data: marketStatus } = useMarketStatus()

    const { data, isLoading, isError } = useTrades({
        page: pagination.pageIndex + 1,
        pageSize: pagination.pageSize,
        sortBy: sorting.length > 0 ? sorting[0].id : 'entry_date',
        sortDesc: sorting.length > 0 ? sorting[0].desc : true,
        status: 'OPEN'
    })

    // Extract symbols for LTP polling
    const symbols = useMemo(() => {
        if (!data?.data) return []
        return data.data.map((t: UnifiedTrade) => `${t.exchange}:${t.trading_symbol}`)
    }, [data?.data])

    // Poll for LTP
    const { data: ltpData } = useQuery({
        queryKey: ['ltp', symbols],
        queryFn: async () => {
            if (symbols.length === 0) return {}
            const res = await api.post('/market-data/ltp', symbols)
            return res.data
        },
        enabled: symbols.length > 0,
        refetchInterval: marketStatus?.open ? 10000 : false, // Poll every 10s if market is open, otherwise fetch once
    })

    // Merge LTP and calculate PnL and Risk
    const { tableData, totalUnrealizedPnL, totalOpenRisk } = useMemo(() => {
        if (!data?.data) return { tableData: [], totalUnrealizedPnL: 0, totalOpenRisk: 0 }

        let totalPnL = 0
        let totalRisk = 0

        const processedData = data.data.map((trade: UnifiedTrade) => {
            const instrumentKey = `${trade.exchange}:${trade.trading_symbol}`
            const ltp = ltpData ? ltpData[instrumentKey] : undefined

            let pnl = trade.pnl // Default to 0 or stored PnL
            // For open trades, pnl is usually 0 in DB, so we calculate it live
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
                // If SL < Entry, Risk = (Entry - SL) * Qty
                if (sl < trade.entry_price) {
                    risk = (trade.entry_price - sl) * trade.qty
                }
            } else {
                // For SHORT: Risk = (SL - Entry) * Qty
                // If SL is 0 (not set), we assume 0. 
                // But 0 < Entry usually, so (0 - Entry) is negative.
                // If SL > Entry, Risk is positive.
                if (sl > trade.entry_price) {
                    risk = (sl - trade.entry_price) * trade.qty
                }
            }

            totalRisk += risk
            totalPnL += pnl

            return {
                ...trade,
                ltp: ltp,
                pnl: pnl,
                open_risk: risk
            }
        })

        return { tableData: processedData, totalUnrealizedPnL: totalPnL, totalOpenRisk: totalRisk }
    }, [data?.data, ltpData])

    const handleSync = () => {
        syncTrades.mutate(undefined, {
            onSuccess: () => {
                toast.success("Sync Successful", {
                    description: "Trades have been synced with Zerodha.",
                })
            },
            onError: (error: any) => {
                if (error.response?.status === 401) {
                    toast.error("Session Expired", {
                        description: "Please connect your Zerodha account again.",
                        action: {
                            label: "Connect",
                            onClick: () => window.location.href = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/login`
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
        <div className="container mx-auto py-10">
            <div className="flex flex-col gap-6">
                <div className="flex justify-between items-start">
                    <div>
                        <h1 className="text-3xl font-bold tracking-tight">Open Positions</h1>
                        <p className="text-muted-foreground mt-1">
                            Manage your active trades and monitor real-time performance.
                        </p>
                    </div>
                    <div className="flex items-center gap-4">
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
                    pageCount={data ? Math.ceil(data.total / data.page_size) : -1}
                    pagination={pagination}
                    onPaginationChange={setPagination}
                    onSortingChange={setSorting}
                />
            </div>
        </div>
    )
}
