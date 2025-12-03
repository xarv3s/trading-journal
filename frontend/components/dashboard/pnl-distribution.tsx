"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { DashboardMetrics } from "@/hooks/use-analytics"
import { Bar, BarChart, ResponsiveContainer, XAxis, YAxis, Tooltip } from "recharts"

interface PnLDistributionProps {
    data: DashboardMetrics['pnl_distribution']
}

export function PnLDistribution({ data }: PnLDistributionProps) {
    // Transform array of PnL values into histogram buckets
    const processData = (values: number[]) => {
        if (!values.length) return []

        // Binning logic for percentages (1% bins)
        const bins: { [key: string]: number } = {}
        values.forEach(val => {
            const bin = Math.floor(val)
            const label = `${bin}% to ${bin + 1}%`
            bins[label] = (bins[label] || 0) + 1
        })

        // Sort bins numerically
        return Object.entries(bins)
            .sort((a, b) => {
                const valA = parseInt(a[0].split('%')[0])
                const valB = parseInt(b[0].split('%')[0])
                return valA - valB
            })
            .map(([name, count]) => ({ name, count }))
    }

    const chartData = processData(data)

    return (
        <Card className="col-span-4 md:col-span-3">
            <CardHeader>
                <CardTitle>PnL Distribution (% Return)</CardTitle>
            </CardHeader>
            <CardContent>
                <div className="h-[350px]">
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={chartData}>
                            <XAxis
                                dataKey="name"
                                stroke="#888888"
                                fontSize={12}
                                tickLine={false}
                                axisLine={false}
                            />
                            <YAxis
                                stroke="#888888"
                                fontSize={12}
                                tickLine={false}
                                axisLine={false}
                            />
                            <Tooltip
                                contentStyle={{ backgroundColor: 'hsl(var(--background))', borderColor: 'hsl(var(--border))' }}
                                itemStyle={{ color: 'hsl(var(--foreground))' }}
                                cursor={{ fill: 'hsl(var(--muted))' }}
                            />
                            <Bar dataKey="count" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </CardContent>
        </Card>
    )
}
