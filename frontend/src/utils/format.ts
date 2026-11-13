/**
 * Format a number into Indian Rupee format with ₹ symbol and Indian grouping.
 * E.g., 418650 -> "₹ 4,18,650"
 */
export function formatINR(amount: number | null | undefined): string {
  if (amount === null || amount === undefined || isNaN(amount)) {
    return '₹ 0';
  }
  const formatted = Math.round(amount).toLocaleString('en-IN');
  return `₹ ${formatted}`;
}

/**
 * Format date string into human readable format, e.g. "12 Oct 2027".
 */
export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return '';
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    return d.toLocaleDateString('en-GB', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    });
  } catch {
    return dateStr;
  }
}

/**
 * Format date into weekday string, e.g. "Sunday, 12 Oct 2027".
 */
export function formatWeekdayDate(dateStr: string | null | undefined): string {
  if (!dateStr) return '';
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    return d.toLocaleDateString('en-GB', {
      weekday: 'long',
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    });
  } catch {
    return dateStr;
  }
}

/**
 * Calculate return date from start date and nights.
 */
export function calculateReturnDate(startDateStr: string, nights: number): string {
  if (!startDateStr) return '';
  try {
    const d = new Date(startDateStr);
    d.setDate(d.getDate() + nights);
    return d.toLocaleDateString('en-GB', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    });
  } catch {
    return '';
  }
}
