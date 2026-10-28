/** Auth state: JWT + user kept in sessionStorage (one session per tab, decision D3). */

import { TOKEN_KEY, USER_KEY } from '../constants.js';
import { authApi } from '../api/endpoints.js';

const listeners = new Set();
let currentUser = readStoredUser();

function readStoredUser() {
  try {
    const raw = sessionStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function getToken() {
  try {
    return sessionStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function getUser() {
  return currentUser;
}

export function isLoggedIn() {
  return Boolean(getToken());
}

export function subscribe(listener) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function emit() {
  listeners.forEach((listener) => listener(currentUser));
}

function persist(token, user) {
  try {
    sessionStorage.setItem(TOKEN_KEY, token);
    sessionStorage.setItem(USER_KEY, JSON.stringify(user));
  } catch {
    /* storage can be disabled in private mode; the in-memory state still works */
  }
  currentUser = user;
  emit();
}

export async function login(email, password) {
  const { data } = await authApi.login({ email, password });
  persist(data.access_token, data.user);
  return data.user;
}

export async function register(payload) {
  const { data } = await authApi.register(payload);
  persist(data.access_token, data.user);
  return data.user;
}

export function logout() {
  try {
    sessionStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(USER_KEY);
  } catch {
    /* ignore */
  }
  currentUser = null;
  emit();
}

/** Loads `/me` once when only the token survived a reload. */
export async function ensureUser() {
  if (!getToken()) return null;
  if (currentUser) return currentUser;
  try {
    const { data } = await authApi.me();
    currentUser = data;
    try {
      sessionStorage.setItem(USER_KEY, JSON.stringify(data));
    } catch {
      /* ignore */
    }
    emit();
    return data;
  } catch (error) {
    if (error?.status === 401) logout();
    return null;
  }
}
