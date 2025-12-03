"use client"

import { useState } from "react"
import { useTrades } from "@/hooks/use-trades"
import { getColumns } from "./columns"
import { DataTable } from "@/components/ui/data-table"
import { SortingState } from "@tanstack/react-table"
import { EditTradeSheet } from "@/components/journal/edit-trade-sheet"
import { UnifiedTrade } from "@/types/trade"

export default function JournalPage() {
    const [pagination, setPagination] = useState({
        pageIndex: 0,
        pageSize: 10,
    })
    const [sorting, setSorting] = useState<SortingState>([])
    const [editingTrade, setEditingTrade] = useState<UnifiedTrade | null>(null)
    const [isSheetOpen, setIsSheetOpen] = useState(false)

    const { data, isLoading, isError } = useTrades({
        page: pagination.pageIndex + 1,
        pageSize: pagination.pageSize,
        sortBy: sorting.length > 0 ? sorting[0].id : 'entry_date',
        sortDesc: sorting.length > 0 ? sorting[0].desc : true,
    })

    const handleEdit = (trade: UnifiedTrade) => {
        setEditingTrade(trade)
        setIsSheetOpen(true)
    }

    const columns = getColumns({ onEdit: handleEdit })

    if (isLoading) {
        return <div className="flex items-center justify-center h-full p-8">Loading journal...</div>
    }

    if (isError) {
        return <div className="text-red-500 p-8">Error loading journal.</div>
    }

    return (
        <div className="container mx-auto py-10">
            <h1 className="text-2xl font-bold mb-5">Trading Journal</h1>
            <DataTable
                columns={columns}
                data={data?.data || []}
                pageCount={data ? Math.ceil(data.total / data.page_size) : -1}
                pagination={pagination}
                onPaginationChange={setPagination}
                onSortingChange={setSorting}
            />
            <EditTradeSheet
                trade={editingTrade}
                open={isSheetOpen}
                onOpenChange={setIsSheetOpen}
            />
        </div>
    )
}
