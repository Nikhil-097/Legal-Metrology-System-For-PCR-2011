import React, { useState } from 'react';
import Link from 'next/link';
import { ArrowLeft, Save, Sliders, Shield, Database, Cpu } from 'lucide-react';

export default function SettingsPage() {
  const [model, setModel] = useState('gemini-3.6-flash');
  const [ocrConfidence, setOcrConfidence] = useState('0.75');
  const [enableStrictMode, setEnableStrictMode] = useState(true);

  return (
    <div className="min-h-screen bg-[#070708] text-white flex flex-col font-sans selection:bg-[#FF1E1E] selection:text-white">
      {/* Background Ambience */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-[-10%] left-[20%] w-[600px] h-[600px] bg-[#FF1E1E]/15 rounded-full blur-[160px]" />
        <div className="absolute inset-0 bg-[radial-gradient(#1c1c20_1px,transparent_1px)] [background-size:28px_28px] opacity-40" />
      </div>

      <div className="relative z-10 flex-1 max-w-[1200px] w-full mx-auto p-6 sm:p-10 flex flex-col space-y-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-900 pb-6">
          <div>
            <div className="flex items-center gap-3">
              <Link href="/dashboard" className="text-zinc-500 hover:text-white transition">
                <ArrowLeft className="w-5 h-5" />
              </Link>
              <h1 className="text-3xl font-black uppercase tracking-tight text-white flex items-center gap-2">
                <span className="text-[#FF1E1E]">++</span>System Configuration
              </h1>
            </div>
            <p className="mt-1 text-xs font-mono text-zinc-500 pl-8">
              Adjust LLM inference engines, vision confidence parameters, and statutory rule schedules.
            </p>
          </div>

          <Link
            href="/dashboard"
            className="px-4 py-2 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-300 hover:text-white text-xs font-mono uppercase tracking-wider rounded transition self-start sm:self-auto"
          >
            ← Return to Dashboard
          </Link>
        </div>

        {/* Configuration Sections */}
        <div className="space-y-6">
          {/* Vision Model Selection */}
          <div className="p-6 bg-zinc-950 border border-zinc-900 rounded-lg space-y-4">
            <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-widest text-zinc-300 font-bold border-b border-zinc-900 pb-3">
              <Cpu className="w-4 h-4 text-[#FF1E1E]" />
              <span>Vision Inference Pipeline</span>
            </div>

            <div className="space-y-4 font-mono text-xs">
              <div>
                <label className="text-zinc-400 block mb-1.5 uppercase text-[11px]">Active LLM Engine</label>
                <select
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  className="w-full bg-zinc-900 border border-zinc-800 rounded px-3 py-2 text-white focus:border-[#FF1E1E] focus:outline-none transition"
                >
                  <option value="gemini-3.6-flash">gemini-3.6-flash (Recommended / Fast)</option>
                  <option value="gemini-3.7-flash">gemini-3.7-flash</option>
                  <option value="gemini-3.1-pro-preview">gemini-3.1-pro-preview</option>
                </select>
              </div>

              <div>
                <label className="text-zinc-400 block mb-1.5 uppercase text-[11px]">OCR Confidence Threshold</label>
                <input
                  type="text"
                  value={ocrConfidence}
                  onChange={(e) => setOcrConfidence(e.target.value)}
                  className="w-full bg-zinc-900 border border-zinc-800 rounded px-3 py-2 text-white focus:border-[#FF1E1E] focus:outline-none transition"
                />
              </div>
            </div>
          </div>

          {/* Compliance Verification Rules */}
          <div className="p-6 bg-zinc-950 border border-zinc-900 rounded-lg space-y-4">
            <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-widest text-zinc-300 font-bold border-b border-zinc-900 pb-3">
              <Shield className="w-4 h-4 text-[#FF1E1E]" />
              <span>Statutory Rule Verification</span>
            </div>

            <div className="space-y-3 font-mono text-xs">
              <label className="flex items-center space-x-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={enableStrictMode}
                  onChange={(e) => setEnableStrictMode(e.target.checked)}
                  className="accent-[#FF1E1E] w-4 h-4"
                />
                <span className="text-zinc-300">Enforce strict PCR 2011 Table 1 font-height bounding compliance</span>
              </label>
            </div>
          </div>

          {/* Save Action */}
          <div className="flex justify-end">
            <button
              type="button"
              className="px-6 py-3 bg-[#FF1E1E] hover:bg-[#d91616] text-white font-bold text-xs uppercase tracking-widest rounded transition flex items-center gap-2 shadow-lg shadow-[#FF1E1E]/20"
            >
              <Save className="w-4 h-4" />
              <span>Save Configuration</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}