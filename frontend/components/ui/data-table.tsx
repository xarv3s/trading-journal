"use client"

import {
    ColumnDef,
    flexRender,
    getCoreRowModel,
    useReactTable,
    getPaginationRowModel,
    SortingState,
    getSortedRowModel,
    ColumnFiltersState,
    getFilteredRowModel,
    RowSelectionState,
    OnChangeFn,
    getExpandedRowModel,
    ExpandedState,
} from "@tanstack/react-table"

import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useState, Fragment } from "react"

interface DataTableProps<TData, TValue> {
    columns: ColumnDef<TData, TValue>[]
    data: TData[]
    pageCount?: number
    pagination?: {
        pageIndex: number
        pageSize: number
    }
    onPaginationChange?: (pagination: { pageIndex: number; pageSize: number }) => void
    onSortingChange?: (sorting: SortingState) => void
    rowSelection?: RowSelectionState
    onRowSelectionChange?: OnChangeFn<RowSelectionState>
    getRowId?: (originalRow: TData, index: number, parent?: any) => string
    renderSubComponent?: (props: { row: any }) => React.ReactElement
    hidePagination?: boolean
    meta?: any
}

export function DataTable<TData, TValue>({
    columns,
    data,
    pageCount,
    pagination,
    onPaginationChange,
    onSortingChange,
    rowSelection,
    onRowSelectionChange,
    getRowId,
    renderSubComponent,
    hidePagination = false,
    meta,
}: DataTableProps<TData, TValue>) {
    const [sorting, setSorting] = useState<SortingState>([])
    const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([])
    const [expanded, setExpanded] = useState<ExpandedState>({})

    const table = useReactTable({
        data,
        columns,
        getCoreRowModel: getCoreRowModel(),
        getRowId, // Use custom getRowId if provided
        // Pagination
        getPaginationRowModel: getPaginationRowModel(),
        manualPagination: !!pageCount,
        pageCount: pageCount ?? -1,
        onPaginationChange: (updater) => {
            if (typeof updater === 'function' && pagination) {
                const newPagination = updater(pagination)
                onPaginationChange?.(newPagination)
            }
        },
        // Sorting
        onSortingChange: (updater) => {
            if (typeof updater === 'function') {
                const newSorting = updater(sorting)
                setSorting(newSorting)
                onSortingChange?.(newSorting)
            } else {
                setSorting(updater)
                onSortingChange?.(updater)
            }
        },
        manualSorting: !!onSortingChange,
        // Row Selection
        onRowSelectionChange: onRowSelectionChange,
        enableRowSelection: !!rowSelection, // Only enable if rowSelection is passed
        // Expansion
        getExpandedRowModel: getExpandedRowModel(),
        onExpandedChange: setExpanded,
        // State
        state: {
            sorting,
            columnFilters,
            pagination: pagination,
            rowSelection: rowSelection || {},
            expanded,
        },
        meta: meta,
    })

    return (
        <div>
            <div className="rounded-md border">
                <Table>
                    <TableHeader>
                        {table.getHeaderGroups().map((headerGroup) => (
                            <TableRow key={headerGroup.id}>
                                {headerGroup.headers.map((header) => {
                                    return (
                                        <TableHead key={header.id}>
                                            {header.isPlaceholder
                                                ? null
                                                : flexRender(
                                                    header.column.columnDef.header,
                                                    header.getContext()
                                                )}
                                        </TableHead>
                                    )
                                })}
                            </TableRow>
                        ))}
                    </TableHeader>
                    <TableBody>
                        {table.getRowModel().rows?.length ? (
                            table.getRowModel().rows.map((row) => (
                                <Fragment key={row.id}>
                                    <TableRow
                                        data-state={row.getIsSelected() && "selected"}
                                    >
                                        {row.getVisibleCells().map((cell) => (
                                            <TableCell key={cell.id}>
                                                {flexRender(cell.column.columnDef.cell, cell.getContext())}
                                            </TableCell>
                                        ))}
                                    </TableRow>
                                    {row.getIsExpanded() && renderSubComponent && (
                                        <TableRow>
                                            <TableCell colSpan={row.getVisibleCells().length}>
                                                {renderSubComponent({ row })}
                                            </TableCell>
                                        </TableRow>
                                    )}
                                </Fragment>
                            ))
                        ) : (
                            <TableRow>
                                <TableCell colSpan={columns.length} className="h-24 text-center">
                                    No results.
                                </TableCell>
                            </TableRow>
                        )}
                    </TableBody>
                </Table>
            </div>
            {!hidePagination && (
                <div className="flex items-center justify-end space-x-2 py-4">
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => table.previousPage()}
                        disabled={!table.getCanPreviousPage()}
                    >
                        Previous
                    </Button>
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => table.nextPage()}
                        disabled={!table.getCanNextPage()}
                    >
                        Next
                    </Button>
                </div>
            )}
        </div>
    )
}
