import { authenticatedFetch } from "../utils/authClient";
import { apiFetch } from "../lib/api";

export function fetchBankStatementImports() {
    return apiFetch("/api/v1/payments/bank/imports/");
}

export async function uploadBankStatementCsv(file) {
    const formData = new FormData();
    formData.append("file", file);

    const response = await authenticatedFetch("/api/v1/payments/bank/imports/upload/", {
        method: "POST",
        body: formData,
    });
    return response.json();
}

export function fetchUnmatchedBankEntries() {
    return apiFetch("/api/v1/payments/bank/unmatched-entries/");
}

export function fetchPayoutBankMatches() {
    return apiFetch("/api/v1/payments/bank/payout-matches/");
}

export function runAutoPayoutBankMatch() {
    return apiFetch("/api/v1/payments/bank/payout-matches/auto/", {
        method: "POST",
        body: JSON.stringify({}),
    });
}

export function createManualPayoutBankMatch(payload) {
    return apiFetch("/api/v1/payments/bank/payout-matches/manual/", {
        method: "POST",
        body: JSON.stringify(payload),
    });
}
