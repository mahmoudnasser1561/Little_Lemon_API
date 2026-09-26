import type { ReactNode } from 'react';

export interface FormFieldProps {
  label: string;
  htmlFor: string;
  error?: string;
  hint?: string;
  children: ReactNode;
}

/** Purely presentational label/error/hint chrome - deliberately has no react-hook-form
 * dependency of its own. The bound <Input> (with its RHF register()) is passed in as
 * children, so this stays a plain design-system piece any form-binding approach can use. */
export function FormField({ label, htmlFor, error, hint, children }: FormFieldProps) {
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={htmlFor} className="text-sm font-semibold text-text">
        {label}
      </label>
      {children}
      {error && <span className="text-xs text-danger font-medium">{error}</span>}
      {!error && hint && <span className="text-xs text-text-tertiary">{hint}</span>}
    </div>
  );
}
