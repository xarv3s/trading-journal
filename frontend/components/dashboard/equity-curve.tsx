"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { DashboardMetrics } from "@/hooks/use-analytics"
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"

interface EquityCurveProps {
    data: DashboardMetrics['equity_curve']
}

export function EquityCurve({ data }: EquityCurveProps) {
    return (
        <Card className="col-span-4">
            <CardHeader>
                <CardTitle>Equity Curve</CardTitle>
            </CardHeader>
            <CardContent className="pl-2">
                <div className="h-[350px]">
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={data}>
                            <XAxis
                                dataKey="date"
                                stroke="#888888"
                                fontSize={12}
                                tickLine={false}
                                axisLine={false}
                                tickFormatter={(value) => new Date(value).toLocaleDateString()}
                            />
                            <YAxis
                                stroke="#888888"
                                fontSize={12}
                                tickLine={false}
                                axisLine={false}
                                tickFormatter={(value) => `₹${value}`}
                            />
                            <Tooltip
                                contentStyle={{ backgroundColor: 'hsl(var(--background))', borderColor: 'hsl(var(--border))' }}
                                itemStyle={{ color: 'hsl(var(--foreground))' }}
                                labelFormatter={(value) => new Date(value).toLocaleDateString()}
                            />
                            <Line
                                type="monotone"
                                dataKey="account_value"
                                stroke="hsl(var(--primary))"
                                strokeWidth={2}
                                dot={false}
                            />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            </CardContent>
        </Card>
    )
}
