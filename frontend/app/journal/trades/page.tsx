"use client"

import { useState } from "react"
import { useTrades } from "@/hooks/use-trades"
import { columns } from "./columns"
import { DataTable } from "@/components/ui/data-table"
import { SortingState } from "@tanstack/react-table"

export default function TradesPage() {
    const [pagination, setPagination] = useState({
        pageIndex: 0,
        pageSize: 10,
    })
    const [sorting, setSorting] = useState<SortingState>([])

    const { data, isLoading, isError } = useTrades({
        page: pagination.pageIndex + 1,
        pageSize: pagination.pageSize,
        sortBy: sorting.length > 0 ? sorting[0].id : 'entry_date',
        sortDesc: sorting.length > 0 ? sorting[0].desc : true,
        status: 'CLOSED'
    })

    if (isLoading) {
        return <div className="flex items-center justify-center h-full p-8">Loading trades...</div>
    }

    if (isError) {
        return <div className="text-red-500 p-8">Error loading trades.</div>
    }

    return (
        <div className="container mx-auto py-10">
            <h1 className="text-2xl font-bold mb-5">Trade List</h1>
            <DataTable
                columns={columns}
                data={data?.data || []}
                pageCount={data ? Math.ceil(data.total / data.page_size) : -1}
                pagination={pagination}
                onPaginationChange={setPagination}
                onSortingChange={setSorting}
            />
        </div>
    )
}
