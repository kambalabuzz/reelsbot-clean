"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { UserButton } from "@clerk/nextjs";
import { 
  Video, LayoutGrid, Film, Settings, CreditCard, 
  HelpCircle, ChevronLeft, Menu, Plus, Sparkles, TrendingUp, Copy
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useState } from "react";

const navItems = [
  { href: "/dashboard", icon: LayoutGrid, label: "Dashboard" },
  { href: "/dashboard/series", icon: Video, label: "Series" },
  { href: "/dashboard/videos", icon: Film, label: "Videos" },
  { href: "/dashboard/trends", icon: TrendingUp, label: "Trends" },
  { href: "/dashboard/clone", icon: Copy, label: "Clone" },
  { href: "/dashboard/create", icon: Sparkles, label: "AI Director" },
  { href: "/dashboard/settings", icon: Settings, label: "Settings" },
  { href: "/dashboard/billing", icon: CreditCard, label: "Billing" },
];

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="min-h-screen bg-background">
      {/* Sidebar */}
      <aside
        className={cn(
          "fixed left-0 top-0 z-40 h-screen border-r bg-card transition-all duration-300",
          collapsed ? "w-16" : "w-64"
        )}
      >
        {/* Logo */}
        <div className="flex h-16 items-center justify-between border-b px-4">
          {!collapsed && (
            <Link href="/dashboard" className="flex items-center gap-2">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <Video className="w-5 h-5 text-white" />
              </div>
              <span className="font-bold text-lg">ReelsBot</span>
            </Link>
          )}
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setCollapsed(!collapsed)}
            className={cn(collapsed && "mx-auto")}
          >
            {collapsed ? <Menu className="h-5 w-5" /> : <ChevronLeft className="h-5 w-5" />}
          </Button>
        </div>

        {/* Create Button */}
        <div className="p-4">
          <Link href="/dashboard/series/create">
            <Button className={cn("w-full gap-2", collapsed && "px-0")}>
              <Plus className="h-5 w-5" />
              {!collapsed && "New Series"}
            </Button>
          </Link>
        </div>

        {/* Navigation */}
        <nav className="space-y-1 px-2">
          {navItems.map((item) => {
            const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 transition-colors",
                  isActive
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground",
                  collapsed && "justify-center px-2"
                )}
              >
                <item.icon className="h-5 w-5 flex-shrink-0" />
                {!collapsed && <span>{item.label}</span>}
              </Link>
            );
          })}
        </nav>

        {/* Bottom section */}
        <div className="absolute bottom-0 left-0 right-0 border-t p-4">
          <Link
            href="/dashboard/help"
            className={cn(
              "flex items-center gap-3 rounded-lg px-3 py-2 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors",
              collapsed && "justify-center px-2"
            )}
          >
            <HelpCircle className="h-5 w-5" />
            {!collapsed && <span>Help & Support</span>}
          </Link>
          
          {/* Upgrade banner */}
          {!collapsed && (
            <div className="mt-4 rounded-lg bg-gradient-to-r from-purple-500/20 to-pink-500/20 p-4">
              <div className="flex items-center gap-2 mb-2">
                <Sparkles className="h-5 w-5 text-primary" />
                <span className="font-medium">Upgrade</span>
              </div>
              <p className="text-xs text-muted-foreground mb-3">
                Get more videos and features
              </p>
              <Link href="/dashboard/billing">
                <Button size="sm" className="w-full">
                  View Plans
                </Button>
              </Link>
            </div>
          )}
        </div>
      </aside>

      {/* Main content */}
      <div className={cn("transition-all duration-300", collapsed ? "ml-16" : "ml-64")}>
        {/* Top bar */}
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b bg-background/95 backdrop-blur px-6">
          <div>
            <h1 className="text-lg font-semibold">
              {navItems.find((item) => pathname.startsWith(item.href))?.label || "Dashboard"}
            </h1>
          </div>
          <div className="flex items-center gap-4">
            <UserButton afterSignOutUrl="/" />
          </div>
        </header>

        {/* Page content */}
        <main className="p-6">{children}</main>
      </div>
    </div>
  );
}
