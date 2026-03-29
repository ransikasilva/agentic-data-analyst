/**
 * ChartPanel component for displaying generated charts.
 */

import { useState } from 'react';
import { useAgentStore } from '../store/useAgentStore';
import { Download, X, Maximize2 } from 'lucide-react';

export function ChartPanel() {
  const { charts } = useAgentStore();
  const [selectedChart, setSelectedChart] = useState<number | null>(null);

  const handleDownload = (chartBase64: string, index: number) => {
    const link = document.createElement('a');
    link.href = `data:image/png;base64,${chartBase64}`;
    link.download = `chart_${index + 1}.png`;
    link.click();
  };

  if (charts.length === 0) {
    return null;
  }

  return (
    <>
      <div className="bg-white rounded-xl border border-gray-200 shadow-lg overflow-hidden animate-fadeIn">
        <div className="bg-gradient-to-r from-emerald-50 to-teal-50 px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-bold text-gray-900">Generated Charts</h3>
              <p className="text-xs text-gray-600 mt-1">{charts.length} visualization{charts.length !== 1 ? 's' : ''} created</p>
            </div>
          </div>
        </div>

        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {charts.map((chart, idx) => (
              <div
                key={idx}
                className="relative group border-2 border-gray-200 rounded-xl overflow-hidden hover:shadow-xl hover:border-blue-300 transition-all duration-300 bg-white animate-scaleIn"
                style={{ animationDelay: `${idx * 0.1}s` }}
              >
                <img
                  src={`data:image/png;base64,${chart}`}
                  alt={`Chart ${idx + 1}`}
                  className="w-full h-auto cursor-pointer transition-transform duration-300 group-hover:scale-105"
                  onClick={() => setSelectedChart(idx)}
                />

                <div className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-all duration-300 flex gap-2">
                  <button
                    onClick={() => setSelectedChart(idx)}
                    className="p-2.5 bg-white/95 backdrop-blur-sm rounded-lg shadow-lg hover:bg-blue-50 hover:shadow-xl transition-all duration-200 border border-gray-200"
                    title="View fullscreen"
                  >
                    <Maximize2 className="w-4 h-4 text-gray-700" />
                  </button>
                  <button
                    onClick={() => handleDownload(chart, idx)}
                    className="p-2.5 bg-white/95 backdrop-blur-sm rounded-lg shadow-lg hover:bg-green-50 hover:shadow-xl transition-all duration-200 border border-gray-200"
                    title="Download"
                  >
                    <Download className="w-4 h-4 text-gray-700" />
                  </button>
                </div>

                <div className="px-4 py-3 bg-gradient-to-r from-gray-50 to-gray-100 border-t-2 border-gray-200">
                  <p className="text-sm text-gray-700 font-bold">Chart {idx + 1}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {selectedChart !== null && (
        <div
          className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 animate-fadeIn"
          onClick={() => setSelectedChart(null)}
        >
          <div className="relative max-w-7xl max-h-full animate-scaleIn" onClick={(e) => e.stopPropagation()}>
            <button
              onClick={() => setSelectedChart(null)}
              className="absolute -top-12 right-0 text-white hover:text-gray-300 transition-all hover:scale-110 p-2 bg-white/10 rounded-lg backdrop-blur-sm"
              title="Close"
            >
              <X className="w-8 h-8" />
            </button>

            <img
              src={`data:image/png;base64,${charts[selectedChart]}`}
              alt={`Chart ${selectedChart + 1}`}
              className="max-w-full max-h-[85vh] rounded-xl shadow-2xl border-4 border-white/20"
            />

            <button
              onClick={() => handleDownload(charts[selectedChart], selectedChart)}
              className="absolute bottom-6 right-6 px-6 py-3 bg-white rounded-xl shadow-xl hover:bg-gray-100 transition-all hover:scale-105 flex items-center gap-2 font-bold text-gray-800 border-2 border-gray-200"
            >
              <Download className="w-5 h-5" />
              Download Chart
            </button>
          </div>
        </div>
      )}
    </>
  );
}
