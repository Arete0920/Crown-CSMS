import { apiFetch } from "../lib/api";

export function createCompuwerxPaymentIntent(payload) {
    return apiFetch("/api/v1/payments/intents/", {
        method: "POST",
        body: JSON.stringify({
            provider: "compuwerx",
            ...payload,
        }),
    });
}

export function fetchCompuwerxIntentStatus(intentId) {
    return apiFetch(`/api/v1/payments/intents/${intentId}/status/`);
}
