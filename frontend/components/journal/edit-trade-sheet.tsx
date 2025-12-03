"use client"

import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as z from "zod"
import {
    Sheet,
    SheetContent,
    SheetDescription,
    SheetHeader,
    SheetTitle,
} from "@/components/ui/sheet"
import {
    Form,
    FormControl,
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Button } from "@/components/ui/button"
import { UnifiedTrade } from "@/types/trade"
import { useUpdateTrade } from "@/hooks/use-trades"
import { useEffect } from "react"

const formSchema = z.object({
    notes: z.string().optional(),
    mistakes_made: z.string().optional(),
    setup_used: z.string().optional(),
    strategy_type: z.string().optional(),
})

interface EditTradeSheetProps {
    trade: UnifiedTrade | null
    open: boolean
    onOpenChange: (open: boolean) => void
}

export function EditTradeSheet({ trade, open, onOpenChange }: EditTradeSheetProps) {
    const updateTrade = useUpdateTrade()

    const form = useForm<z.infer<typeof formSchema>>({
        resolver: zodResolver(formSchema),
        defaultValues: {
            notes: "",
            mistakes_made: "",
            setup_used: "",
            strategy_type: "",
        },
    })

    useEffect(() => {
        if (trade) {
            form.reset({
                notes: trade.notes || "",
                mistakes_made: trade.mistakes_made || "",
                setup_used: trade.setup_used || "",
                strategy_type: trade.strategy_type || "",
            })
        }
    }, [trade, form])

    function onSubmit(values: z.infer<typeof formSchema>) {
        if (!trade) return

        updateTrade.mutate({
            id: trade.id,
            updates: values,
        }, {
            onSuccess: () => {
                onOpenChange(false)
            }
        })
    }

    return (
        <Sheet open={open} onOpenChange={onOpenChange}>
            <SheetContent className="sm:max-w-[540px]">
                <SheetHeader>
                    <SheetTitle>Edit Trade</SheetTitle>
                    <SheetDescription>
                        Make changes to your trade journal entry here. Click save when you're done.
                    </SheetDescription>
                </SheetHeader>
                <div className="py-4">
                    <Form {...form}>
                        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                            <FormField
                                control={form.control}
                                name="strategy_type"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>Strategy Type</FormLabel>
                                        <FormControl>
                                            <Input placeholder="e.g. TRENDING" {...field} />
                                        </FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />
                            <FormField
                                control={form.control}
                                name="setup_used"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>Setup Used</FormLabel>
                                        <FormControl>
                                            <Input placeholder="e.g. Breakout" {...field} />
                                        </FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />
                            <FormField
                                control={form.control}
                                name="mistakes_made"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>Mistakes Made</FormLabel>
                                        <FormControl>
                                            <Input placeholder="e.g. FOMO" {...field} />
                                        </FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />
                            <FormField
                                control={form.control}
                                name="notes"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>Notes</FormLabel>
                                        <FormControl>
                                            <Textarea
                                                placeholder="Detailed notes about the trade..."
                                                className="min-h-[150px]"
                                                {...field}
                                            />
                                        </FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />
                            <div className="flex justify-end pt-4">
                                <Button type="submit" disabled={updateTrade.isPending}>
                                    {updateTrade.isPending ? "Saving..." : "Save changes"}
                                </Button>
                            </div>
                        </form>
                    </Form>
                </div>
            </SheetContent>
        </Sheet>
    )
}
