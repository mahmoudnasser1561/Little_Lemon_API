/** Small local icon set - plain stroke SVGs, not an icon font/library dependency. */

export function DishIcon({ size = 32 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M6 2v20" />
      <path d="M6 2c-1.5 0-2 3-2 5s.5 4 2 4" />
      <path d="M18 2c-2.5 0-4 3-4 6s1 4 2 4" />
      <path d="M18 12v10" />
    </svg>
  );
}

export function BackIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="19" y1="12" x2="5" y2="12" />
      <polyline points="12 19 5 12 12 5" />
    </svg>
  );
}
