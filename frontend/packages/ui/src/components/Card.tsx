import type { HTMLAttributes } from 'react';

export function Card({ className = '', ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={`bg-surface border border-border rounded shadow-[0_1px_2px_rgba(36,31,24,0.07)] ${className}`}
      {...props}
    />
  );
}
