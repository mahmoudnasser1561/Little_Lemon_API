import { clearToken, request, setToken } from './http';
import type { CurrentUser } from './types';

export interface SignupPayload {
  username: string;
  password: string;
  email?: string;
}

export interface ProfileUpdate {
  email?: string;
}

export interface SetPasswordPayload {
  current_password: string;
  new_password: string;
}

interface TokenResponse {
  token: string;
}

export const auth = {
  /** POST /api/api-token-auth/ - DRF's built-in obtain_auth_token. Stores the token on
   * success; throws ApiError (parse with parseFormErrors) on bad credentials. */
  async login(username: string, password: string): Promise<void> {
    clearToken();
    const { token } = await request<TokenResponse>('/api/api-token-auth/', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
    setToken(token);
  },

  /** POST /api/users/ - Djoser's default create-only signup. Does NOT log the new user
   * in (no token comes back) - callers that want that call login() right after. */
  signup(payload: SignupPayload): Promise<CurrentUser> {
    clearToken();
    return request('/api/users/', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  /** POST /token/logout/ */
  async logout(): Promise<void> {
    try {
      await request('/token/logout/', { method: 'POST' });
    } catch {
      // ignore - still clear locally below
    } finally {
      clearToken();
    }
  },

  /** GET /api/users/me/ - the only endpoint that reports `role`. */
  me(): Promise<CurrentUser> {
    return request('/api/users/me/');
  },

  /** PATCH /api/users/me/ - username is read-only server-side, only email is writable. */
  updateProfile(data: ProfileUpdate): Promise<CurrentUser> {
    return request('/api/users/me/', {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },

  /** POST /api/users/set_password/ */
  setPassword(payload: SetPasswordPayload): Promise<void> {
    return request('/api/users/set_password/', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
};
