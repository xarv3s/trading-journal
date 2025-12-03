import useSWR, { mutate } from 'swr'
import api from '@/lib/api'

export interface Transaction {
    id: number
    date: string
    amount: number
    type: 'DEPOSIT' | 'WITHDRAWAL'
    notes?: string
}

const fetcher = (url: string) => api.get(url).then(res => res.data)

export function useTransactions() {
    const { data, error, isLoading } = useSWR<Transaction[]>('/transactions/', fetcher)

    const addTransaction = async (transaction: Omit<Transaction, 'id'>) => {
        await api.post('/transactions/', transaction)
        mutate('/transactions/')
    }

    const deleteTransaction = async (id: number) => {
        await api.delete(`/transactions/${id}`)
        mutate('/transactions/')
    }

    return {
        transactions: data,
        isLoading,
        error,
        addTransaction,
        deleteTransaction
    }
}
