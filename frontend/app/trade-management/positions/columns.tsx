
"use client"

import { ColumnDef } from "@tanstack/react-table"
import { UnifiedTrade } from "@/types/trade"
import { ArrowUpDown, ChevronRight, MoreHorizontal } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Badge } from "@/components/ui/badge"
import { StopLossCell } from "./stop-loss-cell"
import { cn } from "@/lib/utils"
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

export const columns: ColumnDef<UnifiedTrade>[] = [
    {
        id: "expander",
        header: () => null,
        cell: ({ row }) => {
            return row.original.is_basket === 1 ? (
                <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6 p-0 hover:bg-transparent text-muted-foreground"
                    onClick={() => row.toggleExpanded()}
                >
                    <ChevronRight className={cn(
                        "h-4 w-4 transition-transform duration-200",
                        row.getIsExpanded() && "rotate-90"
                    )} />
                </Button>
            ) : null
        },
        size: 30,
    },
    {
        id: "select",
        header: ({ table }) => (
            <Checkbox
                checked={table.getIsAllPageRowsSelected() || (table.getIsSomePageRowsSelected() && "indeterminate")}
                onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)}
                aria-label="Select all"
                className="translate-y-[2px] border-muted-foreground/50 data-[state=checked]:bg-blue-600 data-[state=checked]:border-blue-600"
            />
        ),
        cell: ({ row }) => (
            <Checkbox
                checked={row.getIsSelected()}
                onCheckedChange={(value) => row.toggleSelected(!!value)}
                aria-label="Select row"
                className="translate-y-[2px] border-muted-foreground/50 data-[state=checked]:bg-blue-600 data-[state=checked]:border-blue-600"
            />
        ),
        enableSorting: false,
        enableHiding: false,
        size: 30,
    },
    {
        accessorKey: "order_type",
        header: ({ column }) => <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium">Product</div>,
        cell: ({ row }) => {
            const product = row.getValue("order_type") as string
            if (row.original.is_basket === 1) {
                return (
                    <Badge variant="outline" className="text-[10px] px-1.5 py-0 h-5 font-normal border-purple-500/30 text-purple-400 bg-purple-500/10 hover:bg-purple-500/20 uppercase">
                        BASKET
                    </Badge>
                )
            }
            return (
                <Badge variant="outline" className="text-[10px] px-1.5 py-0 h-5 font-normal border-blue-500/30 text-blue-400 bg-blue-500/10 hover:bg-blue-500/20 uppercase">
                    {product || 'NRML'}
                </Badge>
            )
        },
        size: 80,
    },
    {
        accessorKey: "trading_symbol",
        header: ({ column }) => <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium">Instrument</div>,
        cell: ({ row }) => (
            <div className="flex items-center gap-2">
                <span className="font-medium text-sm text-foreground">{row.getValue("trading_symbol")}</span>
                <span className="text-[10px] text-muted-foreground uppercase">{row.original.exchange}</span>
            </div>
        )
    },
    {
        accessorKey: "qty",
        header: ({ column }) => <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium text-right">Qty.</div>,
        cell: ({ row }) => {
            const qty = row.getValue("qty") as number
            const type = row.original.type

            if (row.original.is_basket === 1) {
                return <div className="font-mono text-sm text-right text-foreground">
                    {qty}
                </div>
            }

            const isLong = type === 'LONG'
            return <div className={cn("font-mono text-sm text-right", isLong ? "text-blue-400" : "text-red-400")}>
                {isLong ? "+" : "-"}{qty}
            </div>
        },
        size: 80,
    },
    {
        accessorKey: "entry_price",
        header: ({ column }) => <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium text-right">Avg.</div>,
        cell: ({ row }) => {
            if (row.original.is_basket === 1) return <div className="text-muted-foreground text-sm text-right">-</div>
            const amount = parseFloat(row.getValue("entry_price"))
            return <div className="font-mono text-sm text-right text-foreground">{amount.toFixed(2)}</div>
        },
        size: 100,
    },
    {
        accessorKey: "ltp",
        header: ({ column }) => <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium text-right">LTP</div>,
        cell: ({ row }) => {
            const amount = row.getValue("ltp")
            if (amount === null || amount === undefined) return <div className="text-muted-foreground text-sm text-right">-</div>
            return <div className="font-mono text-sm text-right text-foreground">{Number(amount).toFixed(2)}</div>
        },
        size: 100,
    },
    {
        accessorKey: "margin_blocked",
        header: ({ column }) => <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium text-right">Margin</div>,
        cell: ({ row }) => {
            const amount = row.original.margin_blocked
            if (amount === undefined || amount === null) return <div className="text-muted-foreground text-sm text-right">-</div>
            return <div className="font-mono text-sm text-right text-foreground">₹{amount.toLocaleString('en-IN', { maximumFractionDigits: 2 })}</div>
        },
        size: 100,
    },
    {
        accessorKey: "gross_exposure",
        header: ({ column }) => <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium text-right">Exposure</div>,
        cell: ({ row }) => {
            const amount = row.original.gross_exposure
            if (amount === undefined || amount === null) return <div className="text-muted-foreground text-sm text-right">-</div>
            return <div className="font-mono text-sm text-right text-foreground">₹{amount.toLocaleString('en-IN', { maximumFractionDigits: 2 })}</div>
        },
        size: 100,
    },
    {
        accessorKey: "realized_pnl",
        header: ({ column }) => <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium text-right">Realized P&L</div>,
        cell: ({ row }) => {
            const amount = row.original.realized_pnl
            if (amount === undefined || amount === null) return <div className="text-muted-foreground text-sm text-right">-</div>
            const color = amount > 0 ? "text-green-500" : amount < 0 ? "text-red-500" : "text-muted-foreground"
            return <div className={cn("font-mono font-medium text-sm text-right", color)}>
                {amount > 0 ? "+" : ""}₹{amount.toFixed(2)}
            </div>
        },
        size: 120,
    },
    {
        accessorKey: "pnl",
        header: ({ column }) => <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium text-right">P&L</div>,
        cell: ({ row }) => {
            const amount = parseFloat(row.getValue("pnl"))
            const color = amount > 0 ? "text-green-500" : amount < 0 ? "text-red-500" : "text-muted-foreground"
            return <div className={cn("font-mono font-medium text-sm text-right", color)}>
                {amount > 0 ? "+" : ""}₹{amount.toFixed(2)}
            </div>
        },
        size: 120,
    },
    {
        id: "chg",
        header: ({ column }) => <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium text-right">Chg.</div>,
        cell: ({ row }) => {
            const ltp = row.original.ltp
            const entry = row.original.entry_price
            const type = row.original.type

            if (!ltp || !entry || row.original.is_basket === 1) return <div className="text-muted-foreground text-sm text-right">-</div>

            let chg = 0
            if (type === 'LONG') {
                chg = ((ltp - entry) / entry) * 100
            } else {
                chg = ((entry - ltp) / entry) * 100
            }

            const color = chg > 0 ? "text-green-500" : chg < 0 ? "text-red-500" : "text-muted-foreground"
            return <div className={cn("font-mono text-sm text-right", color)}>
                {chg.toFixed(2)}%
            </div>
        },
        size: 80,
    },
    {
        accessorKey: "stop_loss",
        header: ({ column }) => <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium text-right pr-8">SL</div>,
        cell: ({ row }) => <div className="flex justify-end"><StopLossCell trade={row.original} /></div>,
        size: 100,
    },
    {
        id: "actions",
        cell: ({ row, table }) => {
            return (
                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <Button variant="ghost" className="h-8 w-8 p-0 text-muted-foreground hover:text-foreground">
                            <span className="sr-only">Open menu</span>
                            <MoreHorizontal className="h-4 w-4" />
                        </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                        <DropdownMenuLabel>Actions</DropdownMenuLabel>
                        <DropdownMenuItem onClick={() => navigator.clipboard.writeText(row.original.id)}>
                            Copy ID
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem>View Details</DropdownMenuItem>
                        {row.original.is_basket !== 1 && (
                            <DropdownMenuItem onClick={() => (table.options.meta as any)?.handleAddToBasket(row.original.id)}>
                                Add to Basket
                            </DropdownMenuItem>
                        )}
                        <DropdownMenuItem className="text-red-600">Exit Position</DropdownMenuItem>
                    </DropdownMenuContent>
                </DropdownMenu>
            )
        },
        size: 40,
    },
]
