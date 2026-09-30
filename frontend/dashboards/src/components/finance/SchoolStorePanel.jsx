import { useEffect, useState } from "react";
import { apiJson } from "../../lib/api";

const base = "/api/v1/payments/store";
const money = (cents) => new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(cents / 100);

export default function SchoolStorePanel() {
  const [products, setProducts] = useState([]);
  const [page, setPage] = useState(1);
  const [count, setCount] = useState(0);
  const [cart, setCart] = useState({});
  const [quote, setQuote] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [version, setVersion] = useState(0);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    apiJson(`${base}/products/?page=${page}`).then((data) => {
      if (active) { setProducts(data.results); setCount(data.count); }
    }).catch((err) => { if (active) setError(err.message || "School store unavailable."); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [page, version]);

  async function submit(event, action) {
    event.preventDefault();
    setBusy(true); setError(""); setQuote(null);
    try { await action(new FormData(event.currentTarget)); }
    catch (err) { setError(err.message || "Operation failed."); }
    finally { setBusy(false); }
  }

  async function preview() {
    setBusy(true); setError(""); setQuote(null);
    try {
      const items = Object.entries(cart).map(([id, quantity]) => ({ product_id: Number(id), quantity }));
      setQuote(await apiJson(`${base}/quote/`, { method: "POST", body: JSON.stringify({ items }) }));
    } catch (err) { setError(err.message || "Unable to price cart."); }
    finally { setBusy(false); }
  }

  const field = "rounded border border-slate-300 px-3 py-2";
  return <section className="mt-6 rounded-lg border border-slate-200 bg-white p-5" aria-labelledby="school-store-title">
    <h2 id="school-store-title" className="text-xl font-semibold">School Store</h2>
    <p className="my-2 text-sm text-slate-600">Manage merchandise and prepare a cart. Payment collection is unavailable. Quotes do not reserve inventory.</p>
    {error && <p role="alert" className="text-red-700">{error}</p>}
    <button type="button" disabled={busy || loading} onClick={() => { setQuote(null); setVersion(version + 1); }}>Refresh catalog</button>
    {loading ? <p role="status">Loading catalog…</p> : <>
      <ul className="my-3 space-y-2">{products.map((product) => <li key={product.id} className="flex flex-wrap items-center justify-between gap-3 border-b py-2">
        <span>{product.name} ({product.sku}) — {money(product.price_cents)} · {product.stock} in stock{!product.active && " · Retired"}</span>
        <button type="button" disabled={busy || !product.active || product.stock <= (cart[product.id] || 0)} onClick={() => { setCart({ ...cart, [product.id]: (cart[product.id] || 0) + 1 }); setQuote(null); }}>Add to cart</button>
      </li>)}</ul>
      {!products.length && <p>No products on this page.</p>}
      <div className="flex gap-4"><button type="button" disabled={busy || page === 1} onClick={() => setPage(page - 1)}>Previous</button><span>Page {page}</span><button type="button" disabled={busy || page * 100 >= count} onClick={() => setPage(page + 1)}>Next</button></div>
    </>}
    <p className="mt-4">Cart: {Object.values(cart).reduce((sum, quantity) => sum + quantity, 0)} items</p>
    <div className="flex gap-4 my-2"><button type="button" disabled={busy || !Object.keys(cart).length} onClick={preview}>Calculate total</button><button type="button" disabled={busy} onClick={() => { setCart({}); setQuote(null); }}>Clear cart</button></div>
    {quote && <div role="status"><ul>{quote.items.map((item) => <li key={item.product_id}>{item.name} × {item.quantity}: {money(item.total_cents)}</li>)}</ul><p>Subtotal {money(quote.subtotal_cents)} · Tax {money(quote.tax_cents)} · Total {money(quote.total_cents)}</p></div>}
    <button type="button" disabled>Payment collection unavailable</button>
    <details className="mt-4"><summary>Catalog and inventory management</summary>
      <form className="my-3 flex flex-wrap gap-3" onSubmit={(event) => submit(event, async (data) => {
        await apiJson(`${base}/products/`, { method: "POST", body: JSON.stringify({ sku: data.get("sku"), name: data.get("name"), barcode: data.get("barcode"), price_cents: Number(data.get("price")), tax_rate_bp: Number(data.get("tax")) }) });
        setVersion(version + 1);
      })}>
        <label>SKU <input className={field} name="sku" required maxLength={64} /></label>
        <label>Name <input className={field} name="name" required maxLength={160} /></label>
        <label>Barcode <input className={field} name="barcode" maxLength={64} /></label>
        <label>Price in cents <input className={field} name="price" type="number" min="0" step="1" required /></label>
        <label>Tax in basis points (600 = 6%) <input className={field} name="tax" type="number" min="0" max="10000" step="1" defaultValue="0" required /></label>
        <button disabled={busy} type="submit">Create product</button>
      </form>
      <form className="my-3 flex flex-wrap gap-3" onSubmit={(event) => submit(event, async (data) => {
        await apiJson(`${base}/products/${data.get("product")}/stock/`, { method: "POST", body: JSON.stringify({ delta: Number(data.get("delta")), reason: data.get("reason"), idempotency_key: data.get("reference") }) });
        setVersion(version + 1);
      })}>
        <label>Product <select className={field} name="product" required><option value="">Select product</option>{products.map((product) => <option key={product.id} value={product.id}>{product.name}</option>)}</select></label>
        <label>Quantity change <input className={field} name="delta" type="number" step="1" min="-1000000" max="1000000" required /></label>
        <label>Reason <input className={field} name="reason" required maxLength={255} /></label>
        <label>Unique adjustment reference <input className={field} name="reference" required maxLength={128} /></label>
        <button disabled={busy} type="submit">Record inventory adjustment</button>
      </form>
    </details>
  </section>;
}
