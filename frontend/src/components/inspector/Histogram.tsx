import React, { useEffect, useState, useRef } from 'react';
import { Activity } from 'lucide-react';
import { resolveMediaUrl } from '../../api/client';

interface HistogramProps {
  imageUrl: string;
}

export const Histogram: React.FC<HistogramProps> = ({ imageUrl }) => {
  const [data, setData] = useState<{
    r: number[];
    g: number[];
    b: number[];
    lum: number[];
  } | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let active = true;
    if (!imageUrl) {
      setData(null);
      return;
    }

    setLoading(true);
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.src = resolveMediaUrl(imageUrl);

    img.onload = () => {
      if (!active) return;
      try {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d', { willReadFrequently: true });
        if (!ctx) {
          setLoading(false);
          return;
        }

        // Downsample to 128x128 for instantaneous, lag-free histogram calculation
        const sampleSize = 128;
        canvas.width = sampleSize;
        canvas.height = sampleSize;
        ctx.drawImage(img, 0, 0, sampleSize, sampleSize);

        const imgData = ctx.getImageData(0, 0, sampleSize, sampleSize).data;
        const buckets = 64; // 64 bin histogram for silky smooth SVG curve
        const rBins = new Array(buckets).fill(0);
        const gBins = new Array(buckets).fill(0);
        const bBins = new Array(buckets).fill(0);
        const lumBins = new Array(buckets).fill(0);

        const totalPixels = sampleSize * sampleSize;
        for (let i = 0; i < imgData.length; i += 4) {
          const r = imgData[i];
          const g = imgData[i + 1];
          const b = imgData[i + 2];
          const lum = Math.round(0.299 * r + 0.587 * g + 0.114 * b);

          const rIdx = Math.min(buckets - 1, Math.floor((r / 256) * buckets));
          const gIdx = Math.min(buckets - 1, Math.floor((g / 256) * buckets));
          const bIdx = Math.min(buckets - 1, Math.floor((b / 256) * buckets));
          const lumIdx = Math.min(buckets - 1, Math.floor((lum / 256) * buckets));

          rBins[rIdx]++;
          gBins[gIdx]++;
          bBins[bIdx]++;
          lumBins[lumIdx]++;
        }

        const maxVal = Math.max(...rBins, ...gBins, ...bBins, ...lumBins, 1);
        setData({
          r: rBins.map((v) => v / maxVal),
          g: gBins.map((v) => v / maxVal),
          b: bBins.map((v) => v / maxVal),
          lum: lumBins.map((v) => v / maxVal),
        });
      } catch {
        // Fallback gracefully on CORS/tainted canvas
        setData(null);
      } finally {
        if (active) setLoading(false);
      }
    };

    img.onerror = () => {
      if (active) {
        setData(null);
        setLoading(false);
      }
    };

    return () => {
      active = false;
    };
  }, [imageUrl]);

  const generateSvgPath = (bins: number[], width: number, height: number): string => {
    if (!bins || bins.length === 0) return '';
    const step = width / (bins.length - 1);
    let d = `M 0 ${height}`;
    bins.forEach((val, i) => {
      const x = i * step;
      // Exponential smoothing for natural optical representation
      const y = height - Math.pow(val, 0.7) * (height - 4);
      d += ` L ${x.toFixed(1)} ${y.toFixed(1)}`;
    });
    d += ` L ${width} ${height} Z`;
    return d;
  };

  return (
    <div className="p-3.5 rounded-2xl bg-black/[0.03] border border-black/[0.06] space-y-2 select-none">
      <div className="flex items-center justify-between text-[11px] font-semibold text-[#86868B] lowercase">
        <div className="flex items-center gap-1.5 text-[#1D1D1F]">
          <Activity className="w-3.5 h-3.5 text-[#0071E3]" />
          <span>histogram</span>
        </div>
        <div className="flex items-center gap-2 text-[9px] font-mono lowercase">
          <span className="flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-500" /> r
          </span>
          <span className="flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" /> g
          </span>
          <span className="flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-500" /> b
          </span>
          <span className="flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-neutral-400" /> lum
          </span>
        </div>
      </div>

      <div className="relative w-full h-18 bg-black/[0.05] rounded-xl overflow-hidden flex items-end">
        {data ? (
          <svg
            viewBox="0 0 200 64"
            preserveAspectRatio="none"
            className="w-full h-full"
          >
            {/* Luminance fill */}
            <path
              d={generateSvgPath(data.lum, 200, 64)}
              fill="rgba(160, 160, 165, 0.25)"
              stroke="rgba(140, 140, 145, 0.6)"
              strokeWidth="0.8"
            />
            {/* Red channel */}
            <path
              d={generateSvgPath(data.r, 200, 64)}
              fill="rgba(244, 63, 94, 0.18)"
              stroke="rgba(244, 63, 94, 0.75)"
              strokeWidth="0.9"
            />
            {/* Green channel */}
            <path
              d={generateSvgPath(data.g, 200, 64)}
              fill="rgba(16, 185, 129, 0.18)"
              stroke="rgba(16, 185, 129, 0.75)"
              strokeWidth="0.9"
            />
            {/* Blue channel */}
            <path
              d={generateSvgPath(data.b, 200, 64)}
              fill="rgba(59, 130, 246, 0.18)"
              stroke="rgba(59, 130, 246, 0.75)"
              strokeWidth="0.9"
            />
          </svg>
        ) : (
          <div className="w-full h-full flex items-center justify-center text-[10px] text-[#86868B] lowercase">
            {loading ? 'calculating...' : 'no data'}
          </div>
        )}

        {/* Gradient grid lines for exposure zones: Shadows, Midtones, Highlights */}
        <div className="absolute inset-0 flex pointer-events-none border-t border-black/[0.04]">
          <div className="w-1/4 h-full border-r border-black/[0.04]" title="shadows" />
          <div className="w-2/4 h-full border-r border-black/[0.04]" title="midtones" />
          <div className="w-1/4 h-full" title="highlights" />
        </div>
      </div>
    </div>
  );
};
