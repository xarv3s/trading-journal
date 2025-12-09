"use client"

import { useState, useMemo, useCallback } from "react"
import { useQuery } from "@tanstack/react-query"
import api from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Loader2 } from "lucide-react"
import { TVChart } from "@/components/charts/TVChart"
import { useTheme } from "next-themes"

export default function EquityCurvePage() {
    const [activeTab, setActiveTab] = useState("intraday")
    const { theme } = useTheme()

    const chartColors = useMemo(() => ({
        backgroundColor: 'transparent',
        lineColor: '#2962FF',
        textColor: theme === 'dark' ? '#D9D9D9' : '#191919',
        areaTopColor: '#2962FF',
        areaBottomColor: 'rgba(41, 98, 255, 0.28)',
        upColor: '#FFFFFF',
        downColor: '#00bcd4',
    }), [theme])

    const intradayTimeScaleOptions = useMemo(() => ({
        timeVisible: true,
        secondsVisible: false,
        tickMarkFormatter: (time: number, tickMarkType: any, locale: any) => {
            return new Date(time * 1000).toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit',
                hour12: false
            });
        }
    }), [])

    const intradayLocalizationOptions = useMemo(() => ({
        timeFormatter: (timestamp: number) => {
            return new Date(timestamp * 1000).toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit',
                hour12: false
            });
        }
    }), [])

    const dailyTimeScaleOptions = useMemo(() => ({ timeVisible: false }), [])
    const dailyLocalizationOptions = useMemo(() => ({ dateFormat: 'yyyy-MM-dd' }), [])

    // Fetch Intraday Data
    const { data: intradayData, isLoading: isIntradayLoading } = useQuery({
        queryKey: ['intraday-equity'],
        queryFn: async () => {
            const res = await api.get('/analytics/intraday-equity')
            // TV Charts expects seconds for intraday
            return res.data.map((d: any) => ({
                time: new Date(d.timestamp).getTime() / 1000,
                value: d.close, // Fallback for Area
                open: d.open,
                high: d.high,
                low: d.low,
                close: d.close
            }))
        },
        refetchInterval: 60000 // Refresh every minute
    })

    // Fetch Historical Data (Daily)
    const { data: historicalData, isLoading: isHistoricalLoading } = useQuery({
        queryKey: ['daily-equity'],
        queryFn: async () => {
            const res = await api.get('/analytics/daily-equity')
            // TV Charts expects YYYY-MM-DD string for daily
            return res.data.map((d: any) => ({
                time: d.date,
                open: d.open,
                high: d.high,
                low: d.low,
                close: d.close
            }))
        },
        refetchInterval: 60000 // Refresh every minute
    })

    // Fetch Weekly Data
    const { data: weeklyData, isLoading: isWeeklyLoading } = useQuery({
        queryKey: ['weekly-equity'],
        queryFn: async () => {
            const res = await api.get('/analytics/weekly-equity')
            // TV Charts expects YYYY-MM-DD string for daily/weekly
            return res.data.map((d: any) => ({
                time: d.week_start_date,
                open: d.open,
                high: d.high,
                low: d.low,
                close: d.close
            }))
        }
    })

    const [ohlcValues, setOhlcValues] = useState<any>(null)

    const handleCrosshairMove = useCallback((data: any) => {
        setOhlcValues(data)
    }, [])

    const formatPrice = (price: number) => {
        try {
            return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(price);
        } catch (e) {
            return price?.toString() || 'N/A';
        }
    }

    const renderHeader = (title: string, description: string) => {
        if (ohlcValues) {
            const { open, high, low, close, value } = ohlcValues
            if (value !== undefined) {
                return (
                    <div className="flex flex-col space-y-1.5">
                        <CardTitle className="text-xs font-mono">
                            Value: {formatPrice(value)}
                        </CardTitle>
                    </div>
                )
            }
            return (
                <div className="flex flex-col space-y-1.5">
                    <CardTitle className="text-xs font-mono flex gap-4">
                        <span>O: {formatPrice(open)}</span>
                        <span>H: {formatPrice(high)}</span>
                        <span>L: {formatPrice(low)}</span>
                        <span>C: {formatPrice(close)}</span>
                    </CardTitle>
                </div>
            )
        }
        return (
            <div className="flex flex-col space-y-1.5">
                <CardTitle>{title}</CardTitle>
            </div>
        )
    }

    return (
        <div className="container mx-auto py-10">
            <h1 className="text-3xl font-bold mb-2">Equity Curve</h1>
            <p className="text-muted-foreground mb-8">Visualizing your account value growth over time.</p>

            <Tabs defaultValue="intraday" onValueChange={(v) => { setActiveTab(v); setOhlcValues(null); }} className="space-y-4">
                <TabsList>
                    <TabsTrigger value="intraday">Intraday</TabsTrigger>
                    <TabsTrigger value="daily">Daily</TabsTrigger>
                    <TabsTrigger value="weekly">Weekly</TabsTrigger>
                </TabsList>

                <TabsContent value="intraday" className="space-y-4">
                    <Card>
                        <CardHeader>
                            {renderHeader("Intraday Performance", "Minute-by-minute account value tracking for today.")}
                        </CardHeader>
                        <CardContent className="h-[500px] p-0 overflow-hidden rounded-b-lg">
                            {isIntradayLoading ? (
                                <div className="flex items-center justify-center h-full">
                                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                                </div>
                            ) : intradayData && intradayData.length > 0 ? (
                                <TVChart
                                    data={intradayData}
                                    chartType="Bar"
                                    colors={chartColors}
                                    timeScaleOptions={intradayTimeScaleOptions}
                                    localizationOptions={intradayLocalizationOptions}
                                    onCrosshairMove={handleCrosshairMove}
                                />
                            ) : (
                                <div className="flex items-center justify-center h-full text-muted-foreground">
                                    No intraday data available yet.
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="daily" className="space-y-4">
                    <Card>
                        <CardHeader>
                            {renderHeader("Daily Performance", "Daily account value closing prices.")}
                        </CardHeader>
                        <CardContent className="h-[500px] p-0 overflow-hidden rounded-b-lg">
                            {isHistoricalLoading ? (
                                <div className="flex items-center justify-center h-full">
                                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                                </div>
                            ) : historicalData && historicalData.length > 0 ? (
                                <TVChart
                                    data={historicalData}
                                    chartType="Bar"
                                    colors={chartColors}
                                    localizationOptions={dailyLocalizationOptions}
                                    timeScaleOptions={dailyTimeScaleOptions}
                                    onCrosshairMove={handleCrosshairMove}
                                />
                            ) : (
                                <div className="flex items-center justify-center h-full text-muted-foreground">
                                    No daily data available yet.
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="weekly" className="space-y-4">
                    <Card>
                        <CardHeader>
                            {renderHeader("Weekly Performance", "Weekly account value closing prices.")}
                        </CardHeader>
                        <CardContent className="h-[500px] p-0 overflow-hidden rounded-b-lg">
                            {isWeeklyLoading ? (
                                <div className="flex items-center justify-center h-full">
                                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                                </div>
                            ) : weeklyData && weeklyData.length > 0 ? (
                                <TVChart
                                    data={weeklyData}
                                    chartType="Bar"
                                    colors={chartColors}
                                    localizationOptions={dailyLocalizationOptions}
                                    timeScaleOptions={dailyTimeScaleOptions}
                                    onCrosshairMove={handleCrosshairMove}
                                />
                            ) : (
                                <div className="flex items-center justify-center h-full text-muted-foreground">
                                    No weekly data available yet.
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
    )
}
