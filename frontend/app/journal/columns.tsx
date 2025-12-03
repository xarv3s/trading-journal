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
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

interface JournalColumnsProps {
    onEdit: (trade: UnifiedTrade) => void
}

export const getColumns = ({ onEdit }: JournalColumnsProps): ColumnDef<UnifiedTrade>[] => [
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
            return <div>{date.toLocaleDateString()}</div>
        },
    },
    {
        accessorKey: "trading_symbol",
        header: "Symbol",
    },
    {
        accessorKey: "pnl",
        header: "PnL",
        cell: ({ row }) => {
            const amount = parseFloat(row.getValue("pnl"))
            const color = amount > 0 ? "text-green-600" : amount < 0 ? "text-red-600" : ""
            return <div className={`font-medium ${color}`}>₹{amount.toFixed(2)}</div>
        },
    },
    {
        accessorKey: "strategy_type",
        header: "Strategy",
    },
    {
        accessorKey: "setup_used",
        header: "Setup",
    },
    {
        accessorKey: "mistakes_made",
        header: "Mistakes",
        cell: ({ row }) => {
            const mistakes = row.getValue("mistakes_made") as string
            return <div className="text-red-500">{mistakes}</div>
        }
    },
    {
        id: "actions",
        cell: ({ row }) => {
            const trade = row.original

            return (
                <Button variant="ghost" className="h-8 w-8 p-0" onClick={() => onEdit(trade)}>
                    <span className="sr-only">Open menu</span>
                    <Pencil className="h-4 w-4" />
                </Button>
            )
        },
    },
]
