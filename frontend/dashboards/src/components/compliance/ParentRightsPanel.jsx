import { useState } from "react";
import { apiFetch } from "../../lib/api";

export default function ParentRightsPanel() {
  const [status, setStatus] = useState("");

  const submitRequest = async (requestType) => {
    try {
      await apiFetch("/api/compliance/parent-rights/", {
        method: "POST",
        body: {
          request_type: requestType,
        },
      });
      setStatus(`Request submitted: ${requestType}`);
    } catch {
      setStatus("Unable to submit request. Please retry.");
    }
  };

  return (
    <div className="rounded-xl border bg-white p-6">
      <h2 className="text-xl font-semibold mb-4">
        Parent Data Rights
      </h2>

      <div className="grid gap-3">
        <button
          className="rounded-lg border px-4 py-3 text-left"
          onClick={() => submitRequest("export")}
        >
          Download My Student Data
        </button>

        <button
          className="rounded-lg border px-4 py-3 text-left"
          onClick={() => submitRequest("correction")}
        >
          Request Data Correction
        </button>

        <button
          className="rounded-lg border px-4 py-3 text-left"
          onClick={() => submitRequest("deletion")}
        >
          Request Data Deletion
        </button>
      </div>

      {status ? (
        <p className="mt-4 text-sm text-slate-700">
          {status}
        </p>
      ) : null}
    </div>
  );
}
