'use client';

interface EmptyStateProps {
  title?: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export function EmptyState({
  title = 'No results yet',
  description = 'Enter a wine name and click analyze to see results.',
  action,
}: EmptyStateProps) {
  return (
    <div className="bg-gray-50 border-2 border-dashed border-gray-200 rounded-lg p-12 text-center">
      <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gray-100 mb-4">
        <svg
          className="w-8 h-8 text-gray-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
      </div>

      <h3 className="text-lg font-medium text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-500 max-w-sm mx-auto mb-4">{description}</p>

      {action && (
        <button
          onClick={action.onClick}
          className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          {action.label}
        </button>
      )}
    </div>
  );
}
