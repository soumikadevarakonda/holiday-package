import React, { useState } from 'react';
import { parseQuickRequest } from '../../api/parse';
import { Icon } from '../common/Icon';
import type { TripRequest } from '../../api/types';

interface QuickRequestBoxProps {
  onParsed: (parsed: Partial<TripRequest>) => void;
}

const EXAMPLE = '2 adults 1 kid age 6 Bengaluru to Japan 10 Apr 6 nights 3.5 lakh';

/** "Describe your trip in one line" — the backend parses it and the search bar is filled in. */
export const QuickRequestBox: React.FC<QuickRequestBoxProps> = ({ onParsed }) => {
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
      if (Object.keys(res.parsed).length === 0) {
        setError(`Couldn't understand that. Try something like: "${EXAMPLE}"`);
        return;
      }
      onParsed(res.parsed);
      const notes = [
        res.missing_fields.length
          ? `Filled in what I found — please set: ${res.missing_fields.join(', ').replace(/_/g, ' ')}.`
          : 'Search filled in — check it and press Search.',
        res.unparsed.length ? `Ignored: “${res.unparsed.join(' ')}”.` : '',
        ...res.warnings,
      ].filter(Boolean);
      setNotice(notes.join(' '));
    } catch (err: any) {
      setError(err.message || 'Could not read that request');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleParse} className="mt-4">
      <label htmlFor="quick-text" className="text-sm font-semibold text-white flex items-center gap-1.5 mb-1.5">
        <Icon name="auto_awesome" className="!text-base" />
        Or describe your trip in one line
      </label>
      <div className="flex gap-2">
        <input
          id="quick-text"
          type="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder={`e.g. ${EXAMPLE}`}
          className="flex-1 min-w-0 h-11 px-3 rounded-md bg-white/95 text-ink placeholder:text-ink-mute focus:outline-none focus:ring-2 focus:ring-sun"
        />
        <button
          type="submit"
          disabled={loading || !text.trim()}
          className="h-11 px-4 rounded-md bg-white/15 hover:bg-white/25 text-white font-semibold ring-1 ring-white/60 disabled:opacity-50 whitespace-nowrap"
        >
          {loading ? 'Reading…' : 'Fill search'}
        </button>
      </div>
      {error && <p className="mt-2 text-sm text-sun font-medium">{error}</p>}
      {notice && !error && <p className="mt-2 text-sm text-white/90">{notice}</p>}
    </form>
  );
};
