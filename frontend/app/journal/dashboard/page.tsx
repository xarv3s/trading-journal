"use client"

import { useDashboardMetrics } from "@/hooks/use-analytics"
import { KPICards } from "@/components/dashboard/kpi-cards"
import { PnLDistribution } from "@/components/dashboard/pnl-distribution"


export default function DashboardPage() {
  const { data, isLoading, error } = useDashboardMetrics()

  if (isLoading) {
    return <div className="flex items-center justify-center h-full">Loading...</div>
  }

  if (error) {
    return <div className="text-red-500">Error loading dashboard data</div>
  }

  if (!data) {
    return <div>No data available</div>
  }

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
      </div>
      <div className="space-y-4">
        <KPICards data={data.kpis} />
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
          <PnLDistribution data={data.pnl_distribution} />
        </div>
      </div>
    </div>
  )
}
