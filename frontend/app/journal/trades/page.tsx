"use client"

import { useState } from "react"
import { useTrades } from "@/hooks/use-trades"
import { columns } from "./columns"
import { DataTable } from "@/components/ui/data-table"
import { SortingState, RowSelectionState } from "@tanstack/react-table"

export default function TradesPage() {
    const [pagination, setPagination] = useState({
        pageIndex: 0,
        pageSize: 10,
    })
    const [sorting, setSorting] = useState<SortingState>([])
    const [rowSelection, setRowSelection] = useState<RowSelectionState>({})

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
            <div className="flex justify-between items-center mb-5">
                <h1 className="text-2xl font-bold">Trade Log</h1>
            </div>
            <DataTable
                columns={columns}
                data={data?.data || []}
                pageCount={data ? Math.ceil(data.total / data.page_size) : -1}
                pagination={pagination}
                onPaginationChange={setPagination}
                onSortingChange={setSorting}
                rowSelection={rowSelection}
                onRowSelectionChange={setRowSelection}
                getRowId={(row) => row.id}
                renderSubComponent={({ row }) => {
                    const constituents = row.original.constituents
                    if (!constituents || constituents.length === 0) return <div>No constituents</div>

                    return (
                        <div className="p-4 bg-muted/50 rounded-md">
                            <h4 className="font-semibold mb-2">Constituents</h4>
                            <div className="grid grid-cols-6 gap-4 text-sm font-medium text-muted-foreground mb-2">
                                <div>Symbol</div>
                                <div>Type</div>
                                <div>Qty</div>
                                <div>Entry Price</div>
                                <div>Exit Price</div>
                                <div>PnL</div>
                            </div>
                            {constituents.map((c: any) => (
                                <div key={c.id} className="grid grid-cols-6 gap-4 text-sm items-center py-1 border-b last:border-0">
                                    <div>{c.symbol}</div>
                                    <div className={c.type === 'LONG' ? 'text-green-600' : 'text-red-600'}>{c.type}</div>
                                    <div>{c.qty}</div>
                                    <div>₹{c.avg_price?.toFixed(2)}</div>
                                    <div>{c.exit_price ? `₹${c.exit_price.toFixed(2)}` : '-'}</div>
                                    <div className={c.pnl > 0 ? 'text-green-600' : 'text-red-600'}>
                                        {c.pnl ? `₹${c.pnl.toFixed(2)}` : '-'}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )
                }}
            />
        </div>
    )
}
