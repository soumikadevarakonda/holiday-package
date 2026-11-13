import React, { useState } from 'react';
import { parseQuickRequest } from '../../api/parse';
import type { TripRequest } from '../../api/types';

interface QuickRequestBoxProps {
  onParsed: (parsed: Partial<TripRequest>) => void;
  onApplyPreset: (preset: 'golden' | 'hokkaido' | 'kansai') => void;
}

export const QuickRequestBox: React.FC<QuickRequestBoxProps> = ({
  onParsed,
  onApplyPreset,
}) => {
  const [open, setOpen] = useState(false);
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const handleParse = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim()) return;
    try {
      setLoading(true);
      setError(null);
      setNotice(null);
      const res = await parseQuickRequest(text);
      const found = Object.keys(res.parsed).length;
      if (found === 0) {
        setError('Could not understand that. Try: "2 adults 1 kid age 6 Bengaluru to Japan 10 Apr 6 nights 3.5 lakh".');
        return;
      }
      onParsed(res.parsed);
      const notes = [
        res.missing_fields.length
          ? `Filled what I could — please check: ${res.missing_fields.join(', ').replace(/_/g, ' ')}.`
          : 'Form filled — check it and press build.',
        res.unparsed.length ? `Ignored: ${res.unparsed.join(', ')}.` : '',
        ...res.warnings,
      ].filter(Boolean);
      setNotice(notes.join(' '));
    } catch (err: any) {
      setError(err.message || 'Failed to parse natural language request');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-space-sm">
      <div className="flex items-center gap-space-xs flex-wrap self-start md:self-end">
        <span className="font-label-sm text-label-sm text-on-surface-variant uppercase mr-1">
          Presets:
        </span>
        <button
          type="button"
          onClick={() => onApplyPreset('golden')}
          className="px-space-sm py-1 rounded bg-surface-container-low hover:bg-surface-container text-on-surface font-label-md text-label-md transition-colors shadow-sm"
        >
          Mumbai → Japan (8N)
        </button>
        <button
          type="button"
          onClick={() => onApplyPreset('hokkaido')}
          className="px-space-sm py-1 rounded bg-surface-container-low hover:bg-surface-container text-on-surface font-label-md text-label-md transition-colors shadow-sm"
        >
          Delhi → Japan (7N)
        </button>
        <button
          type="button"
          onClick={() => onApplyPreset('kansai')}
          className="px-space-sm py-1 rounded bg-surface-container-low hover:bg-surface-container text-on-surface font-label-md text-label-md transition-colors shadow-sm"
        >
          Bengaluru → Japan (6N)
        </button>
        <button
          type="button"
          onClick={() => setOpen(!open)}
          className="px-space-sm py-1 rounded bg-primary-fixed text-on-primary-fixed hover:bg-secondary-fixed font-label-md text-label-md transition-colors shadow-sm flex items-center gap-1"
        >
          <span className="material-symbols-outlined text-[14px]">edit_note</span>
          <span>Quick Text</span>
        </button>
      </div>

      {open && (
        <form
          onSubmit={handleParse}
          className="bg-surface-container-low p-space-sm rounded-lg flex flex-col sm:flex-row items-center gap-space-sm w-full transition-all"
        >
          <div className="relative flex-1 w-full">
            <span className="material-symbols-outlined absolute left-2.5 top-2.5 text-on-surface-variant text-[18px]">
              chat
            </span>
            <input
              type="text"
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="e.g. 2 adults 1 kid age 6 Bengaluru to Japan 10 Apr 6 nights 3.5 lakh"
              className="w-full h-10 pl-9 pr-3 bg-surface-container-lowest text-on-surface rounded font-body-sm text-body-sm focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>
          <button
            type="submit"
            disabled={loading || !text.trim()}
            className="h-10 px-space-md rounded bg-primary text-on-primary font-label-md text-label-md font-semibold hover:bg-primary-container transition-colors disabled:opacity-50 whitespace-nowrap"
          >
            {loading ? 'Parsing...' : 'Fill Form'}
          </button>
          {error && <span className="text-error font-body-sm text-body-sm">{error}</span>}
          {notice && !error && <span className="text-on-surface-variant font-body-sm text-body-sm">{notice}</span>}
        </form>
      )}
    </div>
  );
};
