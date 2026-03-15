import { apiFetch } from "../lib/api";

export function fetchHouseholdFinanceSummary(householdId) {
    return apiFetch(`/api/v1/payments/accounts/${householdId}/summary/`);
}

export function fetchHouseholdPaymentHistory(householdId) {
    return apiFetch(`/api/v1/payments/accounts/${householdId}/history/`);
}

export function fetchCompuwerxDisputes() {
    return apiFetch("/api/v1/payments/disputes/");
}

export function fetchCompuwerxPayoutBatches() {
    return apiFetch("/api/v1/payments/payout-batches/");
}

export function fetchCompuwerxPayoutBatchDetail(batchId) {
    return apiFetch(`/api/v1/payments/payout-batches/${batchId}/`);
}
