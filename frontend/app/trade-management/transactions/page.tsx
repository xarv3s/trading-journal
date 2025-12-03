"use client"

import { useState } from "react"
import { useTransactions, Transaction } from "@/hooks/use-transactions"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Trash2, IndianRupee } from "lucide-react"
import { format } from "date-fns"

export default function CapitalPage() {
    const { transactions, addTransaction, deleteTransaction, isLoading } = useTransactions()
    const [date, setDate] = useState("")
    const [amount, setAmount] = useState("")
    const [type, setType] = useState<"DEPOSIT" | "WITHDRAWAL">("DEPOSIT")
    const [notes, setNotes] = useState("")

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!date || !amount) return

        await addTransaction({
            date,
            amount: parseFloat(amount),
            type,
            notes
        })

        // Reset form
        setAmount("")
        setNotes("")
    }

    if (isLoading) return <div>Loading...</div>

    return (
        <div className="flex-1 space-y-4 p-8 pt-6">
            <div className="flex items-center justify-between space-y-2">
                <h2 className="text-3xl font-bold tracking-tight">Transactions</h2>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
                <Card>
                    <CardHeader>
                        <CardTitle>Add Transaction</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <label className="text-sm font-medium">Date</label>
                                    <Input
                                        type="date"
                                        value={date}
                                        onChange={(e) => setDate(e.target.value)}
                                        required
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-sm font-medium">Type</label>
                                    <Select value={type} onValueChange={(v: "DEPOSIT" | "WITHDRAWAL") => setType(v)}>
                                        <SelectTrigger>
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="DEPOSIT">Deposit</SelectItem>
                                            <SelectItem value="WITHDRAWAL">Withdrawal</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                            </div>

                            <div className="space-y-2">
                                <label className="text-sm font-medium">Amount</label>
                                <div className="relative">
                                    <IndianRupee className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                                    <Input
                                        type="number"
                                        placeholder="0.00"
                                        className="pl-8"
                                        value={amount}
                                        onChange={(e) => setAmount(e.target.value)}
                                        required
                                    />
                                </div>
                            </div>

                            <div className="space-y-2">
                                <label className="text-sm font-medium">Notes</label>
                                <Input
                                    placeholder="Optional notes"
                                    value={notes}
                                    onChange={(e) => setNotes(e.target.value)}
                                />
                            </div>

                            <Button type="submit" className="w-full">
                                Add Transaction
                            </Button>
                        </form>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle>Summary</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            <div className="flex justify-between items-center">
                                <span className="text-sm font-medium">Total Deposits</span>
                                <span className="text-xl font-bold text-green-600">
                                    ₹{transactions?.filter((t: Transaction) => t.type === 'DEPOSIT').reduce((sum: number, t: Transaction) => sum + t.amount, 0).toLocaleString()}
                                </span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-sm font-medium">Total Withdrawals</span>
                                <span className="text-xl font-bold text-red-600">
                                    ₹{transactions?.filter((t: Transaction) => t.type === 'WITHDRAWAL').reduce((sum: number, t: Transaction) => sum + t.amount, 0).toLocaleString()}
                                </span>
                            </div>
                            <div className="pt-4 border-t flex justify-between items-center">
                                <span className="text-sm font-medium">Net Capital Added</span>
                                <span className="text-2xl font-bold">
                                    ₹{(
                                        (transactions?.filter((t: Transaction) => t.type === 'DEPOSIT').reduce((sum: number, t: Transaction) => sum + t.amount, 0) || 0) -
                                        (transactions?.filter((t: Transaction) => t.type === 'WITHDRAWAL').reduce((sum: number, t: Transaction) => sum + t.amount, 0) || 0)
                                    ).toLocaleString()}
                                </span>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>Transaction History</CardTitle>
                </CardHeader>
                <CardContent>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Date</TableHead>
                                <TableHead>Type</TableHead>
                                <TableHead>Amount</TableHead>
                                <TableHead>Notes</TableHead>
                                <TableHead className="w-[50px]"></TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {transactions?.map((t: Transaction) => (
                                <TableRow key={t.id}>
                                    <TableCell>{format(new Date(t.date), 'dd MMM yyyy')}</TableCell>
                                    <TableCell>
                                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${t.type === 'DEPOSIT'
                                            ? 'bg-green-100 text-green-800'
                                            : 'bg-red-100 text-red-800'
                                            }`}>
                                            {t.type}
                                        </span>
                                    </TableCell>
                                    <TableCell className="font-medium">
                                        ₹{t.amount.toLocaleString()}
                                    </TableCell>
                                    <TableCell>{t.notes}</TableCell>
                                    <TableCell>
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            onClick={() => deleteTransaction(t.id)}
                                        >
                                            <Trash2 className="h-4 w-4 text-red-500" />
                                        </Button>
                                    </TableCell>
                                </TableRow>
                            ))}
                            {(!transactions || transactions.length === 0) && (
                                <TableRow>
                                    <TableCell colSpan={5} className="text-center text-muted-foreground">
                                        No transactions found
                                    </TableCell>
                                </TableRow>
                            )}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>
        </div>
    )
}
