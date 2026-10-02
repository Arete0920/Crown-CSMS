import { useState } from "react";

export default function SchoolConsentStep({ onAccepted }) {
  const [checked, setChecked] = useState(false);

  return (
    <div className="rounded-xl border p-6 bg-white">
      <h2 className="text-2xl font-semibold mb-4">
        School Authorization & FERPA/COPPA Notice
      </h2>

      <div className="space-y-4 text-sm text-slate-700">
        <p>
          The school authorizes CROWN to process
          student information solely for legitimate
          educational purposes.
        </p>

        <p>
          CROWN acts as a school official under FERPA
          and processes child information under the
          school-consent educational exception of COPPA.
        </p>

        <p>
          CROWN does not use student data for
          advertising, profiling, or commercial resale.
        </p>
      </div>

      <label className="flex items-start gap-3 mt-6">
        <input
          type="checkbox"
          checked={checked}
          onChange={(e) => setChecked(e.target.checked)}
        />

        <span className="text-sm">
          I acknowledge and authorize educational data
          processing on behalf of the school.
        </span>
      </label>

      <button
        disabled={!checked}
        onClick={() => onAccepted?.()}
        className="mt-6 rounded-lg bg-amber-600 px-4 py-2 text-white disabled:opacity-50"
      >
        Continue
      </button>
    </div>
  );
}
