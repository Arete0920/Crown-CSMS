/**
 * StorePage - list items, purchase, manage inventory.
 * Calls GET  /api/v1/advancement/store/
 *       POST /api/v1/advancement/purchase/store/
 */
import { useEffect, useState } from "react";
import { authenticatedFetch } from "../../utils/authClient.js";

function apiBase() {
  const base = (import.meta?.env?.VITE_API_BASE_URL || "").trim();
  return base.endsWith("/") ? base.slice(0, -1) : base;
}

async function apiJson(path, opts = {}) {
  const response = await authenticatedFetch(`${apiBase()}${path}`, {
    ...opts,
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      ...(opts.headers || {}),
    },
  });
  return response.json();
}

export default function StorePage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [purchasing, setPurchasing] = useState(null);
  const [quantities, setQuantities] = useState({});

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const data = await apiJson("/api/v1/advancement/store/?active=true");
      setItems(data.results ?? data);
    } catch (e) {
      setError(String(e.message || e));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let cancelled = false;

    async function initialize() {
      try {
        const data = await apiJson("/api/v1/advancement/store/?active=true");
        if (!cancelled) {
          setItems(data.results ?? data);
          setError(null);
          setLoading(false);
        }
      } catch (e) {
        if (!cancelled) {
          setError(String(e.message || e));
          setLoading(false);
        }
      }
    }

    void initialize();
    return () => {
      cancelled = true;
    };
  }, []);

  function handlePurchase(item) {
    const qty = parseInt(quantities[item.id] || 1, 10);
    if (Number.isNaN(qty) || qty < 1) return alert("Quantity must be at least 1.");
    setPurchasing(item.id);
    apiJson("/api/v1/advancement/purchase/store/", {
      method: "POST",
      body: JSON.stringify({ item_id: item.id, quantity: qty }),
    })
      .then(() => {
        alert(`Purchased ${qty}x ${item.name}`);
        void load();
      })
      .catch((e) => alert(`Purchase failed: ${e.message || e}`))
      .finally(() => setPurchasing(null));
  }

  if (loading) return <p aria-busy="true">Loading store...</p>;
  if (error) return <p role="alert" style={{ color: "var(--crown-danger)" }}>Error: {error}</p>;

  return (
    <div aria-label="Spirit Store">
      <h2>Spirit Store</h2>
      {items.length === 0 ? (
        <p style={{ color: "var(--crown-compat-color-b5e2bc59ff)", textAlign: "center", padding: 32 }}>No items in store.</p>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))", gap: 16 }}>
          {items.map((item) => (
            <article
              key={item.id}
              aria-label={item.name}
              style={{ border: "1px solid var(--crown-compat-color-3b313dfb66)", borderRadius: 8, padding: 16, background: "var(--crown-compat-color-e08de71387)" }}
            >
              <h3 style={{ margin: "0 0 4px", fontSize: 16 }}>{item.name}</h3>
              <p style={{ margin: "0 0 8px", fontSize: 13, color: "var(--crown-compat-color-6b3d6d843d)" }}>{item.description}</p>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                <span style={{ fontWeight: 700, fontSize: 18 }}>${Number(item.price).toFixed(2)}</span>
                <span style={{
                  fontSize: 12, fontWeight: 600,
                  color: item.inventory < 5 ? "var(--crown-compat-color-3871da3420)" : "var(--crown-compat-color-3c5c1ab6c5)",
                }}>
                  {item.inventory} in stock
                </span>
              </div>
              {item.inventory > 0 ? (
                <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                  <input
                    type="number"
                    min={1}
                    max={item.inventory}
                    value={quantities[item.id] || 1}
                    onChange={(e) => setQuantities({ ...quantities, [item.id]: e.target.value })}
                    aria-label={`Quantity for ${item.name}`}
                    style={{ width: 60, padding: "6px 8px", border: "1px solid var(--crown-compat-color-e2442d83b3)", borderRadius: 6 }}
                  />
                  <button
                    onClick={() => handlePurchase(item)}
                    disabled={purchasing === item.id}
                    style={{ flex: 1, padding: "7px 0" }}
                  >
                    {purchasing === item.id ? "..." : "Purchase"}
                  </button>
                </div>
              ) : (
                <p style={{ color: "var(--crown-compat-color-3871da3420)", fontSize: 13, fontWeight: 600, margin: 0 }}>Out of Stock</p>
              )}
            </article>
          ))}
        </div>
      )}
    </div>
  );
}