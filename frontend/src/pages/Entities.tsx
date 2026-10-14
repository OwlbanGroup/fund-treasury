import { useCallback, useEffect, useState, type FormEvent } from "react";
import {
  createEntity,
  deleteEntity,
  listEntities,
  shortDate,
  type Entity,
} from "../api";

export default function Entities() {
  const [entities, setEntities] = useState<Entity[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  // Create form state
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [currency, setCurrency] = useState("USD");
  const [creating, setCreating] = useState(false);

  const refresh = useCallback(() => {
    listEntities()
      .then((e) => {
        setEntities(e);
        setError(null);
      })
      .catch((err: Error) => setError(err.message));
  }, []);

  useEffect(refresh, [refresh]);

  const onCreate = async (ev: FormEvent) => {
    ev.preventDefault();
    setCreating(true);
    setError(null);
    setNotice(null);
    try {
      const created = await createEntity({
        name: name.trim(),
        code: code.trim().toUpperCase(),
        base_currency: currency.trim().toUpperCase(),
      });
      setNotice(`Entity ${created.code} created.`);
      setName("");
      setCode("");
      setCurrency("USD");
      refresh();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setCreating(false);
    }
  };

  const onDelete = async (e: Entity) => {
    if (!window.confirm(`Delete entity ${e.code} (${e.name})?`)) return;
    setError(null);
    setNotice(null);
    try {
      await deleteEntity(e.id);
      setNotice(`Entity ${e.code} deleted.`);
      refresh();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  return (
    <>
      <h1>Entities</h1>
      <p className="page-sub">Legal entities in the fund structure.</p>

      {error && <div className="error-box">{error}</div>}
      {notice && <div className="success-box">{notice}</div>}

      <div className="panel">
        <h2>New entity</h2>
        <form className="form-grid" onSubmit={onCreate}>
          <div>
            <label className="field" htmlFor="e-name">Name</label>
            <input
              id="e-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="RW Capital Partners"
              required
              maxLength={200}
            />
          </div>
          <div>
            <label className="field" htmlFor="e-code">Code</label>
            <input
              id="e-code"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="RW-CAP"
              required
              maxLength={50}
            />
          </div>
          <div>
            <label className="field" htmlFor="e-ccy">Base currency</label>
            <input
              id="e-ccy"
              value={currency}
              onChange={(e) => setCurrency(e.target.value)}
              placeholder="USD"
              required
              minLength={3}
              maxLength={3}
            />
          </div>
          <div>
            <button className="btn" type="submit" disabled={creating}>
              {creating ? "Creating…" : "Create entity"}
            </button>
          </div>
        </form>
      </div>

      <div className="panel">
        <h2>All entities</h2>
        {entities.length === 0 ? (
          <div className="empty">No entities yet.</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Code</th>
                <th>Name</th>
                <th>Currency</th>
                <th>Created</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {entities.map((e) => (
                <tr key={e.id}>
                  <td className="muted">{e.id}</td>
                  <td className="mono">{e.code}</td>
                  <td>{e.name}</td>
                  <td>{e.base_currency}</td>
                  <td className="muted">{shortDate(e.created_at)}</td>
                  <td className="num">
                    <button
                      className="btn btn-danger btn-sm"
                      onClick={() => onDelete(e)}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}
