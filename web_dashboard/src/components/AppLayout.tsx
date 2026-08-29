import React, { ReactNode } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import {
  Scale,
  LayoutDashboard,
  Scan,
  Clock,
  CalendarCheck,
  Search,
} from 'lucide-react';

interface LayoutProps {
  children: ReactNode;
}

export default function AppLayout({ children }: LayoutProps) {
  const router = useRouter();

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    { name: 'Scan Product', href: '/scan', icon: Scan },
    { name: 'Scan History', href: '/inspections', icon: Clock },
    { name: 'Rules & Schedules', href: '/settings', icon: CalendarCheck },
  ];

  return (
    <div className="min-h-screen bg-[#F8FAFC] text-slate-800 flex font-sans antialiased">
      {/* Sidebar Navigation */}
      <aside className="w-64 bg-[#0A1128] text-white flex flex-col justify-between shrink-0 fixed inset-y-0 left-0 z-30 shadow-xl">
        <div>
          {/* Brand Logo Header */}
          <div className="p-6 flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-blue-600/20 border border-blue-500/40 flex items-center justify-center text-blue-400">
              <Scale className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-base font-black tracking-wider text-white leading-none">
                METROCHECK
              </h1>
              <p className="text-[10px] text-slate-400 font-medium mt-1">Legal Metrology Compliance</p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="px-3 space-y-1 text-xs font-semibold">
            {navigation.map((item) => {
              const isActive = router.pathname === item.href;
              const Icon = item.icon;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`flex items-center space-x-3.5 px-4 py-3 rounded-xl transition-all duration-150 ${
                    isActive
                      ? 'bg-[#2541B2] text-white font-bold shadow-md shadow-blue-900/40'
                      : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                  }`}
                >
                  <Icon className="w-4 h-4 shrink-0" />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Regulatory Footer Card */}
        <div className="p-4 m-4 rounded-xl bg-slate-900/60 border border-slate-800/80">
          <div className="w-7 h-7 rounded-lg bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400 mb-2">
            <Scale className="w-4 h-4" />
          </div>
          <p className="text-xs font-bold text-white leading-snug">
            Legal Metrology (Packaged Commodities) Rules, 2011
          </p>
        </div>
      </aside>

      {/* Main Content Viewport */}
      <div className="pl-64 flex-1 flex flex-col min-w-0">
        {/* Top Header */}
        <header className="h-16 bg-white border-b border-slate-100 px-8 flex items-center justify-between sticky top-0 z-20 shadow-sm">
          <div className="relative w-96">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search anything..."
              className="w-full bg-slate-50 border border-slate-200/80 rounded-xl pl-10 pr-4 py-2 text-xs text-slate-800 placeholder:text-slate-400 focus:outline-none focus:bg-white focus:border-blue-600 transition"
            />
          </div>
        </header>

        {/* Dynamic Outlet */}
        <main className="p-8 flex-1">{children}</main>
      </div>
    </div>
  );
}