import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  ArrowLeft,
  Search,
  Eye,
  CheckCircle2,
  AlertTriangle,
  X,
  Package,
  DollarSign,
  Calendar,
  Hash,
  Award,
  Globe,
  RefreshCw,
  DownloadCloud
} from 'lucide-react';

export default function InspectionsPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [records, setRecords] = useState<any[]>([]);
  const [selectedRecord, setSelectedRecord] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchInspections = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/v1/scans/history');
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data)) setRecords(data);
      }
    } catch (err) {
      console.error('Failed to load history:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInspections();
  }, []);

  const handleDownloadPdf = (scanId: string) => {
    window.open(`http://localhost:8000/api/v1/scans/${scanId}/export-pdf`, '_blank');
  };

  const filtered = records.filter((r) => {
    const brand = (r.brand_name || r.declarations?.brand_name || '').toLowerCase();
    const product = (r.product_name || r.declarations?.commodity_name || '').toLowerCase();
    const scanId = (r.scan_id || r.id || '').toLowerCase();
    const query = searchTerm.toLowerCase();
    return brand.includes(query) || product.includes(query) || scanId.includes(query);
  });

  return (
    <div className="min-h-screen bg-[#070708] text-white flex flex-col font-sans selection:bg-[#FF1E1E] selection:text-white">
      {/* Background Ambience */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-[-10%] left-[20%] w-[600px] h-[600px] bg-[#FF1E1E]/15 rounded-full blur-[160px]" />
        <div className="absolute inset-0 bg-[radial-gradient(#1c1c20_1px,transparent_1px)] [background-size:28px_28px] opacity-40" />
      </div>

      <div className="relative z-10 flex-1 max-w-[1600px] w-full mx-auto p-6 sm:p-10 flex flex-col space-y-6">
        {/* Header Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-900 pb-6">
          <div>
            <div className="flex items-center gap-3">
              <Link href="/dashboard" className="text-zinc-500 hover:text-white transition">
                <ArrowLeft className="w-5 h-5" />
              </Link>
              <h1 className="text-3xl font-black uppercase tracking-tight text-white flex items-center gap-2">
                <span className="text-[#FF1E1E]">++</span>Inspection Audit Records
              </h1>
            </div>
            <p className="mt-1 text-xs font-mono text-zinc-500 pl-8">
              Verified packaging scans with statutory compliance ratings and downloadable PDF notices.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={fetchInspections}
              className="p-2.5 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 rounded text-zinc-400 hover:text-white transition flex items-center gap-1.5 text-xs font-mono"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </button>
            <Link
              href="/dashboard"
              className="px-4 py-2 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-300 hover:text-white text-xs font-mono uppercase tracking-wider rounded transition"
            >
              ← Dashboard
            </Link>
          </div>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-zinc-500" />
          <input
            type="text"
            placeholder="Search by Brand Name, Commodity, or Audit ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-zinc-950 border border-zinc-900 rounded-lg pl-10 pr-4 py-3 text-xs text-zinc-200 placeholder-zinc-600 focus:outline-none focus:border-[#FF1E1E] transition font-mono"
          />
        </div>

        {/* Table */}
        <div className="bg-zinc-950 border border-zinc-900 rounded-lg overflow-hidden">
          <div className="overflow-x-auto font-mono text-xs">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-zinc-900 bg-zinc-900/30 text-zinc-500 uppercase text-[10px] tracking-wider">
                  <th className="p-4 font-bold">Audit ID</th>
                  <th className="p-4 font-bold">Brand & Product</th>
                  <th className="p-4 font-bold">Declared Qty</th>
                  <th className="p-4 font-bold">MRP & USP</th>
                  <th className="p-4 font-bold">Timestamp</th>
                  <th className="p-4 font-bold">Score</th>
                  <th className="p-4 font-bold">Status</th>
                  <th className="p-4 font-bold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-900">
                {filtered.length > 0 ? (
                  filtered.map((item, idx) => {
                    const dec = item.declarations || item.extracted_declarations || {};
                    const compliant = item.is_compliant !== false && item.status !== 'VIOLATION';
                    const scanId = item.scan_id || item.id || `SCN-${idx+1}`;
                    return (
                      <tr key={idx} className="hover:bg-zinc-900/40 transition">
                        <td className="p-4 text-zinc-400 font-bold">#{scanId}</td>
                        <td className="p-4 text-white font-bold">
                          {item.brand_name || dec.brand_name || 'N/A'}{' '}
                          <span className="text-zinc-500 font-normal">({item.product_name || dec.commodity_name || 'Item'})</span>
                        </td>
                        <td className="p-4 text-zinc-300">{dec.net_quantity || dec.net_qty || '—'}</td>
                        <td className="p-4 text-zinc-300">
                          {dec.mrp || dec.maximum_retail_price || '—'}{' '}
                          <span className="text-zinc-500 text-[10px]">({dec.unit_sale_price || dec.usp || '—'})</span>
                        </td>
                        <td className="p-4 text-zinc-500">{item.timestamp || 'Recent'}</td>
                        <td className="p-4 text-white font-bold">{item.compliance_score || item.score || 100}%</td>
                        <td className="p-4">
                          <span
                            className={`px-2.5 py-1 text-[10px] uppercase font-bold rounded ${
                              compliant
                                ? 'bg-emerald-950/60 border border-emerald-800 text-emerald-400'
                                : 'bg-red-950/60 border border-red-800 text-[#FF1E1E]'
                            }`}
                          >
                            {item.status || (compliant ? 'COMPLIANT' : 'INFRACTION')}
                          </span>
                        </td>
                        <td className="p-4 text-right">
                          <div className="flex items-center justify-end gap-2">
                            <button
                              onClick={() => setSelectedRecord(item)}
                              className="px-2.5 py-1.5 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-300 hover:text-white rounded text-[11px] font-mono flex items-center gap-1 transition"
                            >
                              <Eye className="w-3.5 h-3.5 text-[#FF1E1E]" />
                              <span>View</span>
                            </button>
                            <button
                              onClick={() => handleDownloadPdf(scanId)}
                              className="px-2.5 py-1.5 bg-[#FF1E1E]/10 hover:bg-[#FF1E1E] text-[#FF1E1E] hover:text-white border border-[#FF1E1E]/30 rounded text-[11px] font-mono flex items-center gap-1 transition font-bold"
                            >
                              <DownloadCloud className="w-3.5 h-3.5" />
                              <span>PDF</span>
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })
                ) : (
                  <tr>
                    <td colSpan={8} className="py-20 text-center text-zinc-600 font-mono text-xs">
                      {loading ? 'Fetching records from database...' : 'No inspection records found.'}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Detail Modal */}
      {selectedRecord && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-zinc-950 border border-zinc-800 rounded-lg w-full max-w-2xl p-6 space-y-6 font-mono text-xs max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-zinc-900 pb-4">
              <div>
                <h3 className="text-base font-bold uppercase text-white tracking-wider flex items-center gap-2">
                  <span className="text-[#FF1E1E]">++</span>Audit #{selectedRecord.scan_id || selectedRecord.id}
                </h3>
                <span className="text-zinc-500 text-[11px]">{selectedRecord.timestamp}</span>
              </div>
              <button
                onClick={() => setSelectedRecord(null)}
                className="p-1 text-zinc-500 hover:text-white rounded"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Declarations Grid */}
            {(() => {
              const dec = selectedRecord.declarations || selectedRecord.extracted_declarations || {};
              return (
                <div className="grid grid-cols-2 gap-3 text-zinc-300">
                  <div className="p-3 bg-zinc-900/60 border border-zinc-800/80 rounded">
                    <span className="text-zinc-500 block text-[10px]">BRAND</span>
                    <span className="font-bold text-white">{dec.brand_name || 'MISSING'}</span>
                  </div>
                  <div className="p-3 bg-zinc-900/60 border border-zinc-800/80 rounded">
                    <span className="text-zinc-500 block text-[10px]">COMMODITY</span>
                    <span className="font-bold text-white">{dec.commodity_name || selectedRecord.product_name || 'MISSING'}</span>
                  </div>
                  <div className="p-3 bg-zinc-900/60 border border-zinc-800/80 rounded">
                    <span className="text-zinc-500 block text-[10px]">NET QUANTITY</span>
                    <span className="font-bold text-white">{dec.net_quantity || dec.net_qty || 'MISSING'}</span>
                  </div>
                  <div className="p-3 bg-zinc-900/60 border border-zinc-800/80 rounded">
                    <span className="text-zinc-500 block text-[10px]">MRP (INCL TAX)</span>
                    <span className="font-bold text-white">{dec.mrp || dec.maximum_retail_price || 'MISSING'}</span>
                  </div>
                  <div className="p-3 bg-zinc-900/60 border border-zinc-800/80 rounded">
                    <span className="text-zinc-500 block text-[10px]">UNIT SALE PRICE (USP)</span>
                    <span className="font-bold text-white">{dec.unit_sale_price || dec.usp || 'MISSING'}</span>
                  </div>
                  <div className="p-3 bg-zinc-900/60 border border-zinc-800/80 rounded">
                    <span className="text-zinc-500 block text-[10px]">MFG / PACKING DATE</span>
                    <span className="font-bold text-white">{dec.mfg_date || dec.date_of_packing || 'MISSING'}</span>
                  </div>
                  <div className="p-3 bg-zinc-900/60 border border-zinc-800/80 rounded">
                    <span className="text-zinc-500 block text-[10px]">EXPIRY / USE BY</span>
                    <span className="font-bold text-white">{dec.expiry_date || dec.best_before || 'MISSING'}</span>
                  </div>
                  <div className="p-3 bg-zinc-900/60 border border-zinc-800/80 rounded">
                    <span className="text-zinc-500 block text-[10px]">BATCH / LOT NO</span>
                    <span className="font-bold text-white">{dec.batch_number || dec.lot_number || 'MISSING'}</span>
                  </div>
                </div>
              );
            })()}

            <div className="flex justify-between items-center pt-2">
              <button
                onClick={() => handleDownloadPdf(selectedRecord.scan_id || selectedRecord.id)}
                className="px-4 py-2.5 bg-[#FF1E1E] hover:bg-[#d91616] text-white rounded font-bold text-xs uppercase flex items-center gap-2 transition"
              >
                <DownloadCloud className="w-4 h-4" />
                <span>Download Statutory PDF Report</span>
              </button>
              <button
                onClick={() => setSelectedRecord(null)}
                className="px-4 py-2 bg-zinc-900 hover:bg-zinc-800 text-zinc-300 rounded font-bold text-xs uppercase"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}