"use client"

import { ColumnDef } from "@tanstack/react-table"
import { UnifiedTrade } from "@/types/trade"
import { ArrowUpDown, MoreHorizontal, Pencil } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

interface ColumnsProps {
    onEdit: (trade: UnifiedTrade) => void
}

export const getColumns = ({ onEdit }: ColumnsProps): ColumnDef<UnifiedTrade>[] => [
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
        header: "Entry",
        cell: ({ row }) => {
            const amount = parseFloat(row.getValue("entry_price"))
            return <div>₹{amount.toFixed(2)}</div>
        },
    },
    {
        accessorKey: "exit_price",
        header: "Exit",
        cell: ({ row }) => {
            const val = row.getValue("exit_price")
            if (val === null || val === undefined) return <div>-</div>
            const amount = parseFloat(val as string)
            return <div>₹{amount.toFixed(2)}</div>
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
    {
        id: "actions",
        cell: ({ row }) => {
            const trade = row.original

            return (
                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <Button variant="ghost" className="h-8 w-8 p-0">
                            <span className="sr-only">Open menu</span>
                            <MoreHorizontal className="h-4 w-4" />
                        </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                        <DropdownMenuLabel>Actions</DropdownMenuLabel>
                        <DropdownMenuItem onClick={() => onEdit(trade)}>
                            <Pencil className="mr-2 h-4 w-4" />
                            Edit Trade
                        </DropdownMenuItem>
                    </DropdownMenuContent>
                </DropdownMenu>
            )
        },
    },
]
