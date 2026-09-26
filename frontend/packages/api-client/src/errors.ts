import { ApiError } from './http';

/**
 * DRF's validation-error shape, confirmed against the real API (not assumed):
 *   bad login      -> 400 {"non_field_errors": ["Unable to log in with provided credentials."]}
 *   taken username -> 400 {"username": ["A user with that username already exists."]}
 *   weak password  -> 400 {"password": ["This password is too short...", "This password is too common.", ...]}
 * Every field's value is an array of messages (a field can fail more than one
 * validator at once, as password does above) - never a bare string.
 */
export interface FormErrors {
  /** Keyed by field name exactly as the API names it (e.g. "username", "password"). */
  fields: Record<string, string>;
  /** non_field_errors, or a fallback for anything that isn't the shape above at all
   * (a network failure, a 500) - always show this if fields is empty. */
  general?: string;
}

export function parseFormErrors(error: unknown): FormErrors {
  if (!(error instanceof ApiError) || typeof error.body !== 'object' || error.body === null) {
    return { fields: {}, general: 'Something went wrong. Please try again.' };
  }
  const body = error.body as Record<string, unknown>;
  const fields: Record<string, string> = {};
  let general: string | undefined;

  for (const [key, value] of Object.entries(body)) {
    const messages = Array.isArray(value) ? value.filter((v): v is string => typeof v === 'string') : [];
    if (messages.length === 0) continue;
    if (key === 'non_field_errors' || key === 'detail') {
      general = messages.join(' ');
    } else {
      fields[key] = messages.join(' ');
    }
  }

  if (Object.keys(fields).length === 0 && !general) {
    general = 'Something went wrong. Please try again.';
  }
  return { fields, general };
}
