"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { DashboardMetrics } from "@/hooks/use-analytics"
import { ArrowUpRight, ArrowDownRight, IndianRupee, Activity, Percent, TrendingUp } from "lucide-react"

interface KPICardsProps {
    data: DashboardMetrics['kpis']
}

export function KPICards({ data }: KPICardsProps) {
    const kpis = [
        {
            title: "Total PnL",
            value: `₹${data.total_pnl.toLocaleString()}`,
            icon: IndianRupee,
            description: "Net Profit/Loss",
        },
        {
            title: "Win Rate",
            value: `${data.win_rate.toFixed(1)}%`,
            icon: Percent,
            description: "Percentage of winning trades",
        },
        {
            title: "Profit Factor",
            value: data.profit_factor.toFixed(2),
            icon: TrendingUp,
            description: "Gross Profit / Gross Loss",
        },
        {
            title: "Avg R:R",
            value: data.avg_rr.toFixed(2),
            icon: Activity,
            description: "Average Risk:Reward Ratio",
        },
    ]

    return (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {kpis.map((kpi) => (
                <Card key={kpi.title}>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">
                            {kpi.title}
                        </CardTitle>
                        <kpi.icon className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{kpi.value}</div>
                        <p className="text-xs text-muted-foreground">
                            {kpi.description}
                        </p>
                    </CardContent>
                </Card>
            ))}
        </div>
    )
}
