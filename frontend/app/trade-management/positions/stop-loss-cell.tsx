"use client"

import { useState } from "react"
import { UnifiedTrade } from "@/types/trade"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Check, X, Pencil } from "lucide-react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import api from "@/lib/api"
import { toast } from "sonner"

interface StopLossCellProps {
    trade: UnifiedTrade
}

export function StopLossCell({ trade }: StopLossCellProps) {
    const [isEditing, setIsEditing] = useState(false)
    const [value, setValue] = useState(trade.stop_loss?.toString() || "")
    const queryClient = useQueryClient()

    const updateStopLoss = useMutation({
        mutationFn: async (newValue: number | null) => {
            const res = await api.patch(`/trades/${trade.id}`, {
                stop_loss: newValue
            })
            return res.data
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['trades'] })
            setIsEditing(false)
            toast.success("Stop Loss Updated")
        },
        onError: () => {
            toast.error("Failed to update Stop Loss")
        }
    })

    const handleSave = () => {
        const numValue = parseFloat(value)
        if (isNaN(numValue)) {
            toast.error("Invalid number")
            return
        }
        updateStopLoss.mutate(numValue)
    }

    const handleCancel = () => {
        setValue(trade.stop_loss?.toString() || "")
        setIsEditing(false)
    }

    if (isEditing) {
        return (
            <div className="flex items-center gap-1">
                <Input
                    type="number"
                    value={value}
                    onChange={(e) => setValue(e.target.value)}
                    className="w-20 h-8"
                    autoFocus
                />
                <Button variant="ghost" size="icon" className="h-8 w-8 text-green-600" onClick={handleSave}>
                    <Check className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="icon" className="h-8 w-8 text-red-600" onClick={handleCancel}>
                    <X className="h-4 w-4" />
                </Button>
            </div>
        )
    }

    return (
        <div className="group flex items-center gap-2">
            <span>{trade.stop_loss ? `₹${trade.stop_loss}` : "-"}</span>
            <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
                onClick={() => setIsEditing(true)}
            >
                <Pencil className="h-3 w-3" />
            </Button>
        </div>
    )
}
