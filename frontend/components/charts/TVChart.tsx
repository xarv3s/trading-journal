import { useEffect, useRef } from 'react'
import { createChart, ColorType, IChartApi, ISeriesApi, Time, AreaSeries, CandlestickSeries, LineSeries, BarSeries } from 'lightweight-charts'

interface TVChartProps {
    data: { time: Time; value?: number; open?: number; high?: number; low?: number; close?: number }[]
    chartType?: 'Area' | 'Candlestick' | 'Bar'
    overlays?: { data: { time: Time; value: number }[]; color: string }[]
    colors?: {
        backgroundColor?: string
        lineColor?: string
        textColor?: string
        areaTopColor?: string
        areaBottomColor?: string
        upColor?: string
        downColor?: string
    }
    timeScaleOptions?: any
    localizationOptions?: any
    onCrosshairMove?: (data: any) => void
}

const DEFAULT_OVERLAYS: any[] = [];
const DEFAULT_CHART_COLORS: any = {};
const DEFAULT_TIME_SCALE_OPTIONS: any = {};
const DEFAULT_LOCALIZATION_OPTIONS: any = {};

export const TVChart = (props: TVChartProps) => {
    const {
        data,
        chartType = 'Area',
        overlays = DEFAULT_OVERLAYS,
        colors: {
            backgroundColor = 'transparent',
            lineColor = '#2962FF',
            textColor = 'black',
            areaTopColor = '#2962FF',
            areaBottomColor = 'rgba(41, 98, 255, 0.28)',
            upColor = '#FFFFFF',
            downColor = '#00bcd4',
        } = DEFAULT_CHART_COLORS,
        timeScaleOptions = DEFAULT_TIME_SCALE_OPTIONS,
        localizationOptions = DEFAULT_LOCALIZATION_OPTIONS,
        onCrosshairMove,
    } = props

    const chartContainerRef = useRef<HTMLDivElement>(null)
    const chartRef = useRef<IChartApi | null>(null)
    const seriesRef = useRef<ISeriesApi<"Area"> | ISeriesApi<"Candlestick"> | ISeriesApi<"Bar"> | null>(null)
    const overlayRefs = useRef<ISeriesApi<"Line">[]>([])
    const legendRef = useRef<HTMLDivElement | null>(null)

    useEffect(() => {
        if (!chartContainerRef.current) return

        const chart = createChart(chartContainerRef.current, {
            layout: {
                background: { type: ColorType.Solid, color: backgroundColor },
                textColor,
            },
            width: chartContainerRef.current.clientWidth,
            height: 500,
            grid: {
                vertLines: { visible: false },
                horzLines: { visible: false },
            },
            handleScroll: {
                mouseWheel: true,
                pressedMouseMove: true,
                horzTouchDrag: true,
                vertTouchDrag: true,
            },
            handleScale: {
                axisPressedMouseMove: true,
                mouseWheel: true,
                pinch: true,
            },
            timeScale: {
                timeVisible: true,
                secondsVisible: false,
                rightOffset: 12,
                barSpacing: 10,
                ...timeScaleOptions,
            },
            localization: {
                ...localizationOptions
            },
        })
        chartRef.current = chart

        let newSeries;
        if (chartType === 'Candlestick') {
            newSeries = chart.addSeries(CandlestickSeries, {
                upColor,
                downColor,
                borderVisible: false,
                wickUpColor: upColor,
                wickDownColor: downColor,
            })
        } else if (chartType === 'Bar') {
            newSeries = chart.addSeries(BarSeries, {
                upColor,
                downColor,
                thinBars: true,
                openVisible: false,
            })
        } else {
            newSeries = chart.addSeries(AreaSeries, {
                lineColor,
                topColor: areaTopColor,
                bottomColor: areaBottomColor,
            })
        }
        seriesRef.current = newSeries

        // Validate and sort data
        if (Array.isArray(data)) {
            const validData = data
                .filter(d => {
                    if (!d || d.time === null || d.time === undefined) return false
                    if (chartType === 'Candlestick' || chartType === 'Bar') {
                        return (
                            typeof d.open === 'number' &&
                            typeof d.high === 'number' &&
                            typeof d.low === 'number' &&
                            typeof d.close === 'number'
                        )
                    }
                    return typeof d.value === 'number'
                })
                .map(d => {
                    let time = d.time;
                    if (typeof time === 'string' && time.includes('T')) {
                        time = time.split('T')[0];
                    }
                    return {
                        ...d,
                        time: (typeof time === 'number' ? Math.floor(time) : time) as Time
                    }
                })
                .sort((a, b) => {
                    const tA = typeof a.time === 'string' ? new Date(a.time).getTime() : a.time as number
                    const tB = typeof b.time === 'string' ? new Date(b.time).getTime() : b.time as number
                    return tA - tB
                })

            // Deduplicate by time
            const uniqueData = []
            const seenTimes = new Set()
            for (const item of validData) {
                if (!seenTimes.has(item.time)) {
                    seenTimes.add(item.time)
                    uniqueData.push(item)
                }
            }

            newSeries.setData(uniqueData)
        }

        // Add Overlays
        overlayRefs.current = []
        overlays.forEach(overlay => {
            const lineSeries = chart.addSeries(LineSeries, {
                color: overlay.color,
                lineWidth: 2,
                crosshairMarkerVisible: false,
            })
            lineSeries.setData(overlay.data)
            overlayRefs.current.push(lineSeries)
        })

        const handleResize = () => {
            if (chartContainerRef.current) {
                chart.applyOptions({ width: chartContainerRef.current.clientWidth })
            }
        }

        window.addEventListener('resize', handleResize)

        const getLastBar = () => {
            if (!data || data.length === 0) return null;
            return data[data.length - 1];
        }

        const updateLegend = (param: any) => {
            if (!onCrosshairMove) return;

            try {
                const validCrosshairPoint = !(
                    param === undefined || param.time === undefined || param.point.x < 0 || param.point.y < 0
                );

                let bar: any;
                if (validCrosshairPoint) {
                    bar = param.seriesData.get(newSeries);
                }

                if (!bar) {
                    bar = getLastBar();
                }

                if (bar) {
                    onCrosshairMove({
                        open: bar.open,
                        high: bar.high,
                        low: bar.low,
                        close: bar.close,
                        value: bar.value,
                        time: bar.time
                    });
                } else {
                    onCrosshairMove(null);
                }
            } catch (e) {
                console.error("Error updating legend:", e);
            }
        };

        chart.subscribeCrosshairMove(updateLegend);
        // Initial update
        updateLegend({ seriesData: new Map([[newSeries, getLastBar()]]), time: getLastBar()?.time });

        return () => {
            window.removeEventListener('resize', handleResize)
            chart.unsubscribeCrosshairMove(updateLegend); // Clean up crosshair listener
            chart.remove()
        }
    }, [data, chartType, backgroundColor, textColor, lineColor, areaTopColor, areaBottomColor, timeScaleOptions, localizationOptions, overlays, onCrosshairMove])

    return (
        <div ref={chartContainerRef} className="w-full h-full" />
    )
}
