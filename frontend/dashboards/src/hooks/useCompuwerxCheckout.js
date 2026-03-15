import { useCallback, useState } from "react";
import {
    createCompuwerxPaymentIntent,
    fetchCompuwerxIntentStatus,
} from "../api/compuwerxPayments";

export default function useCompuwerxCheckout() {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [intent, setIntent] = useState(null);

    const beginCheckout = useCallback(async (payload) => {
        setLoading(true);
        setError("");

        try {
            const res = await createCompuwerxPaymentIntent(payload);
            setIntent(res);

            if (res?.checkout_url) {
                window.location.assign(res.checkout_url);
            }

            return res;
        } catch (err) {
            setError(err?.message || "Unable to start Compuwerx checkout.");
            throw err;
        } finally {
            setLoading(false);
        }
    }, []);

    const refreshStatus = useCallback(async () => {
        if (!intent?.intent_id) return null;
        return fetchCompuwerxIntentStatus(intent.intent_id);
    }, [intent]);

    return {
        loading,
        error,
        intent,
        beginCheckout,
        refreshStatus,
    };
}
