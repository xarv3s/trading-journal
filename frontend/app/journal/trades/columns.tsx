"use client"

import { ColumnDef } from "@tanstack/react-table"
import { UnifiedTrade } from "@/types/trade"
import { ArrowUpDown } from "lucide-react"
import { Button } from "@/components/ui/button"

import { Checkbox } from "@/components/ui/checkbox"

export const columns: ColumnDef<UnifiedTrade>[] = [
    {
        id: "expander",
        header: () => null,
        cell: ({ row }) => {
            console.log("Row data:", row.original)
            return row.original.is_basket === 1 ? (
                <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => row.toggleExpanded()}
                >
                    {row.getIsExpanded() ? "▼" : "▶"}
                </Button>
            ) : null
        },
    },
    {
        id: "select",
        header: ({ table }) => (
            <Checkbox
                checked={table.getIsAllPageRowsSelected() || (table.getIsSomePageRowsSelected() && "indeterminate")}
                onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)}
                aria-label="Select all"
            />
        ),
        cell: ({ row }) => (
            <Checkbox
                checked={row.getIsSelected()}
                onCheckedChange={(value) => row.toggleSelected(!!value)}
                aria-label="Select row"
            />
        ),
        enableSorting: false,
        enableHiding: false,
    },
    {
        accessorKey: "entry_date",
        header: ({ column }) => {
            return (
                <Button
                    variant="ghost"
                    onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
                >
                    Date
                    <ArrowUpDown className="ml-2 h-4 w-4" />
                </Button>
            )
        },
        cell: ({ row }) => {
            const date = new Date(row.getValue("entry_date"))
            return <div>{date.toLocaleDateString('en-IN')}</div>
        },
    },
    {
        accessorKey: "trading_symbol",
        header: "Symbol",
    },
    {
        accessorKey: "type",
        header: "Type",
        cell: ({ row }) => {
            const type = row.getValue("type") as string
            if (!type) return <div>-</div>
            return (
                <div className={type === 'LONG' ? 'text-green-600' : 'text-red-600'}>
                    {type}
                </div>
            )
        }
    },
    {
        accessorKey: "qty",
        header: "Qty",
    },
    {
        accessorKey: "entry_price",
        header: "Entry Price",
        cell: ({ row }) => {
            if (row.original.is_basket === 1) return <div>-</div>
            const amount = parseFloat(row.getValue("entry_price"))
            return <div>₹{amount.toFixed(2)}</div>
        },
    },
    {
        accessorKey: "exit_price",
        header: "Exit Price",
        cell: ({ row }) => {
            if (row.original.is_basket === 1) return <div>-</div>
            const amount = row.getValue("exit_price")
            if (amount === null || amount === undefined) return <div>-</div>
            return <div>₹{parseFloat(amount as string).toFixed(2)}</div>
        },
    },
    {
        accessorKey: "pnl",
        header: ({ column }) => {
            return (
                <Button
                    variant="ghost"
                    onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
                >
                    PnL
                    <ArrowUpDown className="ml-2 h-4 w-4" />
                </Button>
            )
        },
        cell: ({ row }) => {
            const amount = parseFloat(row.getValue("pnl"))
            const color = amount > 0 ? "text-green-600" : amount < 0 ? "text-red-600" : ""
            return <div className={`font-medium ${color}`}>₹{amount.toFixed(2)}</div>
        },
    },
    {
        accessorKey: "status",
        header: "Status",
    },
]
