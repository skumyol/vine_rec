'use client';

interface NoImageStateProps {
  wineName: string;
  reason?: string;
}

export function NoImageState({ wineName, reason }: NoImageStateProps) {
  return (
    <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
      <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gray-200 mb-4">
        <svg
          className="w-8 h-8 text-gray-500"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
          />
        </svg>
      </div>

      <h3 className="text-lg font-medium text-gray-900 mb-2">No Image Found</h3>

      <p className="text-gray-600 mb-2">
        Could not find a verified photo for:
      </p>

      <p className="font-medium text-gray-900 mb-4">{wineName}</p>

      {reason && (
        <div className="bg-white border rounded-md p-3 max-w-md mx-auto mb-4">
          <p className="text-sm text-gray-600">{reason}</p>
        </div>
      )}

      <div className="text-sm text-gray-500 space-y-1">
        <p>This could mean:</p>
        <ul className="list-disc list-inside text-left max-w-xs mx-auto">
          <li>The wine is rare or newly released</li>
          <li>Available images did not meet quality standards</li>
          <li>Label verification failed for all candidates</li>
        </ul>
      </div>

      <div className="mt-4 pt-4 border-t">
        <p className="text-xs text-gray-400">
          Try adjusting the wine name or checking for typos.
        </p>
      </div>
    </div>
  );
}
