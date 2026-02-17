import { useEffect, useState } from "react";

async function api(path, opts = {}) {
  const base = import.meta.env.VITE_API_BASE_URL || "";
  const res = await fetch(`${base}${path}`, {
    ...opts,
    headers: {
      "Content-Type": "application/json",
      ...(opts.headers || {}),
    },
  });
  const text = await res.text();
  let data = null;
  try { data = JSON.parse(text); } catch { data = text; }
  if (!res.ok) throw new Error(typeof data === "string" ? data : (data.detail || "Request failed"));
  return data;
}

export default function ServiceHoursPage() {
  const [pending, setPending] = useState([]);
  const [err, setErr] = useState("");

  const load = async () => {
    setErr("");
    try {
      const data = await api("/api/service/approvals/");
      setPending(Array.isArray(data) ? data : []);
    } catch (e) {
      setErr(String(e.message || e));
    }
  };

  useEffect(() => { load(); }, []);

  return (
    <div className="p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Service Hours</h1>
        <Button onClick={load}>Refresh</Button>
      </div>

      {err ? <div className="text-sm text-red-600">{err}</div> : null}

      <Card className="rounded-2xl">
        <CardContent className="p-4">
          <div className="text-sm text-muted-foreground mb-2">Pending approvals</div>
          <div className="space-y-2">
            {pending.slice(0, 30).map((x) => (
              <div key={x.id} className="border rounded-xl p-3">
                <div className="flex items-center justify-between">
                  <div className="font-medium">{x.student_name} • {x.hours}h</div>
                  <div className="text-xs opacity-70">{x.status}</div>
                </div>
                <div className="text-sm opacity-80">{x.category} • {x.organization}</div>
                <div className="text-xs opacity-60">{x.date}</div>
              </div>
            ))}
            {pending.length === 0 ? <div className="text-sm opacity-70">No pending items.</div> : null}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
