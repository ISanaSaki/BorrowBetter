/** Accessible modal dialogs: confirm and prompt (used for reservation transitions). */

import { html, htmlToElement } from '../lib/html.js';
import { icon } from '../lib/icons.js';

let activeDialog = null;

function closeActive(result) {
  if (!activeDialog) return;
  const { overlay, resolve, previousFocus, onKeydown } = activeDialog;
  document.removeEventListener('keydown', onKeydown);
  overlay.classList.remove('is-on');
  activeDialog = null;
  setTimeout(() => overlay.remove(), 180);
  previousFocus?.focus?.({ preventScroll: true });
  resolve(result);
}

function trapFocus(overlay, event) {
  const focusable = overlay.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
  );
  if (!focusable.length) return;
  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault();
    first.focus();
  }
}

/**
 * @returns {Promise<boolean>} true when confirmed
 */
export function confirmDialog({
  title,
  message = '',
  confirmText = 'تأیید',
  cancelText = 'انصراف',
  danger = false,
  iconName = danger ? 'warning' : 'info',
}) {
  return openDialog({
    title,
    message,
    confirmText,
    cancelText,
    danger,
    iconName,
    withInput: false,
  }).then((value) => Boolean(value));
}

/**
 * @returns {Promise<string|null>} the entered text, or null when cancelled
 */
export function promptDialog({
  title,
  message = '',
  label = '',
  placeholder = '',
  confirmText = 'ثبت',
  cancelText = 'انصراف',
  required = false,
  maxLength = 500,
  initialValue = '',
}) {
  return openDialog({
    title,
    message,
    label,
    placeholder,
    confirmText,
    cancelText,
    required,
    maxLength,
    initialValue,
    withInput: true,
    iconName: 'edit',
  });
}

function openDialog(config) {
  if (activeDialog) closeActive(null);

  const previousFocus = document.activeElement;
  const overlay = htmlToElement(html`
    <div class="modal-overlay" role="presentation">
      <div class="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title">
        <div class="modal-head">
          <span class="modal-icon ${config.danger ? 'is-danger' : ''}">${icon(config.iconName)}</span>
          <div>
            <h2 id="modal-title">${config.title}</h2>
            ${config.message ? html`<p>${config.message}</p>` : ''}
          </div>
          <button type="button" class="icon-btn modal-close" data-modal="cancel" aria-label="بستن">
            ${icon('close')}
          </button>
        </div>

        ${config.withInput
          ? html`
              <label class="field modal-field">
                <span>${config.label || 'یادداشت'}</span>
                <textarea rows="3" maxlength="${config.maxLength}" placeholder="${config.placeholder}" data-modal-input>${config.initialValue || ''}</textarea>
                <small class="field-hint">${config.required ? 'این فیلد الزامی است.' : 'اختیاری — برای طرف دیگر نمایش داده می‌شود.'}</small>
              </label>`
          : ''}

        <div class="modal-actions">
          <button type="button" class="btn ${config.danger ? 'btn-danger' : 'btn-primary'}" data-modal="confirm">
            ${config.confirmText}
          </button>
          <button type="button" class="btn btn-ghost" data-modal="cancel">${config.cancelText}</button>
        </div>
      </div>
    </div>
  `);

  const promise = new Promise((resolve) => {
    const confirmButton = overlay.querySelector('[data-modal="confirm"]');
    const input = overlay.querySelector('[data-modal-input]');
    const errorHint = overlay.querySelector('.field-hint');

    const onKeydown = (event) => {
      if (event.key === 'Escape') {
        event.preventDefault();
        closeActive(null);
      } else if (event.key === 'Tab') {
        trapFocus(overlay, event);
      } else if (event.key === 'Enter' && config.withInput && (event.metaKey || event.ctrlKey)) {
        event.preventDefault();
        confirmButton.click();
      }
    };

    activeDialog = { overlay, resolve, previousFocus, onKeydown };
    document.addEventListener('keydown', onKeydown);

    overlay.addEventListener('click', (event) => {
      if (event.target === overlay || event.target.closest('[data-modal="cancel"]')) {
        closeActive(null);
        return;
      }
      if (event.target.closest('[data-modal="confirm"]')) {
        if (!config.withInput) {
          closeActive(true);
          return;
        }
        const value = input.value.trim();
        if (config.required && !value) {
          errorHint.textContent = 'برای ادامه، یادداشت را بنویس.';
          errorHint.classList.add('is-error');
          input.focus();
          return;
        }
        closeActive(value);
      }
    });

    document.body.append(overlay);
    requestAnimationFrame(() => overlay.classList.add('is-on'));
    setTimeout(() => {
      if (config.withInput) input?.focus();
      else confirmButton?.focus();
    }, 40);
  });

  return promise;
}
