import React, { useEffect, useState } from 'react';
import { BookOpen, Layers } from 'lucide-react';
import { fetchRulesSummary } from '../services/api';

export default function SettingsPage() {
  const [rules, setRules] = useState<any[]>([]);

  useEffect(() => {
    fetchRulesSummary()
      .then((data) => setRules(data.rules || []))
      .catch(() => {});
  }, []);

  return (
    <div className="min-h-screen bg-slate-100 p-7 font-sans">
      <div className="max-w-5xl mx-auto">
        <div className="flex justify-between items-center mb-5">
          <div>
            <h1 className="text-xl font-bold text-slate-900">Codified Regulatory Matrix</h1>
            <p className="text-xs text-slate-500 mt-0.5">
              Active statutory requirements under Legal Metrology (Packaged Commodities) Rules, 2011.
            </p>
          </div>
          <a href="/dashboard" className="text-xs font-bold text-slate-600 hover:text-slate-900">
            &larr; Return to Dashboard
          </a>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm mb-5">
          <div className="flex items-center space-x-2 mb-2.5">
            <BookOpen className="w-4 h-4 text-blue-600" />
            <h2 className="font-bold text-xs text-slate-900">Rule 7: Table 1 - Minimum Font Height Requirements</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-[11px]">
              <thead>
                <tr className="bg-slate-50 border-b text-slate-500 uppercase font-bold text-[10px]">
                  <th className="p-2.5">Area of PDP (A)</th>
                  <th className="p-2.5">Min Height (&le; 200g / 200ml)</th>
                  <th className="p-2.5">Min Height (&gt; 200g / 200ml)</th>
                  <th className="p-2.5">Blown/Moulded Containers</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                <tr><td className="p-2.5 font-semibold">A &le; 50 cm²</td><td className="p-2.5">1.0 mm</td><td className="p-2.5">1.5 mm</td><td className="p-2.5">2.0 mm</td></tr>
                <tr><td className="p-2.5 font-semibold">50 cm² &lt; A &le; 100 cm²</td><td className="p-2.5">1.5 mm</td><td className="p-2.5">2.0 mm</td><td className="p-2.5">3.0 mm</td></tr>
                <tr><td className="p-2.5 font-semibold">100 cm² &lt; A &le; 500 cm²</td><td className="p-2.5">2.5 mm</td><td className="p-2.5">4.0 mm</td><td className="p-2.5">6.0 mm</td></tr>
                <tr><td className="p-2.5 font-semibold">A &gt; 500 cm²</td><td className="p-2.5">4.0 mm</td><td className="p-2.5">6.0 mm</td><td className="p-2.5">6.0 mm</td></tr>
              </tbody>
            </table>
          </div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center space-x-2 mb-2.5">
            <Layers className="w-4 h-4 text-slate-700" />
            <h2 className="font-bold text-xs text-slate-900">Codified Statutory Rules (Rule 1 to 34)</h2>
          </div>
          <div className="grid grid-cols-2 gap-2.5 text-xs">
            {rules.length === 0 ? (
              <p className="text-slate-400 p-2 text-[11px]">Loading statutory clauses from data engine...</p>
            ) : (
              rules.map((r, i) => (
                <div key={i} className="p-2.5 bg-slate-50 rounded-lg border border-slate-200">
                  <span className="font-bold text-blue-700 uppercase block text-[10px]">{r.rule_number}</span>
                  <p className="text-slate-700 mt-0.5 text-[11px] leading-tight">{r.title}</p>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}