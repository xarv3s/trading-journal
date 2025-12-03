import { useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';

export const useSyncTrades = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async () => {
            const { data } = await api.post('/trades/sync');
            return data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['trades'] });
            queryClient.invalidateQueries({ queryKey: ['dashboard-metrics'] });
        },
    });
};
