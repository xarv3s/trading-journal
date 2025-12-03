import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';

export interface DashboardMetrics {
    kpis: {
        total_pnl: number;
        win_rate: number;
        profit_factor: number;
        avg_rr: number;
        max_drawdown: number;
        total_trades: number;
    };
    equity_curve: {
        date: string;
        account_value: number;
    }[];
    pnl_distribution: number[];
}

export const useDashboardMetrics = () => {
    return useQuery({
        queryKey: ['dashboard-metrics'],
        queryFn: async () => {
            const { data } = await api.get<DashboardMetrics>('/analytics/dashboard');
            return data;
        },
    });
};
