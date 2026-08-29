import React from 'react';
import { AlertOctagon, AlertTriangle, Info } from 'lucide-react';
import { Violation } from '../services/api';

export default function ViolationCard({ code, severity, rule, detail }: Violation) {
  const isHigh = severity === 'HIGH';
  const isMed = severity === 'MEDIUM';

  return (
    <div
      className={`p-3.5 mb-2.5 rounded-lg border text-xs flex items-start space-x-3 transition-all ${
        isHigh
          ? 'bg-red-50/90 border-red-200 text-red-950'
          : isMed
          ? 'bg-amber-50/90 border-amber-200 text-amber-950'
          : 'bg-blue-50/90 border-blue-200 text-blue-950'
      }`}
    >
      <div className="mt-0.5 shrink-0">
        {isHigh ? (
          <AlertOctagon className="w-4 h-4 text-red-600" />
        ) : isMed ? (
          <AlertTriangle className="w-4 h-4 text-amber-600" />
        ) : (
          <Info className="w-4 h-4 text-blue-600" />
        )}
      </div>
      <div className="flex-1">
        <div className="flex items-center justify-between mb-1">
          <span className="font-bold tracking-tight uppercase px-1.5 py-0.5 rounded bg-white border border-slate-200 text-[10px]">
            {rule}
          </span>
          <span
            className={`text-[9px] font-black uppercase px-1.5 py-0.5 rounded ${
              isHigh ? 'bg-red-200 text-red-800' : 'bg-amber-200 text-amber-800'
            }`}
          >
            {severity}
          </span>
        </div>
        <p className="font-semibold text-slate-800 text-[11px]">{code.replace(/_/g, ' ')}</p>
        <p className="text-slate-600 mt-0.5 leading-snug">{detail}</p>
      </div>
    </div>
  );
}