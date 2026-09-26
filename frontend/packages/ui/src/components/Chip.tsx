import type { ButtonHTMLAttributes } from 'react';

export interface ChipProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  active?: boolean;
}

export function Chip({ active = false, className = '', ...props }: ChipProps) {
  return (
    <button
      type="button"
      className={`h-9 px-4 rounded-full border text-[13px] font-semibold transition-colors ${
        active
          ? 'bg-text border-text text-white'
          : 'bg-white border-border-strong text-text-secondary hover:border-accent'
      } ${className}`}
      {...props}
    />
  );
}
