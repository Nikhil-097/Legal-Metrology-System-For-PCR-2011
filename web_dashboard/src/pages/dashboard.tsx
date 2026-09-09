import React, { useState, useEffect } from "react";
import Head from "next/head";
import Link from "next/link";
import { LayoutDashboard, ScanLine, History, Settings, RotateCw } from "lucide-react";

interface ScanSummary {
  scan_id: string;
  product_name: string;
  brand_name: string;
  category: string;
  timestamp: string;
  compliance_score: number;
  status: string;
  declarations?: {
    net_quantity?: string;
    mrp?: string;
  };
}

export default function Dashboard() {
  const [scans, setScans] = useState<ScanSummary[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchScans = async () => {
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/api/v1/scans/history");
      if (res.ok) {
        const data = await res.json();
        setScans(data);
      }
    } catch (err) {
      console.error("Failed to fetch scan history", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchScans();
  }, []);

  const totalScans = scans.length;
  const violationsCount = scans.filter(
    (s) => s.status === "NON-COMPLIANT" || (s.compliance_score !== undefined && s.compliance_score < 70)
  ).length;

  const avgScore =
    totalScans > 0
      ? Math.round(scans.reduce((acc, s) => acc + (s.compliance_score || 0), 0) / totalScans)
      : 100;

  return (
    <div className="min-h-screen bg-[#050608] text-white flex flex-col font-sans relative overflow-x-hidden">
      <Head>
        <title>MetroCheck | Overview & Operations</title>
      </Head>

      {/* Expansive Full-Screen Red Ambient Glow & Dotted Matrix Grid */}
      <div
        className="fixed inset-0 pointer-events-none z-0"
        style={{
          background: `
            radial-gradient(ellipse 1100px 750px at 60% 28%, rgba(220, 20, 20, 0.22) 0%, rgba(180, 15, 15, 0.12) 35%, rgba(100, 10, 10, 0.04) 65%, transparent 80%),
            radial-gradient(ellipse 900px 600px at 50% 70%, rgba(190, 15, 15, 0.14) 0%, rgba(140, 10, 10, 0.05) 45%, transparent 75%),
            radial-gradient(rgba(255, 255, 255, 0.09) 1px, transparent 1px)
          `,
          backgroundSize: "auto, auto, 28px 28px"
        }}
      />

      <div className="relative z-10 flex flex-1">
        {/* Sidebar */}
        <aside className="w-64 border-r border-[#16181F] bg-[#07080B]/90 backdrop-blur-md flex flex-col justify-between p-6 shrink-0 hidden md:flex">
          <div className="space-y-8">
            <Link className="flex items-center space-x-2" href="/">
              <span className="text-xl font-black tracking-tighter text-white">
                <span className="text-[#FF1E1E]">++</span>METROCHECK
              </span>
            </Link>

            <nav className="space-y-1 font-mono text-xs uppercase tracking-wider">
              <Link
                className="flex items-center space-x-3 px-3.5 py-3 text-white bg-[#FF1E1E] font-bold rounded-lg shadow-lg shadow-[#FF1E1E]/20"
                href="/dashboard"
              >
                <LayoutDashboard className="w-4 h-4" />
                <span>DASHBOARD</span>
              </Link>
              <Link
                className="flex items-center space-x-3 px-3.5 py-3 text-[#7E8B9B] hover:text-white hover:bg-[#101217] rounded-lg transition"
                href="/scan"
              >
                <ScanLine className="w-4 h-4" />
                <span>SCAN PRODUCT</span>
              </Link>
              <Link
                className="flex items-center space-x-3 px-3.5 py-3 text-[#7E8B9B] hover:text-white hover:bg-[#101217] rounded-lg transition"
                href="/inspections"
              >
                <History className="w-4 h-4" />
                <span>INSPECTIONS</span>
              </Link>
              <Link
                className="flex items-center space-x-3 px-3.5 py-3 text-[#7E8B9B] hover:text-white hover:bg-[#101217] rounded-lg transition"
                href="/settings"
              >
                <Settings className="w-4 h-4" />
                <span>SETTINGS</span>
              </Link>
            </nav>
          </div>

          <div className="p-3.5 bg-[#0A0B0E] border border-[#16181F] rounded-lg text-[10px] font-mono text-[#555E6B]">
            <div className="text-[#8E99A8] font-bold mb-0.5">LEGAL METROLOGY ACT, 2011</div>
            <div>PCR 2011 // Active Engine</div>
          </div>
        </aside>

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col min-w-0">
          <header className="h-16 border-b border-[#16181F] px-8 flex items-center justify-between bg-[#07080B]/40 backdrop-blur-md">
            <span className="text-[#7E8B9B] font-mono text-xs uppercase tracking-widest font-bold">
              OVERVIEW & OPERATIONS
            </span>
            <div className="flex items-center gap-4">
              <button
                onClick={fetchScans}
                title="Refresh Records"
                className="p-2 bg-[#0E1015] hover:bg-[#161922] border border-[#202430] rounded text-[#7E8B9B] hover:text-white transition"
              >
                <RotateCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
              </button>
              <div className="text-right font-mono text-xs hidden sm:block">
                <span className="text-[#555E6B] text-[10px] block">STANDARD</span>
                <span className="text-[#B5BFC9] uppercase font-bold tracking-wider">PCR 2011 // ACT 2011</span>
              </div>
            </div>
          </header>

          <main className="flex-1 p-8 space-y-6 overflow-y-auto">
            {/* Top 3 Metric Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* 1. Overall Compliance Score */}
              <div
                className="rounded-xl p-6 border border-[#242936] relative"
                style={{ backgroundColor: "rgba(10, 11, 15, 0.60)", backdropFilter: "blur(12px)" }}
              >
                <span className="text-[11px] font-mono tracking-wider text-[#7E8B9B] uppercase block mb-3 font-semibold">
                  OVERALL COMPLIANCE SCORE
                </span>
                <div className="text-4xl font-bold text-[#00E5A3] font-mono tracking-tight mb-4">
                  {avgScore}%
                </div>
                <div className="flex items-center text-xs text-[#00E5A3] space-x-2 font-mono">
                  <span className="text-base leading-none">∿</span>
                  <span>Live System Health</span>
                </div>
              </div>

              {/* 2. Total Scans Audited */}
              <div
                className="rounded-xl p-6 border border-[#242936] relative"
                style={{ backgroundColor: "rgba(10, 11, 15, 0.60)", backdropFilter: "blur(12px)" }}
              >
                <span className="text-[11px] font-mono tracking-wider text-[#7E8B9B] uppercase block mb-3 font-semibold">
                  TOTAL SCANS AUDITED
                </span>
                <div className="text-4xl font-bold text-white font-mono tracking-tight mb-4">
                  {totalScans}
                </div>
                <div className="flex items-center text-xs text-[#7E8B9B] space-x-2 font-mono">
                  <span className="text-[#FF3B30] text-sm leading-none">🗎</span>
                  <span>Verified Declarations</span>
                </div>
              </div>

              {/* 3. Violations */}
              <div
                className="rounded-xl p-6 border border-[#242936] relative"
                style={{ backgroundColor: "rgba(10, 11, 15, 0.60)", backdropFilter: "blur(12px)" }}
              >
                <span className="text-[11px] font-mono tracking-wider text-[#7E8B9B] uppercase block mb-3 font-semibold">
                  VIOLATIONS
                </span>
                <div className="text-4xl font-bold text-[#FF1E1E] font-mono tracking-tight mb-4">
                  {violationsCount}
                </div>
                <div className="flex items-center text-xs text-[#FF1E1E] space-x-2 font-mono">
                  <span className="text-sm leading-none">⊗</span>
                  <span>Statutory contraventions</span>
                </div>
              </div>
            </div>

            {/* Recent Scan History Container */}
            <div
              className="rounded-xl p-6 border border-[#242936]"
              style={{ backgroundColor: "rgba(10, 11, 15, 0.65)", backdropFilter: "blur(12px)" }}
            >
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-lg font-black tracking-wide uppercase text-white font-mono">
                    RECENT SCAN HISTORY
                  </h2>
                  <p className="text-xs text-[#555E6B] font-mono mt-1">
                    Live audit logs stored in Legal Metrology database
                  </p>
                </div>
                <Link
                  href="/inspections"
                  className="px-4 py-2 text-xs font-mono border border-[#2A303F] rounded-lg text-white hover:bg-[#141720] transition flex items-center space-x-1.5"
                >
                  <span className="tracking-wider">VIEW ALL RECORDS</span>
                  <span className="text-[#FF1E1E] font-bold">↗</span>
                </Link>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs font-mono">
                  <thead>
                    <tr className="text-[#555E6B] border-b border-[#1E222D] pb-3">
                      <th className="py-3 px-2 uppercase font-medium">AUDIT ID</th>
                      <th className="py-3 px-2 uppercase font-medium">PRODUCT / COMMODITY</th>
                      <th className="py-3 px-2 uppercase font-medium">BRAND</th>
                      <th className="py-3 px-2 uppercase font-medium">NET QTY / MRP</th>
                      <th className="py-3 px-2 uppercase font-medium">TIMESTAMP</th>
                      <th className="py-3 px-2 uppercase font-medium">SCORE</th>
                      <th className="py-3 px-2 uppercase font-medium text-right">STATUS</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#161922]">
                    {loading ? (
                      <tr>
                        <td colSpan={7} className="py-14 text-center text-[#555E6B]">
                          Loading records...
                        </td>
                      </tr>
                    ) : scans.length === 0 ? (
                      <tr>
                        <td colSpan={7} className="py-14 text-center text-[#555E6B]">
                          No scans performed yet.
                        </td>
                      </tr>
                    ) : (
                      scans.slice(0, 10).map((item) => (
                        <tr key={item.scan_id} className="hover:bg-[#141822]/60 transition-colors">
                          <td className="py-3.5 px-2 text-[#00E5A3] font-bold">{item.scan_id}</td>
                          <td className="py-3.5 px-2 text-white font-medium">{item.product_name}</td>
                          <td className="py-3.5 px-2 text-[#7E8B9B]">{item.brand_name || "N/A"}</td>
                          <td className="py-3.5 px-2 text-[#7E8B9B]">
                            {item.declarations?.net_quantity || "—"} / {item.declarations?.mrp || "—"}
                          </td>
                          <td className="py-3.5 px-2 text-[#555E6B]">{item.timestamp}</td>
                          <td className="py-3.5 px-2 font-bold text-white">
                            {item.compliance_score}%
                          </td>
                          <td className="py-3.5 px-2 text-right">
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-bold tracking-wider border ${
                                item.status === "COMPLIANT"
                                  ? "bg-[#00E5A3]/10 border-[#00E5A3]/30 text-[#00E5A3]"
                                  : "bg-[#FF1E1E]/10 border-[#FF1E1E]/30 text-[#FF1E1E]"
                              }`}
                            >
                              {item.status}
                            </span>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}