import { apiGet, apiPatch, apiPost } from './request';

const INQUIRIES_PATH = '/api/v1/crm/inquiries/';

export function createInquiryRequestKey() {
  if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID();
  const bytes = new Uint8Array(16);
  globalThis.crypto.getRandomValues(bytes);
  bytes[6] = (bytes[6] & 0x0f) | 0x40;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;
  const hex = Array.from(bytes, (value) => value.toString(16).padStart(2, '0')).join('');
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}

export function submitAdmissionsInquiry(payload, idempotencyKey) {
  return apiPost(INQUIRIES_PATH, payload, {
    headers: {
      'Idempotency-Key': idempotencyKey,
      // A public campus request must not inherit a previously selected staff tenant.
      'X-School-Id': payload.school_id || '',
    },
  });
}

export function startInquiryApplication(receipt) {
  return apiPost(`${INQUIRIES_PATH}${encodeURIComponent(receipt.inquiry_id)}/start/`, {
    school_id: receipt.school_id,
    continuation_token: receipt.continuation_token,
  }, { headers: { 'X-School-Id': receipt.school_id } });
}

export function fetchAdmissionsInquiries(filters = {}) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== '' && value != null && value !== false) params.set(key, String(value));
  });
  return apiGet(`${INQUIRIES_PATH}${params.size ? `?${params}` : ''}`);
}

export function updateAdmissionsInquiry(inquiryId, changes) {
  return apiPatch(`${INQUIRIES_PATH}${encodeURIComponent(inquiryId)}/`, changes);
}
