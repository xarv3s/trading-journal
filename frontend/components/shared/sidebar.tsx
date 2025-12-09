"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { useState } from "react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { ModeToggle } from "@/components/mode-toggle"
import {
    LayoutDashboard,
    LineChart,
    ScrollText,
    Briefcase,
    ArrowLeftRight,
    ChevronLeft,
    ChevronRight,
    Settings,
    LogOut,
    ShoppingCart
} from "lucide-react"

interface SidebarProps {
    className?: string
}

export function Sidebar({ className }: SidebarProps) {
    const pathname = usePathname()
    const [isCollapsed, setIsCollapsed] = useState(false)

    const toggleSidebar = () => {
        setIsCollapsed(!isCollapsed)
    }

    const navItems = [
        {
            title: "Journal",
            items: [
                {
                    title: "Dashboard",
                    href: "/journal/dashboard",
                    icon: LayoutDashboard
                },
                {
                    title: "Equity Curve",
                    href: "/journal/equity",
                    icon: LineChart
                },
                {
                    title: "Trade Log",
                    href: "/journal/trades",
                    icon: ScrollText
                }
            ]
        },
        {
            title: "Trade Management",
            items: [
                {
                    title: "Open Positions",
                    href: "/trade-management/positions",
                    icon: Briefcase
                },
                {
                    title: "Transactions",
                    href: "/trade-management/transactions",
                    icon: ArrowLeftRight
                },
                {
                    title: "Orders",
                    href: "/trade-management/orders",
                    icon: ShoppingCart
                }
            ]
        }
    ]

    return (
        <div
            className={cn(
                "relative flex flex-col border-r bg-background transition-all duration-300 ease-in-out",
                isCollapsed ? "w-16" : "w-64",
                className
            )}
        >
            <div className="flex h-16 items-center justify-between px-4 border-b">
                {!isCollapsed && (
                    <Link href="/" className="hover:opacity-80 transition-opacity">
                        <span className="text-lg font-bold tracking-tight truncate">
                            Trading Platform
                        </span>
                    </Link>
                )}
                <Button
                    variant="ghost"
                    size="icon"
                    className={cn("ml-auto", isCollapsed && "mx-auto")}
                    onClick={toggleSidebar}
                >
                    {isCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
                </Button>
            </div>

            <div className="flex-1 overflow-y-auto py-4">
                <nav className="grid gap-1 px-2">
                    {navItems.map((section, index) => (
                        <div key={index} className="mb-4">
                            {!isCollapsed && (
                                <h3 className="mb-2 px-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                                    {section.title}
                                </h3>
                            )}
                            <div className="grid gap-1">
                                {section.items.map((item, itemIndex) => {
                                    const Icon = item.icon
                                    const isActive = pathname === item.href

                                    return (
                                        <Link
                                            key={itemIndex}
                                            href={item.href}
                                            className={cn(
                                                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground",
                                                isActive ? "bg-accent text-accent-foreground" : "transparent",
                                                isCollapsed && "justify-center px-2"
                                            )}
                                            title={isCollapsed ? item.title : undefined}
                                        >
                                            <Icon className="h-4 w-4" />
                                            {!isCollapsed && <span>{item.title}</span>}
                                        </Link>
                                    )
                                })}
                            </div>
                        </div>
                    ))}
                </nav>
            </div>

            <div className="border-t p-4">
                <div className={cn("flex items-center gap-3", isCollapsed ? "justify-center" : "justify-between")}>
                    <ModeToggle />
                    {!isCollapsed && (
                        <Button variant="ghost" size="icon" title="Settings">
                            <Settings className="h-4 w-4" />
                        </Button>
                    )}
                </div>
            </div>
        </div>
    )
}
