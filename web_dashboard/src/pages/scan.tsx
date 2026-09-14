import React, { useState, useRef } from 'react';
import Link from 'next/link';
import {
  LayoutDashboard,
  ScanLine,
  History,
  Settings,
  UploadCloud,
  RefreshCw,
  DownloadCloud,
  FileSpreadsheet,
  Utensils,
  Pill,
  ShieldCheck,
  PhoneCall,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';

export default function ScanPage() {
  const [category, setCategory] = useState<'food' | 'drugs_commodities'>('food');

  // Dual surface files
  const [frontFile, setFrontFile] = useState<File | null>(null);
  const [frontPreview, setFrontPreview] = useState<string | null>(null);
  const [backFile, setBackFile] = useState<File | null>(null);
  const [backPreview, setBackPreview] = useState<string | null>(null);

  const [heightCm, setHeightCm] = useState('15');
  const [widthCm, setWidthCm] = useState('10');
  const [brandName, setBrandName] = useState('');
  const [commodityName, setCommodityName] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any | null>(null);

  const frontInputRef = useRef<HTMLInputElement>(null);
  const backInputRef = useRef<HTMLInputElement>(null);

  const handleAnalyze = async () => {
    if (!frontFile) return;
    setLoading(true);

    const formData = new FormData();
    formData.append('front_file', frontFile);
    if (backFile) formData.append('back_file', backFile);
    formData.append('category', category);
    formData.append('height_cm', heightCm);
    formData.append('width_cm', widthCm);
    if (brandName) formData.append('brand_name', brandName);
    if (commodityName) formData.append('commodity_name', commodityName);

    try {
      const res = await fetch('http://localhost:8000/api/v1/scans/analyze', {
        method: 'POST',
        body: formData,
      });
      if (res.ok) {
        const data = await res.json();
        setResult(data);
      }
    } catch (err) {
      console.error('Inspection failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const declarations = result?.declarations || {};
  const boxes = result?.bounding_boxes || {};
  const care = result?.consumer_care || {};
  const barcode = result?.barcode_data || {};
  const score = result?.compliance_score ?? 100;
  const status = result?.status || 'COMPLIANT';

  return (
    <div className="min-h-screen bg-[#070708] text-white flex flex-col font-sans">
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-[-10%] left-[20%] w-[600px] h-[600px] bg-[#FF1E1E]/15 rounded-full blur-[160px]" />
        <div className="absolute inset-0 bg-[radial-gradient(#1c1c20_1px,transparent_1px)] [background-size:28px_28px] opacity-40" />
      </div>

      <div className="relative z-10 flex flex-1">
        {/* Sidebar */}
        <aside className="w-64 border-r border-zinc-900 bg-[#09090b]/80 backdrop-blur flex flex-col justify-between p-6 shrink-0 hidden md:flex">
          <div className="space-y-8">
            <Link className="flex items-center space-x-2" href="/">
              <span className="text-xl font-black tracking-tighter text-white">
                <span className="text-[#FF1E1E]">++</span>METROCHECK
              </span>
            </Link>

            <nav className="space-y-1.5 font-mono text-xs uppercase tracking-wider">
              <Link className="flex items-center space-x-3 px-3.5 py-3 text-zinc-400 hover:text-white hover:bg-zinc-900/60 rounded-md transition" href="/dashboard">
                <LayoutDashboard className="w-4 h-4" />
                <span>Dashboard</span>
              </Link>
              <Link className="flex items-center space-x-3 px-3.5 py-3 text-white bg-[#FF1E1E] font-bold rounded-md shadow-lg shadow-[#FF1E1E]/20" href="/scan">
                <ScanLine className="w-4 h-4" />
                <span>Dual Scan</span>
              </Link>
              <Link className="flex items-center space-x-3 px-3.5 py-3 text-zinc-400 hover:text-white hover:bg-zinc-900/60 rounded-md transition" href="/inspections">
                <History className="w-4 h-4" />
                <span>Inspections</span>
              </Link>
              <Link className="flex items-center space-x-3 px-3.5 py-3 text-zinc-400 hover:text-white hover:bg-zinc-900/60 rounded-md transition" href="/settings">
                <Settings className="w-4 h-4" />
                <span>Settings</span>
              </Link>
            </nav>
          </div>

          <div className="p-4 bg-zinc-950 border border-zinc-900 rounded text-[10px] font-mono text-zinc-500">
            <div className="text-zinc-400 font-bold mb-1">LEGAL METROLOGY ACT, 2011</div>
            <div>PCR 2011 + Rule 6(1)(h) Engine</div>
          </div>
        </aside>

        {/* Content Area */}
        <div className="flex-1 flex flex-col min-w-0">
          <header className="h-16 border-b border-zinc-900 bg-[#09090b]/60 backdrop-blur px-8 flex items-center justify-between">
            <span className="text-zinc-400 font-mono text-xs uppercase tracking-widest font-bold">
              AI DUAL-PANEL STATUTORY AUDITOR
            </span>
            <div className="flex items-center gap-3">
              <button
                onClick={() => window.open('http://localhost:8000/api/v1/scans/export-csv', '_blank')}
                className="px-3 py-1.5 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-xs font-mono rounded text-zinc-300 hover:text-white flex items-center gap-2 transition"
              >
                <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-500" />
                <span>Batch CSV Export</span>
              </button>
              <div className="text-right font-mono text-xs hidden sm:block">
                <span className="text-zinc-500 text-[10px] block">STANDARDS</span>
                <span className="text-zinc-200 uppercase font-bold">PCR 2011 // GS1 VERIFIED</span>
              </div>
            </div>
          </header>

          <main className="flex-1 p-8 space-y-6 overflow-y-auto">
            {/* Category Toggle */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 bg-zinc-950 border border-zinc-900 rounded-lg">
              <div>
                <span className="text-xs font-mono uppercase tracking-wider text-zinc-400 block font-bold">
                  Packaging Inspection Standard
                </span>
                <span className="text-[11px] font-mono text-zinc-500">
                  {category === 'food'
                    ? 'Audits Food Category: Rule 6 mandatory declarations + FSSAI registration numbers.'
                    : 'Audits Non-Food / Commodities: Ommits FSSAI checks; strictly enforces Legal Metrology standard schedules.'}
                </span>
              </div>

              <div className="flex bg-zinc-900 p-1 border border-zinc-800 rounded-lg font-mono text-xs">
                <button
                  type="button"
                  onClick={() => setCategory('food')}
                  className={`flex items-center gap-2 px-4 py-2 rounded-md transition font-bold uppercase text-[11px] ${
                    category === 'food' ? 'bg-[#FF1E1E] text-white shadow-md' : 'text-zinc-400 hover:text-white'
                  }`}
                >
                  <Utensils className="w-3.5 h-3.5" />
                  <span>Food Products</span>
                </button>
                <button
                  type="button"
                  onClick={() => setCategory('drugs_commodities')}
                  className={`flex items-center gap-2 px-4 py-2 rounded-md transition font-bold uppercase text-[11px] ${
                    category === 'drugs_commodities' ? 'bg-[#FF1E1E] text-white shadow-md' : 'text-zinc-400 hover:text-white'
                  }`}
                >
                  <Pill className="w-3.5 h-3.5" />
                  <span>Drugs & Commodities</span>
                </button>
              </div>
            </div>

            {/* Dual Artwork Upload Section */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Surface 1: Front Principal Display Panel (PDP) */}
              <div
                onClick={() => frontInputRef.current?.click()}
                className="relative h-[320px] bg-zinc-950/80 border-2 border-dashed border-zinc-800 hover:border-[#FF1E1E]/50 rounded-lg flex flex-col items-center justify-center p-4 text-center cursor-pointer transition overflow-hidden group"
              >
                <input
                  type="file"
                  ref={frontInputRef}
                  onChange={(e) => {
                    if (e.target.files?.[0]) {
                      setFrontFile(e.target.files[0]);
                      setFrontPreview(URL.createObjectURL(e.target.files[0]));
                      setResult(null);
                    }
                  }}
                  accept="image/*"
                  className="hidden"
                />

                {frontPreview ? (
                  <div className="relative w-full h-full">
                    <img src={frontPreview} alt="Front PDP" className="w-full h-full object-contain" />
                    {/* Bounding Box Visual Overlays */}
                    {Object.entries(boxes).map(([key, box]: [string, any]) => {
                      if (!Array.isArray(box) || box.length !== 4) return null;
                      const [ymin, xmin, ymax, xmax] = box;
                      return (
                        <div
                          key={key}
                          className="absolute border border-emerald-500 bg-emerald-500/15 pointer-events-none text-[9px] font-mono text-emerald-300 font-bold px-1"
                          style={{
                            top: `${ymin / 10}%`,
                            left: `${xmin / 10}%`,
                            width: `${(xmax - xmin) / 10}%`,
                            height: `${(ymax - ymin) / 10}%`,
                          }}
                        >
                          {key.replace('_', ' ')}
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="space-y-2">
                    <UploadCloud className="w-8 h-8 text-[#FF1E1E] mx-auto group-hover:scale-110 transition" />
                    <span className="font-mono text-xs font-bold text-white block uppercase">1. Front Surface (PDP)</span>
                    <span className="font-mono text-[10px] text-zinc-500">Mandatory: Net Qty, MRP, Brand</span>
                  </div>
                )}
              </div>

              {/* Surface 2: Back Information Panel */}
              <div
                onClick={() => backInputRef.current?.click()}
                className="relative h-[320px] bg-zinc-950/80 border-2 border-dashed border-zinc-800 hover:border-[#FF1E1E]/50 rounded-lg flex flex-col items-center justify-center p-4 text-center cursor-pointer transition overflow-hidden group"
              >
                <input
                  type="file"
                  ref={backInputRef}
                  onChange={(e) => {
                    if (e.target.files?.[0]) {
                      setBackFile(e.target.files[0]);
                      setBackPreview(URL.createObjectURL(e.target.files[0]));
                      setResult(null);
                    }
                  }}
                  accept="image/*"
                  className="hidden"
                />

                {backPreview ? (
                  <img src={backPreview} alt="Back Panel" className="w-full h-full object-contain" />
                ) : (
                  <div className="space-y-2">
                    <UploadCloud className="w-8 h-8 text-zinc-500 group-hover:text-white mx-auto group-hover:scale-110 transition" />
                    <span className="font-mono text-xs font-bold text-white block uppercase">2. Back Information Panel (Optional)</span>
                    <span className="font-mono text-[10px] text-zinc-500">Consumer Care, Barcode, Mfg Details</span>
                  </div>
                )}
              </div>
            </div>

            {/* Run Button */}
            <button
              disabled={!frontFile || loading}
              onClick={handleAnalyze}
              className="w-full py-3.5 bg-[#FF1E1E] hover:bg-[#d91616] disabled:opacity-40 text-white font-mono uppercase font-black tracking-wider text-xs rounded-lg transition shadow-lg shadow-[#FF1E1E]/20 flex items-center justify-center gap-2"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              <span>{loading ? 'Performing Multi-Angle Optical Audit...' : `Execute Comprehensive Audit (${category === 'food' ? 'Food' : 'Drugs/Commodities'})`}</span>
            </button>

            {/* Results Section */}
            {result && (
              <div className="p-6 bg-zinc-950 border border-zinc-900 rounded-lg space-y-6 font-mono text-xs">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-900 pb-4">
                  <div>
                    <div className="flex items-center gap-3">
                      <span className="text-base font-black uppercase text-white">
                        <span className="text-[#FF1E1E]">++</span>Audit: {result.product_name}
                      </span>
                      <span
                        className={`px-2.5 py-0.5 rounded text-[10px] font-bold uppercase border ${
                          status === 'COMPLIANT'
                            ? 'bg-emerald-950/60 border-emerald-800 text-emerald-400'
                            : status === 'WARNING'
                            ? 'bg-amber-950/60 border-amber-800 text-amber-400'
                            : 'bg-red-950/60 border-red-800 text-[#FF1E1E]'
                        }`}
                      >
                        {status} ({score}%)
                      </span>
                    </div>
                    <span className="text-zinc-500 text-[11px] block mt-0.5">
                      Ref: {result.scan_id} • Barcode: {barcode.code} ({barcode.country})
                    </span>
                  </div>

                  <button
                    onClick={() => window.open(`http://localhost:8000/api/v1/scans/${result.scan_id}/export-pdf`, '_blank')}
                    className="px-4 py-2 bg-[#FF1E1E] hover:bg-[#d91616] text-white rounded font-bold text-xs uppercase flex items-center gap-2 transition"
                  >
                    <DownloadCloud className="w-4 h-4" />
                    <span>Statutory PDF</span>
                  </button>
                </div>

                {/* Consumer Care & GS1 Integrity Checks */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 bg-zinc-900/60 border border-zinc-800 rounded">
                    <div className="flex items-center gap-2 font-bold text-white mb-2">
                      <PhoneCall className="w-4 h-4 text-[#FF1E1E]" />
                      <span>Rule 6(1)(h) Consumer Redressal Audit</span>
                    </div>
                    <div className="space-y-1 text-zinc-400 text-[11px]">
                      <div>Helpline Phone: <span className="text-white font-bold">{care.extracted_phone}</span></div>
                      <div>Helpline Email: <span className="text-white font-bold">{care.extracted_email}</span></div>
                      <div>Officer / Cell Designated: <span className="text-white font-bold">{care.has_person_or_designation ? 'YES' : 'NO / MISSING'}</span></div>
                    </div>
                  </div>

                  <div className="p-4 bg-zinc-900/60 border border-zinc-800 rounded">
                    <div className="flex items-center gap-2 font-bold text-white mb-2">
                      <ShieldCheck className="w-4 h-4 text-emerald-400" />
                      <span>GS1 Barcode Country Verification</span>
                    </div>
                    <div className="space-y-1 text-zinc-400 text-[11px]">
                      <div>Decoded Code: <span className="text-white font-bold">{barcode.code}</span></div>
                      <div>GS1 India Registered (890): <span className="text-white font-bold">{barcode.is_gs1_india ? 'YES (Valid Prefix)' : 'NO / International'}</span></div>
                      <div>Origin Reconciliation: <span className="text-emerald-400 font-bold">{barcode.origin_verified}</span></div>
                    </div>
                  </div>
                </div>

                {/* Declarations Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 text-zinc-300">
                  <div className="p-3 bg-zinc-900/60 border border-zinc-800 rounded">
                    <span className="text-zinc-500 block text-[10px]">BRAND</span>
                    <span className="font-bold text-white">{declarations.brand_name || 'MISSING'}</span>
                  </div>
                  <div className="p-3 bg-zinc-900/60 border border-zinc-800 rounded">
                    <span className="text-zinc-500 block text-[10px]">NET QUANTITY</span>
                    <span className="font-bold text-white">{declarations.net_quantity || 'MISSING'}</span>
                  </div>
                  <div className="p-3 bg-zinc-900/60 border border-zinc-800 rounded">
                    <span className="text-zinc-500 block text-[10px]">MRP (INCL TAX)</span>
                    <span className="font-bold text-white">{declarations.mrp || 'MISSING'}</span>
                  </div>
                  <div className="p-3 bg-zinc-900/60 border border-zinc-800 rounded">
                    <span className="text-zinc-500 block text-[10px]">UNIT SALE PRICE</span>
                    <span className="font-bold text-white">{declarations.unit_sale_price || 'MISSING'}</span>
                  </div>
                  <div className="p-3 bg-zinc-900/60 border border-zinc-800 rounded">
                    <span className="text-zinc-500 block text-[10px]">MFG DATE</span>
                    <span className="font-bold text-white">{declarations.mfg_date || 'MISSING'}</span>
                  </div>
                  <div className="p-3 bg-zinc-900/60 border border-zinc-800 rounded">
                    <span className="text-zinc-500 block text-[10px]">EXPIRY DATE</span>
                    <span className="font-bold text-white">{declarations.expiry_date || 'MISSING'}</span>
                  </div>
                  <div className="p-3 bg-zinc-900/60 border border-zinc-800 rounded">
                    <span className="text-zinc-500 block text-[10px]">BATCH NO</span>
                    <span className="font-bold text-white">{declarations.batch_number || 'MISSING'}</span>
                  </div>

                  {category === 'food' && (
                    <div className="p-3 bg-zinc-900/60 border border-zinc-800 rounded">
                      <span className="text-zinc-500 block text-[10px]">FSSAI LICENSE</span>
                      <span className="font-bold text-white">{declarations.fssai_license || 'MISSING'}</span>
                    </div>
                  )}

                  <div className="p-3 bg-zinc-900/60 border border-zinc-800 rounded">
                    <span className="text-zinc-500 block text-[10px]">COUNTRY OF ORIGIN</span>
                    <span className="font-bold text-white">{declarations.country_of_origin || 'India'}</span>
                  </div>
                </div>
              </div>
            )}
          </main>
        </div>
      </div>
    </div>
  );
}