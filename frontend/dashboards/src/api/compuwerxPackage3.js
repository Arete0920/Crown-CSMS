import { apiFetch } from "../lib/api";

export function fetchSavedPaymentMethods(householdId) {
    return apiFetch(`/api/v1/payments/accounts/${householdId}/methods/`);
}

export function createSavedPaymentMethodSetup(householdId, payload) {
    return apiFetch(`/api/v1/payments/accounts/${householdId}/methods/setup/`, {
        method: "POST",
        body: JSON.stringify(payload),
    });
}

export function setDefaultPaymentMethod(householdId, methodId) {
    return apiFetch(`/api/v1/payments/accounts/${householdId}/methods/${methodId}/default/`, {
        method: "POST",
        body: JSON.stringify({}),
    });
}

export function detachSavedPaymentMethod(householdId, methodId) {
    return apiFetch(`/api/v1/payments/accounts/${householdId}/methods/${methodId}/`, {
        method: "DELETE",
    });
}

export function fetchHouseholdStatementCsvUrl(householdId) {
    return `/api/v1/payments/accounts/${householdId}/statement.csv`;
}

export function fetchPaymentReceiptUrl(paymentId) {
    return `/api/v1/payments/receipts/${paymentId}/`;
}

export function fetchDisputeDetail(disputeId) {
    return apiFetch(`/api/v1/payments/disputes/${disputeId}/`);
}

export function createDisputeAction(disputeId, payload) {
    return apiFetch(`/api/v1/payments/disputes/${disputeId}/actions/`, {
        method: "POST",
        body: JSON.stringify(payload),
    });
}

export function fetchPaymentExceptions() {
    return apiFetch("/api/v1/payments/exceptions/");
}

export function retryPaymentException(exceptionId) {
    return apiFetch(`/api/v1/payments/exceptions/${exceptionId}/retry/`, {
        method: "POST",
        body: JSON.stringify({}),
    });
}

export function ignorePaymentException(exceptionId) {
    return apiFetch(`/api/v1/payments/exceptions/${exceptionId}/ignore/`, {
        method: "POST",
        body: JSON.stringify({}),
    });
}
