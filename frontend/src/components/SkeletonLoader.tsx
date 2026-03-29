/**
 * Skeleton Loading Components
 */

export function TimelineSkeleton() {
  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-lg overflow-hidden animate-scaleIn">
      <div className="bg-gradient-to-r from-gray-300 to-gray-400 px-6 py-4">
        <div className="h-6 w-48 bg-gray-200 rounded skeleton" />
        <div className="h-4 w-32 bg-gray-200 rounded mt-2 skeleton" />
      </div>

      <div className="p-6 space-y-6">
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex gap-4">
            <div className="w-12 h-12 bg-gray-200 rounded-xl skeleton flex-shrink-0" />
            <div className="flex-1 space-y-3">
              <div className="h-6 w-32 bg-gray-200 rounded skeleton" />
              <div className="h-4 w-full bg-gray-200 rounded skeleton" />
              <div className="h-24 w-full bg-gray-200 rounded-lg skeleton" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function InsightSkeleton() {
  return (
    <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl border-2 border-blue-200 p-6 shadow-lg animate-scaleIn">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 bg-blue-200 rounded-lg skeleton" />
        <div className="h-6 w-48 bg-blue-200 rounded skeleton" />
      </div>
      <div className="space-y-3">
        <div className="h-4 w-full bg-blue-100 rounded skeleton" />
        <div className="h-4 w-5/6 bg-blue-100 rounded skeleton" />
        <div className="h-4 w-4/6 bg-blue-100 rounded skeleton" />
      </div>
    </div>
  );
}

export function ChartSkeleton() {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-lg animate-scaleIn">
      <div className="h-6 w-40 bg-gray-200 rounded mb-4 skeleton" />
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {[1, 2].map((i) => (
          <div key={i} className="aspect-video bg-gray-200 rounded-lg skeleton" />
        ))}
      </div>
    </div>
  );
}
