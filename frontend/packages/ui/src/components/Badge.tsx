import type { HTMLAttributes } from 'react';

type Tone = 'neutral' | 'olive' | 'amber' | 'danger' | 'accent';

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: Tone;
}

const toneClasses: Record<Tone, string> = {
  neutral: 'bg-surface-alt text-text-secondary',
  olive: 'bg-olive-soft text-olive',
  amber: 'bg-amber-soft text-amber',
  danger: 'bg-danger-soft text-danger',
  accent: 'bg-accent-soft text-accent',
};

export function Badge({ tone = 'neutral', className = '', ...props }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 h-[26px] px-2.5 rounded-full text-xs font-semibold whitespace-nowrap ${toneClasses[tone]} ${className}`}
      {...props}
    />
  );
}
