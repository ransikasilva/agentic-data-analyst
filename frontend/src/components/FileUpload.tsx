/**
 * FileUpload component with drag-and-drop support.
 */

import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileSpreadsheet, Check } from 'lucide-react';
import { useAnalysis } from '../hooks/useAnalysis';
import { useAgentStore } from '../store/useAgentStore';

export function FileUpload() {
  const { uploadFile, isUploading } = useAnalysis();
  const { filename, dataPreview } = useAgentStore();

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        await uploadFile(acceptedFiles[0]);
      }
    },
    [uploadFile]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
    },
    multiple: false,
    disabled: isUploading,
  });

  return (
    <div className="w-full">
      <div
        {...getRootProps()}
        className={`
          relative border-2 border-dashed rounded-xl p-10 text-center cursor-pointer
          transition-all duration-300 ease-out
          ${
            isDragActive
              ? 'border-blue-500 bg-gradient-to-br from-blue-50 to-indigo-50 scale-105 shadow-lg'
              : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50 hover:shadow-md'
          }
          ${isUploading ? 'opacity-70 cursor-not-allowed pointer-events-none' : ''}
          ${filename ? 'border-green-500 bg-gradient-to-br from-green-50 to-emerald-50 shadow-md' : ''}
        `}
      >
        <input {...getInputProps()} />

        {/* Animated background effect on drag */}
        {isDragActive && (
          <div className="absolute inset-0 bg-blue-400 opacity-10 rounded-xl animate-pulse" />
        )}

        <div className="relative flex flex-col items-center gap-4">
          {filename ? (
            <>
              <div className="p-3 bg-green-100 rounded-full animate-scaleIn">
                <Check className="w-10 h-10 text-green-600" />
              </div>
              <div>
                <p className="text-xl font-bold text-green-700 mb-1">{filename}</p>
                {dataPreview && (
                  <div className="flex items-center justify-center gap-4 text-sm text-gray-600">
                    <span className="px-3 py-1 bg-white rounded-full shadow-sm">
                      <strong className="text-gray-900">{dataPreview.shape[0].toLocaleString()}</strong> rows
                    </span>
                    <span className="px-3 py-1 bg-white rounded-full shadow-sm">
                      <strong className="text-gray-900">{dataPreview.shape[1]}</strong> columns
                    </span>
                  </div>
                )}
              </div>
              <p className="text-sm text-gray-600 font-medium">Click or drop to replace</p>
            </>
          ) : (
            <>
              {isUploading ? (
                <>
                  <div className="relative">
                    <div className="animate-spin rounded-full h-14 w-14 border-4 border-blue-200" />
                    <div className="absolute inset-0 animate-spin rounded-full h-14 w-14 border-4 border-transparent border-t-blue-600" style={{ animationDuration: '0.8s' }} />
                  </div>
                  <p className="text-xl font-bold text-blue-700">Uploading...</p>
                  <p className="text-sm text-blue-600">Processing your file</p>
                </>
              ) : (
                <>
                  <div className={`p-4 rounded-full transition-all duration-300 ${
                    isDragActive ? 'bg-blue-100 scale-110' : 'bg-gray-100'
                  }`}>
                    <Upload className={`w-10 h-10 transition-colors duration-300 ${
                      isDragActive ? 'text-blue-600' : 'text-gray-400'
                    }`} />
                  </div>
                  <div>
                    <p className="text-xl font-bold text-gray-800 mb-1">
                      {isDragActive ? 'Release to upload' : 'Drag & Drop your file here'}
                    </p>
                    <p className="text-sm text-gray-500">
                      or <span className="text-blue-600 font-semibold">click to browse</span>
                    </p>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-gray-500 mt-2">
                    <span className="px-2 py-1 bg-white rounded border border-gray-200">.csv</span>
                    <span className="px-2 py-1 bg-white rounded border border-gray-200">.xlsx</span>
                    <span className="px-2 py-1 bg-white rounded border border-gray-200">.xls</span>
                    <span className="text-gray-400">•</span>
                    <span>Max 50MB</span>
                  </div>
                </>
              )}
            </>
          )}
        </div>
      </div>

      {dataPreview && (
        <div className="mt-6 bg-gradient-to-br from-white to-gray-50 rounded-xl border border-gray-200 shadow-md overflow-hidden animate-fadeIn">
          <div className="bg-gradient-to-r from-gray-50 to-gray-100 px-5 py-3 border-b border-gray-200">
            <h3 className="text-sm font-bold text-gray-800 flex items-center gap-2">
              <FileSpreadsheet className="w-5 h-5 text-gray-600" />
              Data Preview
              <span className="ml-auto text-xs font-normal text-gray-500">First 5 rows</span>
            </h3>
          </div>
          <div className="overflow-x-auto custom-scrollbar">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b-2 border-gray-200">
                  {dataPreview.columns.map((col) => (
                    <th key={col} className="text-left py-3 px-4 font-bold text-gray-800 whitespace-nowrap">
                      <div className="flex flex-col gap-1">
                        <span>{col}</span>
                        <span className="text-xs font-medium text-gray-500 bg-white px-2 py-0.5 rounded inline-block">
                          {dataPreview.dtypes[col]}
                        </span>
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {dataPreview.rows && dataPreview.rows.slice(0, 5).map((row, idx) => (
                  <tr key={idx} className="border-b border-gray-100 hover:bg-blue-50 transition-colors">
                    {dataPreview.columns.map((col) => (
                      <td key={col} className="py-3 px-4 text-gray-700 whitespace-nowrap">
                        {String(row[col] ?? 'null')}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
