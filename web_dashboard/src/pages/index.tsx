import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { ArrowUpRight, Shield, Scan, Layers, BarChart3, Activity } from 'lucide-react';

export default function Home() {
  const [time, setTime] = useState<string>('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTime(
        now.toLocaleTimeString('en-US', {
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
          hour12: false,
        })
      );
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="relative min-h-screen bg-[#070708] text-white selection:bg-red-600 selection:text-white font-sans overflow-x-hidden">
      {/* Background Ambience: Deep Red Glow & Refraction Glass Effect */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-[-10%] left-[20%] w-[550px] h-[550px] bg-red-600/25 rounded-full blur-[140px] opacity-75 animate-pulse" />
        <div className="absolute top-[30%] right-[10%] w-[450px] h-[450px] bg-red-800/15 rounded-full blur-[160px]" />
        {/* Subtle Diagonal Grid Geometry */}
        <div className="absolute inset-0 bg-[radial-gradient(#1f1f23_1px,transparent_1px)] [background-size:32px_32px] opacity-30" />
      </div>

      {/* Grid Layout Container */}
      <div className="relative z-10 min-h-screen flex flex-col justify-between p-6 sm:p-10 max-w-[1600px] mx-auto">
        
        {/* Top Header Row */}
        <header className="grid grid-cols-2 sm:grid-cols-4 items-start gap-4 text-xs tracking-wider uppercase text-zinc-400 border-b border-zinc-900/80 pb-6">
          <div className="flex items-center space-x-2">
            <span className="text-xl font-black text-white tracking-tighter flex items-center gap-1">
              <span className="text-red-600">++</span>LM
            </span>
          </div>

          <div className="hidden sm:block">
            <span className="text-zinc-500 block text-[10px]">STANDARD</span>
            <span className="text-zinc-200 font-mono">PCR 2011 // ACT 2011</span>
          </div>

          <div className="hidden sm:block">
            <span className="text-zinc-500 block text-[10px]">TIME (IST)</span>
            <span className="text-zinc-200 font-mono">{time || '11:38:00'}</span>
          </div>

          <div className="text-right">
            <span className="text-zinc-500 block text-[10px]">SYSTEM STATUS</span>
            <span className="inline-flex items-center gap-1.5 text-emerald-400 font-mono text-[11px]">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping" />
              ONLINE 2026
            </span>
          </div>
        </header>

        {/* Main Editorial Hero Section */}
        <main className="my-auto py-12 grid grid-cols-1 lg:grid-cols-12 gap-8 items-end">
          
          {/* Left Column: Sub-manifesto & Actions */}
          <div className="lg:col-span-5 space-y-8 order-2 lg:order-1">
            <div className="space-y-4">
              <div className="inline-flex items-center gap-2 px-3 py-1 bg-red-950/40 border border-red-800/40 text-red-400 text-xs font-mono uppercase tracking-widest rounded">
                <Activity className="w-3 h-3" />
                Statutory Vision Pipeline
              </div>
              <p className="text-xl sm:text-2xl font-medium tracking-tight text-zinc-200 leading-snug">
                <strong className="text-white font-bold">++metrologyAI</strong> is an autonomous computer vision and legal compliance engine engineered for packaging statutory enforcement.
              </p>
              <p className="text-sm text-zinc-400 leading-relaxed font-normal max-w-md">
                Instantly decode dot-matrix continuous inkjet (CIJ) stamps, extract multi-line MRP declarations, verify USP unit rates, and identify missing statutory disclosures.
              </p>
            </div>

            {/* CTA Button Group */}
            <div className="flex flex-wrap items-center gap-4 pt-2">
              <Link
                href="/scan"
                className="group relative inline-flex items-center justify-between gap-6 px-6 py-4 bg-white text-black hover:bg-red-600 hover:text-white transition-all duration-300 font-bold text-xs uppercase tracking-widest"
              >
                <span>Launch Scanner</span>
                <ArrowUpRight className="w-4 h-4 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
              </Link>

              <Link
                href="/dashboard"
                className="inline-flex items-center gap-2 px-6 py-4 bg-zinc-900/80 hover:bg-zinc-800 border border-zinc-800 text-zinc-300 hover:text-white transition-all text-xs font-mono uppercase tracking-wider"
              >
                <BarChart3 className="w-3.5 h-3.5 text-red-500" />
                <span>Audit Records</span>
              </Link>
            </div>
          </div>

          {/* Right Column: Giant Heavy Stacked Typography */}
          <div className="lg:col-span-7 order-1 lg:order-2 flex flex-col justify-end text-left lg:text-right select-none">
            <h1 className="text-[14vw] sm:text-[11vw] lg:text-[7.8vw] font-black leading-[0.88] tracking-tighter uppercase text-white font-stretch-condensed">
              <span className="block hover:text-red-500 transition-colors duration-300">LEGAL</span>
              <span className="block text-transparent bg-clip-text bg-gradient-to-r from-red-500 via-white to-zinc-300">METROLOGY</span>
              <span className="block hover:text-red-500 transition-colors duration-300">COMPLIANCE</span>
              <span className="block text-zinc-400">AUDIT</span>
            </h1>
          </div>

        </main>

        {/* Feature Capabilities Grid */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-4 border-t border-zinc-900/80 pt-8 pb-8">
          <div className="p-5 bg-zinc-950/60 border border-zinc-900 hover:border-red-900/50 transition duration-300">
            <div className="text-red-500 font-mono text-xs mb-2">01 // VISION</div>
            <h3 className="text-white text-base font-bold uppercase tracking-tight mb-1">CIJ Inkjet Parsing</h3>
            <p className="text-zinc-400 text-xs leading-relaxed">
              Deciphers deformed, shifted, and faded dot-matrix stamps for MFD, EXP, and Batch LOT numbers.
            </p>
          </div>

          <div className="p-5 bg-zinc-950/60 border border-zinc-900 hover:border-red-900/50 transition duration-300">
            <div className="text-red-500 font-mono text-xs mb-2">02 // RULES</div>
            <h3 className="text-white text-base font-bold uppercase tracking-tight mb-1">Statutory Verification</h3>
            <p className="text-zinc-400 text-xs leading-relaxed">
              Validates mandatory MRP statements, Tax Inclusivity clauses, Net Weight declarations, and USP formulas.
            </p>
          </div>

          <div className="p-5 bg-zinc-950/60 border border-zinc-900 hover:border-red-900/50 transition duration-300">
            <div className="text-red-500 font-mono text-xs mb-2">03 // REPORTS</div>
            <h3 className="text-white text-base font-bold uppercase tracking-tight mb-1">Instant Infraction Logs</h3>
            <p className="text-zinc-400 text-xs leading-relaxed">
              Generates legal compliance reports and flagged defect crops for audit-ready enforcement.
            </p>
          </div>
        </section>

        {/* Bottom Footer Bar */}
        <footer className="grid grid-cols-2 sm:grid-cols-3 items-center text-[11px] font-mono text-zinc-500 border-t border-zinc-900/80 pt-4">
          <div>
            <span className="text-zinc-400">LEGAL METROLOGY ACT, 2011</span>
          </div>
          <div className="hidden sm:text-center sm:block">
            <span>PACKAGED COMMODITIES RULES, 2011</span>
          </div>
          <div className="text-right">
            <span className="text-zinc-300">© 2026 METROLOGY.AI</span>
          </div>
        </footer>

      </div>
    </div>
  );
}