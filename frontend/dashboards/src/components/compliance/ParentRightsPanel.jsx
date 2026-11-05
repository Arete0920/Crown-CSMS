import { useRef, useState } from "react";
import { apiJson } from "../../lib/api";

export default function ParentRightsPanel() {
  const [status, setStatus] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const inFlight = useRef(false);

  const submitRequest = async (requestType) => {
    if (inFlight.current) return;
    inFlight.current = true;
    setSubmitting(true);
    setStatus("");
    try {
      const receipt = await apiJson("/api/compliance/parent-rights/", {
        method: "POST",
        body: JSON.stringify({ request_type: requestType }),
      });
      if (
        receipt?.status !== "received"
        || receipt?.request_type !== requestType
        || typeof receipt?.request_id !== "string"
        || !receipt.request_id.trim()
      ) {
        throw new Error("Missing request receipt");
      }
      setStatus(
        `Request received (reference ${receipt.request_id}). School review and identity verification are required before any data is provided, changed, or deleted.`,
      );
    } catch {
      setStatus(
        "Submission could not be confirmed. Contact your school before retrying to avoid duplicate requests.",
      );
    } finally {
      inFlight.current = false;
      setSubmitting(false);
    }
  };

  return (
    <div className="rounded-xl border bg-white p-6">
      <h2 className="text-xl font-semibold mb-4">Parent Data Rights</h2>
      <p className="mb-4 text-sm text-slate-700">
        Submit a request for your school to review. Submitting a request does not
        grant consent or immediately export, change, or delete student records.
      </p>

      <div className="grid gap-3" aria-busy={submitting}>
        <button
          disabled={submitting}
          className="rounded-lg border px-4 py-3 text-left disabled:opacity-50"
          onClick={() => submitRequest("export")}
        >
          Request Student Data Export
        </button>
        <button
          disabled={submitting}
          className="rounded-lg border px-4 py-3 text-left disabled:opacity-50"
          onClick={() => submitRequest("correction")}
        >
          Request Data Correction
        </button>
        <button
          disabled={submitting}
          className="rounded-lg border px-4 py-3 text-left disabled:opacity-50"
          onClick={() => submitRequest("deletion")}
        >
          Request Data Deletion
        </button>
      </div>

      <p role="status" className="mt-4 text-sm text-slate-700">{status}</p>
    </div>
  );
}
