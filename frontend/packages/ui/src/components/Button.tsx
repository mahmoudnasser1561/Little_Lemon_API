import type { ButtonHTMLAttributes } from 'react';

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger';
type Size = 'md' | 'sm';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
}

const variantClasses: Record<Variant, string> = {
  primary: 'bg-accent text-white hover:bg-accent-hover border-transparent',
  secondary: 'bg-white text-text border-border-strong hover:border-accent',
  ghost: 'bg-transparent text-text-secondary hover:bg-surface-alt hover:text-text border-transparent',
  danger: 'bg-white text-danger border-danger-soft hover:bg-danger-soft',
};

const sizeClasses: Record<Size, string> = {
  md: 'h-11 px-5 text-sm',
  sm: 'h-9 px-3.5 text-[13px]',
};

export function Button({ variant = 'primary', size = 'md', className = '', ...props }: ButtonProps) {
  return (
    <button
      className={`inline-flex items-center justify-center gap-2 rounded-sm font-semibold border transition-colors disabled:opacity-45 disabled:cursor-not-allowed whitespace-nowrap ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
      {...props}
    />
  );
}
