import { request } from './client.js';

export const authApi = {
  login: (body) => request('/auth/login', { method: 'POST', body, auth: false }),
  register: (body) => request('/auth/register', { method: 'POST', body, auth: false }),
  me: (signal) => request('/me', { signal }),
};

export const itemsApi = {
  list: (query, signal) => request('/items', { query, auth: false, signal }),
  get: (id, signal) => request(`/items/${id}`, { auth: false, signal }),
  create: (body) => request('/items', { method: 'POST', body }),
  update: (id, body) => request(`/items/${id}`, { method: 'PATCH', body }),
  remove: (id) => request(`/items/${id}`, { method: 'DELETE' }),
  myItems: (query, signal) => request('/me/items', { query, signal }),
  availability: (id, from, to, signal) =>
    request(`/items/${id}/availability`, { query: { from, to }, auth: false, signal }),
  categories: (signal) => request('/categories', { auth: false, signal }),
};

export const reservationsApi = {
  create: (body) => request('/reservations', { method: 'POST', body }),
  mine: (query, signal) => request('/me/reservations', { query, signal }),
  get: (id, signal) => request(`/reservations/${id}`, { signal }),
  approve: (id, body = {}) => request(`/reservations/${id}/approve`, { method: 'POST', body }),
  reject: (id, body = {}) => request(`/reservations/${id}/reject`, { method: 'POST', body }),
  cancel: (id, body = {}) => request(`/reservations/${id}/cancel`, { method: 'POST', body }),
  handover: (id, body = {}) => request(`/reservations/${id}/handover`, { method: 'POST', body }),
  returnItem: (id, body) => request(`/reservations/${id}/return`, { method: 'POST', body }),
};
