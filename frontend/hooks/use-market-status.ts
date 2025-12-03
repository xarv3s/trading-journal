import { useQuery } from "@tanstack/react-query"
import api from "@/lib/api"

export interface MarketStatus {
    open: boolean
    reason?: string
    error?: string
}

export function useMarketStatus() {
    return useQuery({
        queryKey: ['market-status'],
        queryFn: async () => {
            const res = await api.get<MarketStatus>('/market-data/status')
            return res.data
        },
        refetchInterval: 60000, // Check every minute
    })
}
