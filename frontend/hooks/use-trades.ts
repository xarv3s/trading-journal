import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import { PaginatedTradesResponse, TradeUpdate, UnifiedTrade } from '@/types/trade';

interface GetTradesParams {
    page: number;
    pageSize: number;
    sortBy?: string;
    sortDesc?: boolean;
    status?: string;
}

export const useTrades = (params: GetTradesParams) => {
    return useQuery({
        queryKey: ['trades', params],
        queryFn: async () => {
            const { data } = await api.get<PaginatedTradesResponse>('/trades/', {
                params: {
                    skip: (params.page - 1) * params.pageSize,
                    limit: params.pageSize,
                    sort_by: params.sortBy,
                    sort_desc: params.sortDesc,
                    status: params.status,
                },
            });
            return data;
        },
    });
};

export const useUpdateTrade = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async ({ id, updates }: { id: string; updates: TradeUpdate }) => {
            const { data } = await api.patch<UnifiedTrade>(`/trades/${id}`, updates);
            return data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['trades'] });
        },
    });
};
