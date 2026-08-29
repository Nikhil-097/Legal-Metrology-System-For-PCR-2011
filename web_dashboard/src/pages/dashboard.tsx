import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  Scan,
  AlertTriangle,
  AlertOctagon,
  ArrowUpRight,
  ArrowDownRight,
  MoreVertical,
} from 'lucide-react';
import AppLayout from '../components/AppLayout';
import ReportViewer from '../components/ReportViewer';
import { fetchDashboardStats, fetchScanHistory, ScanResult } from '../services/api';

// Helper function to format timestamp accurately to local time
const formatScanDateTime = (dateStr?: string) => {
  if (!dateStr) {
    return new Date().toLocaleDateString('en-GB', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
    }).replace(',', ' •');
  }

  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return dateStr;

  return d.toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  }).replace(',', ' •');
};

export default function Dashboard() {
  const [stats, setStats] = useState({
    total_scans: 0,
    compliant_count: 0,
    non_compliant_count: 0,
    compliance_rate_percentage: 100,
    warnings_count: 0,
    violations_count: 0,
  });

  const [recentScans, setRecentScans] = useState<any[]>([]);
  const [selectedScan, setSelectedScan] = useState<ScanResult | null>(null);

  useEffect(() => {
    fetchDashboardStats()
      .then((data) => {
        if (data && typeof data.total_scans === 'number') {
          setStats((prev) => ({
            ...prev,
            total_scans: data.total_scans,
            compliant_count: data.compliant_count || 0,
            compliance_rate_percentage: Math.round(data.compliance_rate_percentage || 100),
          }));
        }
      })
      .catch(() => {});

    fetchScanHistory()
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) {
          const formatted = data.map((d: any) => ({
            ...d,
            status: d.is_compliant
              ? 'Compliant'
              : (d.compliance_score || 0) >= 60
              ? 'Warning'
              : 'Violation',
            created_at: formatScanDateTime(d.created_at),
          }));

          setRecentScans(formatted);

          // Compute KPI counts dynamically from real scan history
          const total = formatted.length;
          const violations = formatted.filter((s: any) => s.status === 'Violation').length;
          const warnings = formatted.filter((s: any) => s.status === 'Warning').length;
          const compliant = formatted.filter((s: any) => s.status === 'Compliant').length;
          const rate = total > 0 ? Math.round((compliant / total) * 100) : 100;

          setStats({
            total_scans: total,
            compliant_count: compliant,
            non_compliant_count: violations + warnings,
            compliance_rate_percentage: rate,
            warnings_count: warnings,
            violations_count: violations,
          });
        }
      })
      .catch(() => {});
  }, []);

  return (
    <AppLayout>
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Top 4 KPI Stat Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white border border-slate-100 rounded-2xl p-5 shadow-sm flex items-center justify-between">
            <div>
              <p className="text-xs text-slate-500 font-semibold">Overall Compliance Score</p>
              <h3 className="text-3xl font-black text-emerald-600 mt-1">
                {stats.compliance_rate_percentage}%
              </h3>
              <p className="text-[11px] text-emerald-600 font-bold flex items-center gap-0.5 mt-2">
                <ArrowUpRight className="w-3.5 h-3.5" />
                <span>Live System Health</span>
              </p>
            </div>
            <div className="w-14 h-14 rounded-full border-4 border-emerald-500 border-t-slate-100 flex items-center justify-center shrink-0" />
          </div>

          <div className="bg-white border border-slate-100 rounded-2xl p-5 shadow-sm flex items-center justify-between">
            <div>
              <p className="text-xs text-slate-500 font-semibold">Total Scans</p>
              <h3 className="text-3xl font-black text-blue-600 mt-1">{stats.total_scans}</h3>
              <p className="text-[11px] text-blue-600 font-bold flex items-center gap-0.5 mt-2">
                <ArrowUpRight className="w-3.5 h-3.5" />
                <span>Total records audited</span>
              </p>
            </div>
            <div className="w-12 h-12 rounded-2xl bg-blue-50 flex items-center justify-center text-blue-600 shrink-0">
              <Scan className="w-6 h-6" />
            </div>
          </div>

          <div className="bg-white border border-slate-100 rounded-2xl p-5 shadow-sm flex items-center justify-between">
            <div>
              <p className="text-xs text-slate-500 font-semibold">Warnings</p>
              <h3 className="text-3xl font-black text-amber-500 mt-1">{stats.warnings_count}</h3>
              <p className="text-[11px] text-slate-400 font-medium flex items-center gap-0.5 mt-2">
                <ArrowDownRight className="w-3.5 h-3.5 text-amber-500" />
                <span>Minor Rule 6 variances</span>
              </p>
            </div>
            <div className="w-12 h-12 rounded-2xl bg-amber-50 flex items-center justify-center text-amber-500 shrink-0">
              <AlertTriangle className="w-6 h-6" />
            </div>
          </div>

          <div className="bg-white border border-slate-100 rounded-2xl p-5 shadow-sm flex items-center justify-between">
            <div>
              <p className="text-xs text-slate-500 font-semibold">Violations</p>
              <h3 className="text-3xl font-black text-rose-600 mt-1">{stats.violations_count}</h3>
              <p className="text-[11px] text-slate-400 font-medium flex items-center gap-0.5 mt-2">
                <ArrowDownRight className="w-3.5 h-3.5 text-rose-500" />
                <span>Statutory contraventions</span>
              </p>
            </div>
            <div className="w-12 h-12 rounded-2xl bg-rose-50 flex items-center justify-center text-rose-500 shrink-0">
              <AlertOctagon className="w-6 h-6" />
            </div>
          </div>
        </div>

        {/* Recent Scan History Table */}
        <div className="bg-white border border-slate-100 rounded-2xl p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-slate-900">Recent Scan History</h3>
            <Link
              href="/inspections"
              className="px-3 py-1.5 bg-[#2541B2] hover:bg-blue-700 text-white rounded-lg text-xs font-bold transition shadow-sm"
            >
              View All
            </Link>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-slate-100 text-slate-400 font-bold uppercase text-[10px]">
                  <th className="pb-3">Product Name</th>
                  <th className="pb-3">Brand</th>
                  <th className="pb-3">Scan Date & Time</th>
                  <th className="pb-3">Compliance Score</th>
                  <th className="pb-3">Status</th>
                  <th className="pb-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50 font-medium">
                {recentScans.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-slate-400">
                      No scans performed yet. Go to Scan Product to begin.
                    </td>
                  </tr>
                ) : (
                  recentScans.map((scan, idx) => {
                    const isCompliant = scan.status === 'Compliant';
                    const isWarning = scan.status === 'Warning';
                    return (
                      <tr key={idx} className="hover:bg-slate-50/60 transition">
                        <td className="py-3 font-bold text-slate-900 flex items-center space-x-3">
                          <div className="w-7 h-7 rounded-lg bg-slate-100 flex items-center justify-center shrink-0 border border-slate-200">
                            <Scan className="w-3.5 h-3.5 text-slate-500" />
                          </div>
                          <span>{scan.commodity_name || scan.brand_name}</span>
                        </td>
                        <td className="py-3 text-slate-600">{scan.brand_name || 'N/A'}</td>
                        <td className="py-3 text-slate-400">{scan.created_at}</td>
                        <td className="py-3 font-bold">
                          <span
                            className={
                              isCompliant
                                ? 'text-emerald-600'
                                : isWarning
                                ? 'text-amber-500'
                                : 'text-rose-600'
                            }
                          >
                            {scan.compliance_score}%
                          </span>
                        </td>
                        <td className="py-3">
                          <span
                            className={`px-2.5 py-1 rounded-full text-[10px] font-bold ${
                              isCompliant
                                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                              : isWarning
                              ? 'bg-amber-50 text-amber-700 border border-amber-200'
                              : 'bg-rose-50 text-rose-700 border border-rose-200'
                            }`}
                          >
                            {scan.status}
                          </span>
                        </td>
                        <td className="py-3 text-right">
                          <div className="inline-flex items-center space-x-2">
                            <button
                              onClick={() => setSelectedScan(scan)}
                              className="px-3 py-1 border border-blue-200 text-blue-600 hover:bg-blue-50 rounded-lg text-xs font-bold transition"
                            >
                              View Report
                            </button>
                            <button className="p-1 text-slate-400 hover:text-slate-600 rounded">
                              <MoreVertical className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {selectedScan && (
        <ReportViewer scan={selectedScan} onClose={() => setSelectedScan(null)} />
      )}
    </AppLayout>
  );
}