'use client';

import { ParsedSKU } from '@/lib/types';

interface FieldMatchTableProps {
  parsedSku: ParsedSKU;
}

export function FieldMatchTable({ parsedSku }: FieldMatchTableProps) {
  const fields = [
    { label: 'Producer', value: parsedSku.producer, normalized: parsedSku.producer_normalized },
    { label: 'Appellation', value: parsedSku.appellation, normalized: parsedSku.appellation_normalized },
    { label: 'Vineyard', value: parsedSku.vineyard, normalized: parsedSku.vineyard_normalized },
    { label: 'Classification', value: parsedSku.classification, normalized: parsedSku.classification_normalized },
    { label: 'Vintage', value: parsedSku.vintage },
    { label: 'Region', value: parsedSku.region },
  ];

  return (
    <div className="bg-white border rounded-lg p-4">
      <h3 className="font-medium text-gray-900 mb-3">Parsed Wine Identity</h3>
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b">
            <th className="text-left py-2 font-medium text-gray-600">Field</th>
            <th className="text-left py-2 font-medium text-gray-600">Value</th>
            <th className="text-left py-2 font-medium text-gray-600">Normalized</th>
          </tr>
        </thead>
        <tbody>
          {fields.map((field) => (
            <tr key={field.label} className="border-b last:border-0">
              <td className="py-2 text-gray-500">{field.label}</td>
              <td className="py-2 font-medium">{field.value || '-'}</td>
              <td className="py-2 text-gray-400 text-xs">{field.normalized || '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {parsedSku.normalized_tokens.length > 0 && (
        <div className="mt-3 pt-3 border-t">
          <span className="text-xs text-gray-500">Normalized Tokens: </span>
          <span className="text-xs text-gray-600">
            {parsedSku.normalized_tokens.join(', ')}
          </span>
        </div>
      )}
    </div>
  );
}
