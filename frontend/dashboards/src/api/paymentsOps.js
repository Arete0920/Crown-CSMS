import { apiFetch } from "../lib/api";

export function fetchHouseholdFinanceSummary(householdId) {
    return apiFetch(`/api/v1/payments/accounts/${householdId}/summary/`);
}

export function fetchHouseholdPaymentHistory(householdId) {
    return apiFetch(`/api/v1/payments/accounts/${householdId}/history/`);
}

export function fetchPaymentDisputes() {
    return apiFetch("/api/v1/payments/disputes/");
}

export function fetchPayoutBatches() {
    return apiFetch("/api/v1/payments/payout-batches/");
}

export function fetchPayoutBatchDetail(batchId) {
    return apiFetch(`/api/v1/payments/payout-batches/${batchId}/`);
}
