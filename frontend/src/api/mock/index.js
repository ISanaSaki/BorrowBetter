/** Mock transport: adds a little latency and forwards to the route handlers. */

import { handleRoute } from './handlers.js';
import { resetDb } from './db.js';

function sleep(ms, signal) {
  return new Promise((resolve, reject) => {
    if (signal?.aborted) {
      reject(new DOMException('Aborted', 'AbortError'));
      return;
    }
    const timer = setTimeout(() => {
      signal?.removeEventListener('abort', onAbort);
      resolve();
    }, ms);
    function onAbort() {
      clearTimeout(timer);
      reject(new DOMException('Aborted', 'AbortError'));
    }
    signal?.addEventListener('abort', onAbort, { once: true });
  });
}

export async function mockRequest({ method, path, query, body, token, signal }) {
  // A small, human-like delay keeps loading states honest during the demo.
  await sleep(120 + Math.floor(Math.random() * 140), signal);
  return handleRoute({ method, path, query, body, token });
}

/** Exposed for the demo: `window.__bbResetMock()` restores the seed data. */
if (typeof window !== 'undefined') {
  window.__bbResetMock = () => {
    resetDb();
    window.location.reload();
  };
}
