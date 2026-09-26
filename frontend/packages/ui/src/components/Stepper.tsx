export interface StepperProps {
  value: number;
  onChange: (next: number) => void;
  min?: number;
  max?: number;
}

/** max defaults to 99 to match the cart's own per-line cap (MAX_QUANTITY_PER_LINE in
 * cart/models.py) - the client should never let a user compose a request the API is
 * guaranteed to reject. */
export function Stepper({ value, onChange, min = 1, max = 99 }: StepperProps) {
  return (
    <div className="inline-flex items-center border border-border-strong rounded-sm overflow-hidden">
      <button
        type="button"
        aria-label="Decrease quantity"
        className="w-8 h-8 flex items-center justify-center hover:bg-surface-alt disabled:opacity-40 disabled:cursor-not-allowed"
        onClick={() => onChange(Math.max(min, value - 1))}
        disabled={value <= min}
      >
        −
      </button>
      <span className="w-8 text-center text-sm font-semibold">{value}</span>
      <button
        type="button"
        aria-label="Increase quantity"
        className="w-8 h-8 flex items-center justify-center hover:bg-surface-alt disabled:opacity-40 disabled:cursor-not-allowed"
        onClick={() => onChange(Math.min(max, value + 1))}
        disabled={value >= max}
      >
        +
      </button>
    </div>
  );
}
