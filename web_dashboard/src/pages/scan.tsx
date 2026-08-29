import React, { useState } from 'react';
import Head from 'next/head';
import AppLayout from '../components/AppLayout';
import ReportViewer from '../components/ReportViewer';
import { Upload, ScanLine, Loader2, Image as ImageIcon } from 'lucide-react';
import axios from 'axios';

export default function ScanPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [scanResult, setScanResult] = useState<any>(null);
  const [showModal, setShowModal] = useState(false);

  const [heightCm, setHeightCm] = useState<number>(15.0);
  const [widthCm, setWidthCm] = useState<number>(10.0);
  const [pdpType, setPdpType] = useState<string>('rectangular');
  const [brandName, setBrandName] = useState<string>('');
  const [commodityName, setCommodityName] = useState<string>('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
    }
  };

  const handleRunVerification = async () => {
    if (!selectedFile) return;

    setLoading(true);
    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('height_cm', heightCm.toString());
    formData.append('width_cm', widthCm.toString());
    formData.append('pdp_type', pdpType);
    if (brandName) formData.append('brand_name', brandName);
    if (commodityName) formData.append('commodity_name', commodityName);
    formData.append('inspector_id', 'INSP-402');

    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

    try {
      const response = await axios.post(`${baseUrl}/scans/analyze`, formData);
      setScanResult(response.data);
      setShowModal(true);
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      const errorMsg = typeof detail === 'string' ? detail : JSON.stringify(detail) || err.message;
      alert(`Verification Error: ${errorMsg}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppLayout>
      <Head>
        <title>Scan Product | METROCHECK</title>
      </Head>

      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header Title Section */}
        <div className="pb-2 flex items-center justify-between">
          <div>
            <div className="flex items-center space-x-3">
              <h1 className="text-2xl font-black text-slate-900 tracking-tight">
                AI Optical Compliance Scanner
              </h1>
              <span className="px-2.5 py-0.5 bg-blue-50 border border-blue-200 text-[#2541B2] text-[11px] font-bold rounded-md">
                PCR 2011 Verified
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Extract mandatory statutory declarations, verify font stroke thresholds, and identify Rule 6 contraventions.
            </p>
          </div>
        </div>

        {/* Scan Workbench */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          
          {/* Packaging Artwork Preview Box (8 cols) */}
          <div className="lg:col-span-8 bg-[#0A1128] rounded-2xl border border-slate-800/60 p-6 shadow-sm flex flex-col items-center justify-center min-h-[460px] relative overflow-hidden">
            {previewUrl ? (
              <img
                src={previewUrl}
                alt="Packaging Artwork"
                className="max-h-[410px] w-auto object-contain rounded-xl shadow-lg"
              />
            ) : (
              <div className="flex flex-col items-center justify-center text-slate-500 space-y-3">
                <div className="w-16 h-16 rounded-2xl bg-slate-900/80 border border-slate-800 flex items-center justify-center">
                  <ImageIcon className="w-8 h-8 text-slate-600 stroke-[1.5]" />
                </div>
                <p className="text-xs font-semibold tracking-wide text-slate-400">
                  No packaging image selected
                </p>
              </div>
            )}
          </div>

          {/* Form & Controls Panel (4 cols) */}
          <div className="lg:col-span-4 space-y-4">
            
            {/* Dimensions & PDP Type */}
            <div className="bg-white rounded-2xl border border-slate-100 p-5 shadow-sm space-y-3.5">
              <h2 className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                Calibrated PDP Parameters
              </h2>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    Height (cm)
                  </label>
                  <input
                    type="number"
                    value={heightCm}
                    onChange={(e) => setHeightCm(Number(e.target.value))}
                    className="w-full px-3 py-2 text-xs font-mono font-bold bg-slate-50 border border-slate-200/80 rounded-xl focus:outline-none focus:border-blue-600 focus:bg-white text-slate-900 transition"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    Width (cm)
                  </label>
                  <input
                    type="number"
                    value={widthCm}
                    onChange={(e) => setWidthCm(Number(e.target.value))}
                    className="w-full px-3 py-2 text-xs font-mono font-bold bg-slate-50 border border-slate-200/80 rounded-xl focus:outline-none focus:border-blue-600 focus:bg-white text-slate-900 transition"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  PDP Configuration
                </label>
                <select
                  value={pdpType}
                  onChange={(e) => setPdpType(e.target.value)}
                  className="w-full px-3 py-2 text-xs font-semibold bg-slate-50 border border-slate-200/80 rounded-xl focus:outline-none focus:border-blue-600 focus:bg-white text-slate-900 transition"
                >
                  <option value="rectangular">Rectangular (Height × Width)</option>
                  <option value="cylindrical">Cylindrical (40% × Height × Circumference)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Brand Name (Optional)
                </label>
                <input
                  type="text"
                  placeholder="e.g. Britannia, Nestle, Amul"
                  value={brandName}
                  onChange={(e) => setBrandName(e.target.value)}
                  className="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-200/80 rounded-xl focus:outline-none focus:border-blue-600 focus:bg-white text-slate-900 transition"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Commodity Name (Optional)
                </label>
                <input
                  type="text"
                  placeholder="e.g. Packaged Milk, Biscuits, Oil"
                  value={commodityName}
                  onChange={(e) => setCommodityName(e.target.value)}
                  className="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-200/80 rounded-xl focus:outline-none focus:border-blue-600 focus:bg-white text-slate-900 transition"
                />
              </div>
            </div>

            {/* Action Buttons */}
            <div className="bg-white rounded-2xl border border-slate-100 p-5 shadow-sm space-y-3">
              <label className="w-full flex items-center justify-center space-x-2 px-4 py-3 bg-[#2541B2] hover:bg-blue-700 text-white text-xs font-bold rounded-xl cursor-pointer transition shadow-sm">
                <Upload className="w-4 h-4" />
                <span>Select Packaging Artwork</span>
                <input type="file" accept="image/*" onChange={handleFileChange} className="hidden" />
              </label>

              <button
                onClick={handleRunVerification}
                disabled={!selectedFile || loading}
                className="w-full flex items-center justify-center space-x-2 px-4 py-3 bg-[#0A1128] hover:bg-slate-900 text-white text-xs font-bold rounded-xl disabled:opacity-40 disabled:cursor-not-allowed transition shadow-sm"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Auditing Declarations...</span>
                  </>
                ) : (
                  <>
                    <ScanLine className="w-4 h-4" />
                    <span>Run Statutory Verification</span>
                  </>
                )}
              </button>

              {selectedFile && (
                <p className="text-[11px] text-center font-mono text-slate-400 truncate mt-1">
                  {selectedFile.name}
                </p>
              )}
            </div>

          </div>
        </div>
      </div>

      {/* Audit Report Modal */}
      {showModal && scanResult && (
        <ReportViewer scan={scanResult} onClose={() => setShowModal(false)} />
      )}
    </AppLayout>
  );
}