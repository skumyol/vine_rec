'use client';

interface LoadingStateProps {
  stage?: string;
  progress?: number;
}

export function LoadingState({ stage = 'Analyzing', progress }: LoadingStateProps) {
  const stages = [
    { name: 'Parsing wine identity', duration: 500 },
    { name: 'Searching for images', duration: 2000 },
    { name: 'Downloading candidates', duration: 3000 },
    { name: 'Analyzing images', duration: 4000 },
    { name: 'Verifying matches', duration: 2000 },
    { name: 'Selecting best image', duration: 500 },
  ];

  return (
    <div className="bg-white border rounded-lg p-8 text-center">
      <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-blue-100 mb-4">
        <svg
          className="animate-spin h-6 w-6 text-blue-600"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
          />
        </svg>
      </div>

      <h3 className="text-lg font-medium text-gray-900 mb-2">{stage}</h3>

      {progress !== undefined && (
        <div className="w-full max-w-xs mx-auto bg-gray-200 rounded-full h-2 mb-4">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}

      <div className="space-y-2 text-sm text-gray-500">
        {stages.map((s, i) => (
          <div key={s.name} className="flex items-center justify-center gap-2">
            <div
              className={`w-2 h-2 rounded-full ${
                progress && progress > (i / stages.length) * 100
                  ? 'bg-green-500'
                  : 'bg-gray-300'
              }`}
            />
            <span>{s.name}</span>
          </div>
        ))}
      </div>

      <p className="mt-4 text-xs text-gray-400">
        This may take 10-30 seconds depending on image count
      </p>
    </div>
  );
}
