import { useCallback, useEffect, useState, type FormEvent } from "react";
import {
  createAccount,
  deleteAccount,
  listAccounts,
  listEntities,
  money,
  type Account,
  type Entity,
} from "../api";

const emptyForm = {
  entity_id: "",
  bank_name: "",
  account_number_masked: "",
  account_type: "Operating",
  currency: "USD",
  current_balance: "0.00",
  available_balance: "0.00",
};

export default function Accounts() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [entities, setEntities] = useState<Entity[]>([]);
  const [entityFilter, setEntityFilter] = useState<number | "">("");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [creating, setCreating] = useState(false);

  const refresh = useCallback(() => {
    Promise.all([
      listAccounts(entityFilter === "" ? undefined : entityFilter),
      listEntities(),
    ])
      .then(([a, e]) => {
        setAccounts(a);
        setEntities(e);
        setError(null);
      })
      .catch((err: Error) => setError(err.message));
  }, [entityFilter]);

  useEffect(refresh, [refresh]);

  const set = (key: keyof typeof form) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
      setForm((f) => ({ ...f, [key]: e.target.value }));

  const onCreate = async (ev: FormEvent) => {
    ev.preventDefault();
    setCreating(true);
    setError(null);
    setNotice(null);
    try {
      const created = await createAccount({
        entity_id: Number(form.entity_id),
        bank_name: form.bank_name.trim(),
        account_number_masked: form.account_number_masked.trim(),
        account_type: form.account_type.trim() || "Operating",
        currency: form.currency.trim().toUpperCase(),
        current_balance: form.current_balance || "0",
        available_balance: form.available_balance || "0",
      });
      setNotice(`Account ${created.account_number_masked} at ${created.bank_name} created.`);
      setForm({ ...emptyForm, entity_id: form.entity_id });
      refresh();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setCreating(false);
    }
  };

  const onDelete = async (a: Account) => {
    if (!window.confirm(`Delete account ${a.bank_name} ${a.account_number_masked}?`)) return;
    setError(null);
    setNotice(null);
    try {
      await deleteAccount(a.id);
      setNotice("Account deleted.");
      refresh();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const entityCode = (id: number) =>
    entities.find((e) => e.id === id)?.code ?? `#${id}`;

  return (
    <>
      <h1>Bank accounts</h1>
      <p className="page-sub">Accounts held across all entities.</p>

      {error && <div className="error-box">{error}</div>}
      {notice && <div className="success-box">{notice}</div>}

      <div className="panel">
        <h2>New account</h2>
        <form className="form-grid" onSubmit={onCreate}>
          <div>
            <label className="field" htmlFor="a-entity">Entity</label>
            <select
              id="a-entity"
              value={form.entity_id}
              onChange={set("entity_id")}
              required
            >
              <option value="" disabled>
                Select…
              </option>
              {entities.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.code} — {e.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="field" htmlFor="a-bank">Bank</label>
            <input
              id="a-bank"
              value={form.bank_name}
              onChange={set("bank_name")}
              placeholder="JPMorgan Chase"
              required
              maxLength={200}
            />
          </div>
          <div>
            <label className="field" htmlFor="a-mask">Account (masked)</label>
            <input
              id="a-mask"
              value={form.account_number_masked}
              onChange={set("account_number_masked")}
              placeholder="••••1234"
              required
              maxLength={20}
            />
          </div>
          <div>
            <label className="field" htmlFor="a-type">Type</label>
            <input
              id="a-type"
              value={form.account_type}
              onChange={set("account_type")}
              maxLength={40}
            />
          </div>
          <div>
            <label className="field" htmlFor="a-ccy">Currency</label>
            <input
              id="a-ccy"
              value={form.currency}
              onChange={set("currency")}
              required
              minLength={3}
              maxLength={3}
            />
          </div>
          <div>
            <label className="field" htmlFor="a-cur">Current balance</label>
            <input
              id="a-cur"
              value={form.current_balance}
              onChange={set("current_balance")}
              inputMode="decimal"
              required
            />
          </div>
          <div>
            <label className="field" htmlFor="a-avail">Available balance</label>
            <input
              id="a-avail"
              value={form.available_balance}
              onChange={set("available_balance")}
              inputMode="decimal"
              required
            />
          </div>
          <div>
            <button className="btn" type="submit" disabled={creating || entities.length === 0}>
              {creating ? "Creating…" : "Create account"}
            </button>
          </div>
        </form>
        {entities.length === 0 && (
          <div className="empty">Create an entity first — accounts belong to an entity.</div>
        )}
      </div>

      <div className="panel">
        <div className="toolbar">
          <h2 style={{ margin: 0 }}>All accounts</h2>
          <span className="spacer" />
          <label className="field" htmlFor="a-filter" style={{ margin: 0 }}>
            Filter
          </label>
          <select
            id="a-filter"
            value={entityFilter}
            onChange={(e) =>
              setEntityFilter(e.target.value === "" ? "" : Number(e.target.value))
            }
            style={{ width: 220 }}
          >
            <option value="">All entities</option>
            {entities.map((e) => (
              <option key={e.id} value={e.id}>
                {e.code}
              </option>
            ))}
          </select>
        </div>
        {accounts.length === 0 ? (
          <div className="empty">No accounts match.</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Entity</th>
                <th>Bank</th>
                <th>Account</th>
                <th>Type</th>
                <th className="num">Current</th>
                <th className="num">Available</th>
                <th>Status</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {accounts.map((a) => (
                <tr key={a.id}>
                  <td className="mono">{entityCode(a.entity_id)}</td>
                  <td>{a.bank_name}</td>
                  <td className="mono">
                    {a.account_number_masked}{" "}
                    <span className="muted">({a.currency})</span>
                  </td>
                  <td>{a.account_type}</td>
                  <td className="num">{money(a.current_balance, a.currency)}</td>
                  <td className="num">{money(a.available_balance, a.currency)}</td>
                  <td>
                    <span
                      className={`badge ${a.status === "active" ? "badge-ok" : "badge-muted"}`}
                    >
                      {a.status}
                    </span>
                  </td>
                  <td className="num">
                    <button
                      className="btn btn-danger btn-sm"
                      onClick={() => onDelete(a)}
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
