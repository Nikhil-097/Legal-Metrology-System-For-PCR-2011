import React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { LayoutDashboard, ScanLine, FileText, Scale, ShieldCheck } from 'lucide-react';

export default function Sidebar() {
  const router = useRouter();

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    { name: 'Scan & Verify Package', href: '/scan', icon: ScanLine },
    { name: 'Inspection Records', href: '/inspections', icon: FileText },
    { name: 'Rule Matrices (PCR 2011)', href: '/settings', icon: Scale },
  ];

  return (
    <aside className="fixed inset-y-0 left-0 w-64 bg-[#0F172A] border-r border-slate-800 flex flex-col z-30">
      <div className="p-6 border-b border-slate-800/80">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-blue-600/20 border border-blue-500/30 rounded-xl text-blue-400">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-sm font-black text-white tracking-wide">Legal Metrology</h1>
            <p className="text-[10px] text-slate-400 font-medium">Digital Verification Vault</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 p-4 space-y-1.5 overflow-y-auto">
        {navigation.map((item) => {
          const isActive = router.pathname === item.href;
          const Icon = item.icon;
          const linkClass = isActive
            ? 'bg-blue-600 text-white shadow-sm shadow-blue-600/30'
            : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60';
          const iconClass = isActive ? 'text-white' : 'text-slate-400';

          return (
            <Link
              key={item.name}
              href={item.href}
              className={'flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all duration-150 ' + linkClass}
            >
              <Icon className={'w-4 h-4 ' + iconClass} />
              <span>{item.name}</span>
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-slate-800/80">
        <div className="p-3 bg-slate-900/60 rounded-xl border border-slate-800 flex items-center justify-between">
          <div>
            <p className="text-xs font-bold text-white">Inspector #402</p>
            <p className="text-[10px] text-emerald-400 font-medium">National Node Synced</p>
          </div>
          <div className="w-2 h-2 rounded-full bg-emerald-500 ring-4 ring-emerald-500/20" />
        </div>
      </div>
    </aside>
  );
}