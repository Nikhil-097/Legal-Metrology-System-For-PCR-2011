import React, { useState } from 'react';
import { ShieldCheck, AlertOctagon, AlertTriangle, X, Download, Loader2 } from 'lucide-react';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';

interface ReportViewerProps {
  scan: any;
  onClose: () => void;
}

export default function ReportViewer({ scan, onClose }: ReportViewerProps) {
  const [generatingPdf, setGeneratingPdf] = useState(false);

  const d = scan?.extracted_declarations || scan?.extracted_data || scan?.data || scan || {};

  const netQty = d.net_quantity || 'MISSING';
  const mrpVal = d.mrp || 'MISSING';
  const hasTax = d.has_tax_clause === true || d.tax_inclusivity_phrase === 'Present';
  const uspVal = d.unit_sale_price || 'MISSING';
  const mfgVal = d.mfg_date || 'MISSING';
  const originVal = d.country_of_origin || 'India (Presumed / Domestic)';

  let infractions: any[] = [];
  if (Array.isArray(scan?.violations) && scan.violations.length > 0) {
    infractions = scan.violations;
  } else {
    if (netQty === 'MISSING' || netQty.toLowerCase().includes('gm')) {
      infractions.push({
        rule: 'Rule 6(1)(d) & Rule 13',
        code: netQty.toLowerCase().includes('gm') ? 'ILLEGAL_METRIC_SYMBOL' : 'NET_QUANTITY_MISSING',
        detail: "Standard SI unit ('g' or 'kg') required.",
      });
    }
    if (mrpVal === 'MISSING') infractions.push({ rule: 'Rule 6(1)(e)', code: 'MRP_MISSING', detail: 'Maximum Retail Price missing.' });
    if (!hasTax) infractions.push({ rule: 'Rule 6(1)(e)', code: 'TAX_INCLUSIVITY_MISSING', detail: "Clause '(Inclusive of all taxes)' missing." });
    if (uspVal === 'MISSING') infractions.push({ rule: 'Rule 6(11)', code: 'MISSING_USP', detail: 'Unit Sale Price (USP) declaration absent.' });
    if (mfgVal === 'MISSING') infractions.push({ rule: 'Rule 6(1)(f)', code: 'MFG_DATE_MISSING', detail: 'Date of Packaging/Manufacture missing.' });
  }

  const isCompliant = infractions.length === 0;
  const score = isCompliant ? 100 : Math.max(0, 100 - infractions.length * 18);
  const scanId = scan?.scan_id ? String(scan.scan_id).substring(0, 8).toUpperCase() : '28AE4F7F';

  const handleExportPdf = () => {
    setGeneratingPdf(true);
    try {
      const doc = new jsPDF();
      doc.setFillColor(10, 17, 40);
      doc.rect(0, 0, 210, 28, 'F');

      doc.setFont('helvetica', 'bold');
      doc.setFontSize(13);
      doc.setTextColor(255, 255, 255);
      doc.text('METROCHECK • STATUTORY AUDIT CERTIFICATE', 14, 18);

      autoTable(doc, {
        startY: 38,
        theme: 'grid',
        headStyles: { fillColor: [10, 17, 40], textColor: [255, 255, 255] },
        head: [['Statutory Declaration (Rule 6)', 'Evaluated Label Value', 'Compliance Status']],
        body: [
          ['Net Quantity (Rule 6(1)(d))', String(netQty), netQty !== 'MISSING' ? 'COMPLIANT' : 'BREACH'],
          ['Maximum Retail Price (Rule 6(1)(e))', String(mrpVal), mrpVal !== 'MISSING' ? 'COMPLIANT' : 'BREACH'],
          ['Tax Inclusivity Clause', hasTax ? 'Present' : 'MISSING', hasTax ? 'COMPLIANT' : 'BREACH'],
          ['Unit Sale Price (Rule 6(11))', String(uspVal), uspVal !== 'MISSING' ? 'COMPLIANT' : 'BREACH'],
          ['Date of Packing (Rule 6(1)(f))', String(mfgVal), mfgVal !== 'MISSING' ? 'COMPLIANT' : 'BREACH'],
          ['Country of Origin (Rule 6(10))', String(originVal), 'COMPLIANT'],
        ],
        styles: { fontSize: 9 },
      });

      doc.save(`Inspection_Report_SCN_${scanId}.pdf`);
    } catch (e) {
      alert(`PDF Generation failed: ${e}`);
    } finally {
      setGeneratingPdf(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-4xl w-full max-h-[90vh] flex flex-col overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
          <div>
            <h2 className="text-base font-black text-slate-900">Legal Metrology Verification Trail</h2>
            <p className="text-xs text-slate-400 font-mono">SCN-{scanId}</p>
          </div>
          <button onClick={onClose} className="p-2 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 overflow-y-auto space-y-5 text-xs">
          <div
            className={`p-4 rounded-xl border flex items-center justify-between ${
              isCompliant ? 'bg-emerald-50 border-emerald-200 text-emerald-900' : 'bg-rose-50 border-rose-200 text-rose-900'
            }`}
          >
            <div className="flex items-center space-x-3">
              {isCompliant ? <ShieldCheck className="w-6 h-6 text-emerald-600 shrink-0" /> : <AlertOctagon className="w-6 h-6 text-rose-600 shrink-0" />}
              <div>
                <p className="font-bold text-sm">{isCompliant ? 'Statutory Compliance Certified' : 'Infractions Detected'}</p>
                <p className="text-[11px] opacity-80">Compliance Rating: {score}%</p>
              </div>
            </div>
            <span
              className={`px-3 py-1 rounded-full text-[10px] font-black uppercase ${
                isCompliant ? 'bg-emerald-200/60 text-emerald-800' : 'bg-rose-200/60 text-rose-800'
              }`}
            >
              {infractions.length} Infraction{infractions.length === 1 ? '' : 's'}
            </span>
          </div>

          <div>
            <h3 className="font-bold text-slate-400 uppercase tracking-wider text-[10px] mb-2">
              Extracted Declarations (Rule 6)
            </h3>
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 bg-slate-50/60 rounded-xl border border-slate-200/80 flex justify-between items-center">
                <span className="font-medium text-slate-500">Declared Net Qty:</span>
                <span className={`font-bold font-mono ${netQty !== 'MISSING' ? 'text-emerald-700' : 'text-rose-600'}`}>{netQty}</span>
              </div>

              <div className="p-3 bg-slate-50/60 rounded-xl border border-slate-200/80 flex justify-between items-center">
                <span className="font-medium text-slate-500">Maximum Retail Price:</span>
                <span className={`font-bold font-mono ${mrpVal !== 'MISSING' ? 'text-emerald-700' : 'text-rose-600'}`}>{mrpVal}</span>
              </div>

              <div className="p-3 bg-slate-50/60 rounded-xl border border-slate-200/80 flex justify-between items-center">
                <span className="font-medium text-slate-500">Tax Inclusivity Phrase:</span>
                <span className={`font-bold font-mono ${hasTax ? 'text-emerald-700' : 'text-rose-600'}`}>{hasTax ? 'Present' : 'MISSING'}</span>
              </div>

              <div className="p-3 bg-slate-50/60 rounded-xl border border-slate-200/80 flex justify-between items-center">
                <span className="font-medium text-slate-500">Unit Sale Price (USP):</span>
                <span className={`font-bold font-mono ${uspVal !== 'MISSING' ? 'text-emerald-700' : 'text-rose-600'}`}>{uspVal}</span>
              </div>

              <div className="p-3 bg-slate-50/60 rounded-xl border border-slate-200/80 flex justify-between items-center">
                <span className="font-medium text-slate-500">Date of Packing:</span>
                <span className={`font-bold font-mono ${mfgVal !== 'MISSING' ? 'text-emerald-700' : 'text-rose-600'}`}>{mfgVal}</span>
              </div>

              <div className="p-3 bg-slate-50/60 rounded-xl border border-slate-200/80 flex justify-between items-center">
                <span className="font-medium text-slate-500">Country of Origin:</span>
                <span className="font-bold font-mono text-emerald-700">{originVal}</span>
              </div>
            </div>
          </div>

          {infractions.length > 0 && (
            <div>
              <h3 className="font-bold text-slate-400 uppercase tracking-wider text-[10px] mb-2">
                Itemized Non-Compliance Notices ({infractions.length})
              </h3>
              <div className="space-y-2">
                {infractions.map((v: any, idx: number) => (
                  <div key={idx} className="p-3 bg-rose-50/50 rounded-xl border border-rose-200/80 flex items-start space-x-2.5">
                    <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                    <div>
                      <span className="font-bold text-rose-900 font-mono text-[11px]">
                        {v.rule} - {v.code}
                      </span>
                      <p className="text-slate-600 text-[11px] mt-0.5">{v.detail}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3.5 border-t border-slate-100 flex items-center justify-between bg-slate-50/50">
          <button onClick={onClose} className="px-4 py-2 text-xs font-bold text-slate-600 hover:text-slate-900 transition">
            Close
          </button>
          <button
            onClick={handleExportPdf}
            disabled={generatingPdf}
            className="px-4 py-2 bg-[#0A1128] hover:bg-slate-900 text-white text-xs font-bold rounded-xl flex items-center space-x-2 transition shadow-sm"
          >
            {generatingPdf ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Download className="w-3.5 h-3.5" />}
            <span>Export Inspection PDF</span>
          </button>
        </div>
      </div>
    </div>
  );
}