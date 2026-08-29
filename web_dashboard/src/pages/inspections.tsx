import React, { useEffect, useState } from 'react';
import { Search, CheckCircle, AlertTriangle } from 'lucide-react';
import { fetchScanHistory, ScanResult } from '../services/api';
import ReportViewer from '../components/ReportViewer';

export default function InspectionsPage() {
  const [scans, setScans] = useState<ScanResult[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [activeScan, setActiveScan] = useState<ScanResult | null>(null);

  useEffect(() => {
    fetchScanHistory()
      .then((data) => setScans(data))
      .catch(() => {});
  }, []);

  const filtered = scans.filter(
    (s) =>
      s.brand_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.scan_id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-slate-100 p-7 font-sans">
      <div className="max-w-5xl mx-auto">
        <div className="flex justify-between items-center mb-5">
          <div>
            <h1 className="text-xl font-bold text-slate-900">Inspection Audit Records</h1>
            <p className="text-xs text-slate-500 mt-0.5">
              Verified packaging scans with compliance ratings and notice export tools.
            </p>
          </div>
          <a href="/dashboard" className="text-xs font-bold text-slate-600 hover:text-slate-900">
            &larr; Return to Dashboard
          </a>
        </div>

        <div className="bg-white p-2.5 rounded-xl border border-slate-200 shadow-sm mb-5 flex items-center space-x-2">
          <Search className="w-3.5 h-3.5 text-slate-400 ml-1" />
          <input
            type="text"
            placeholder="Search by Brand Name or Scan ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full text-xs outline-none bg-transparent"
          />
        </div>

        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider text-[10px]">
                <th className="p-3">Notice ID</th>
                <th className="p-3">Brand & Commodity</th>
                <th className="p-3">PDP Surface</th>
                <th className="p-3">Score</th>
                <th className="p-3">Statutory Status</th>
                <th className="p-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium">
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={6} className="p-6 text-center text-slate-400">
                    No inspection audit records found.
                  </td>
                </tr>
              ) : (
                filtered.map((s, idx) => (
                  <tr key={idx} className="hover:bg-slate-50 transition">
                    <td className="p-3 font-mono font-bold text-blue-600">
                      SCN-{s.scan_id.substring(0, 8).toUpperCase()}
                    </td>
                    <td className="p-3">
                      <p className="font-bold text-slate-900">{s.brand_name}</p>
                      <p className="text-[10px] text-slate-400">{s.commodity_name}</p>
                    </td>
                    <td className="p-3">{s.pdp_area_cm2} cm²</td>
                    <td className="p-3 font-bold">{s.compliance_score}%</td>
                    <td className="p-3">
                      <span
                        className={`inline-flex items-center space-x-1 px-1.5 py-0.5 rounded text-[10px] font-bold ${
                          s.is_compliant
                            ? 'bg-emerald-100 text-emerald-800'
                            : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {s.is_compliant ? <CheckCircle className="w-3 h-3" /> : <AlertTriangle className="w-3 h-3" />}
                        <span>{s.is_compliant ? 'COMPLIANT' : `${s.violations.length} VIOLATIONS`}</span>
                      </span>
                    </td>
                    <td className="p-3 text-right">
                      <button
                        onClick={() => setActiveScan(s)}
                        className="px-2.5 py-1 bg-slate-900 hover:bg-slate-800 text-white rounded font-bold text-[10px] transition"
                      >
                        View Audit
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {activeScan && <ReportViewer scan={activeScan} onClose={() => setActiveScan(null)} />}
    </div>
  );
}