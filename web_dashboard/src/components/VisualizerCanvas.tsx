import React, { useEffect, useRef } from 'react';
import { ScanResult } from '../services/api';

interface VisualizerProps {
  imageSrc: string;
  scanResult: ScanResult | null;
}

export default function VisualizerCanvas({ imageSrc, scanResult }: VisualizerProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    if (!canvasRef.current || !imageSrc) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.src = imageSrc;

    img.onload = () => {
      canvas.width = img.naturalWidth;
      canvas.height = img.naturalHeight;
      ctx.drawImage(img, 0, 0);

      if (scanResult) {
        const isCompliant = scanResult.is_compliant;
        ctx.lineWidth = Math.max(3, Math.round(canvas.width / 220));

        // Draw outer package bounding box
        ctx.strokeStyle = isCompliant ? '#16A34A' : '#DC2626';
        ctx.strokeRect(16, 16, canvas.width - 32, canvas.height - 32);

        // Render header badge
        const badgeWidth = Math.min(320, canvas.width * 0.6);
        ctx.fillStyle = isCompliant ? 'rgba(22, 163, 74, 0.9)' : 'rgba(220, 38, 38, 0.9)';
        ctx.fillRect(16, 16, badgeWidth, 42);

        ctx.font = 'bold 16px sans-serif';
        ctx.fillStyle = '#FFFFFF';
        ctx.fillText(
          isCompliant ? 'PCR 2011 COMPLIANT' : `${scanResult.violations.length} INFRACTIONS DETECTED`,
          28,
          43
        );
      }
    };
  }, [imageSrc, scanResult]);

  return (
    <div className="w-full h-full bg-slate-900 rounded-lg overflow-hidden flex items-center justify-center border border-slate-700 min-h-[380px] relative">
      <canvas ref={canvasRef} className="max-w-full max-h-[480px] object-contain" />
      {!imageSrc && (
        <p className="text-slate-500 text-xs italic">No packaging image selected</p>
      )}
    </div>
  );
}