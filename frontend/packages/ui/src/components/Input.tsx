import { forwardRef } from 'react';
import type { InputHTMLAttributes } from 'react';

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  invalid?: boolean;
}

/** forwardRef so React Hook Form's register() can attach directly to the underlying
 * <input> - this is the one thing a form-binding library needs from a UI primitive. */
export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { invalid = false, className = '', ...props },
  ref,
) {
  return (
    <input
      ref={ref}
      className={`h-11 px-3.5 rounded-sm border bg-white text-sm text-text w-full focus:outline focus:outline-2 focus:outline-accent focus:outline-offset-1 ${
        invalid ? 'border-danger' : 'border-border-strong'
      } ${className}`}
      {...props}
    />
  );
});
