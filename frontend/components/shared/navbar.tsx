"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { ThemeProvider } from "@/components/theme-provider"
import { ModeToggle } from "@/components/mode-toggle"

export function Navbar() {
    const pathname = usePathname()

    return (
        <nav className="border-b">
            <div className="flex h-16 items-center px-4">
                <div className="mr-8 hidden md:flex">
                </div >
                <div className="ml-auto flex items-center space-x-4">
                    <ModeToggle />
                </div>
            </div >
        </nav >
    )
}
