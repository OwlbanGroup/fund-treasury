import { useCallback, useEffect, useState, type FormEvent } from "react";
import {
  createPayment,
  dateTime,
  listAccounts,
  listPayments,
  money,
  sendPayment,
  type Account,
  type Payment,
} from "../api";

const METHODS = ["ACH", "WIRE", "SWIFT", "FEDWIRE", "RTGS"];

const emptyForm = {
  account_id: "",
  amount: "",
  counterparty: "",
  reference: "",
  payment_method: "ACH",
  note: "",
};

export default function Payments() {
  const [payments, setPayments] = useState<Payment[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [creating, setCreating] = useState(false);
  const [sendingId, setSendingId] = useState<number | null>(null);

  const refresh = useCallback(() => {
    Promise.all([listPayments(), listAccounts()])
      .then(([p, a]) => {
        setPayments(p);
        setAccounts(a);
        setError(null);
      })
      .catch((err: Error) => setError(err.message));
  }, []);

  useEffect(refresh, [refresh]);

  const set = (key: keyof typeof form) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
      setForm((f) => ({ ...f, [key]: e.target.value }));

  const accountLabel = (id: number) => {
    const a = accounts.find((x) => x.id === id);
    return a ? `${a.bank_name} ${a.account_number_masked}` : `#${id}`;
  };

  const onCreate = async (ev: FormEvent) => {
    ev.preventDefault();
    setCreating(true);
    setError(null);
    setNotice(null);
    try {
      const created = await createPayment({
        account_id: Number(form.account_id),
        amount: form.amount,
        counterparty: form.counterparty.trim(),
        reference: form.reference.trim(),
        payment_method: form.payment_method,
        note: form.note.trim() || undefined,
      });
      setNotice(
        `Payment ${created.reference} created with status '${created.status}'. Send it to dispatch.`,
      );
      setForm({ ...emptyForm, account_id: form.account_id });
      refresh();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setCreating(false);
    }
  };

  const onSend = async (p: Payment) => {
    if (!window.confirm(`Send payment ${p.reference} (${money(p.amount, p.currency)})?`)) {
      return;
    }
    setSendingId(p.id);
    setError(null);
    setNotice(null);
    try {
      const res = await sendPayment(p.id);
      setNotice(
        `Sent — bank reference ${res.bank_reference}` +
          (res.outbox_file ? `, outbox file ${res.outbox_file}` : ""),
      );
      refresh();
    } catch (err) {
      setError((err as Error).message);
      refresh();
    } finally {
      setSendingId(null);
    }
  };

  return (
    <>
      <h1>Payments</h1>
      <p className="page-sub">
        Create a pending payment, then dispatch it through the bank client.
      </p>

      {error && <div className="error-box">{error}</div>}
      {notice && <div className="success-box">{notice}</div>}

      <div className="panel">
        <h2>New payment</h2>
        <form className="form-grid" onSubmit={onCreate}>
          <div>
            <label className="field" htmlFor="p-account">From account</label>
            <select
              id="p-account"
              value={form.account_id}
              onChange={set("account_id")}
              required
            >
              <option value="" disabled>
                Select…
              </option>
              {accounts.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.bank_name} {a.account_number_masked} ({a.currency})
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="field" htmlFor="p-amount">Amount</label>
            <input
              id="p-amount"
              value={form.amount}
              onChange={set("amount")}
              placeholder="2500.75"
              inputMode="decimal"
              required
            />
          </div>
          <div>
            <label className="field" htmlFor="p-cp">Counterparty</label>
            <input
              id="p-cp"
              value={form.counterparty}
              onChange={set("counterparty")}
              placeholder="Vendor Co"
              required
              maxLength={200}
            />
          </div>
          <div>
            <label className="field" htmlFor="p-ref">Reference</label>
            <input
              id="p-ref"
              value={form.reference}
              onChange={set("reference")}
              placeholder="INV-001"
              required
              maxLength={100}
            />
          </div>
          <div>
            <label className="field" htmlFor="p-method">Method</label>
            <select id="p-method" value={form.payment_method} onChange={set("payment_method")}>
              {METHODS.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="field" htmlFor="p-note">Note (optional)</label>
            <input id="p-note" value={form.note} onChange={set("note")} maxLength={500} />
          </div>
          <div>
            <button
              className="btn"
              type="submit"
              disabled={creating || accounts.length === 0}
            >
              {creating ? "Creating…" : "Create payment"}
            </button>
          </div>
        </form>
        {accounts.length === 0 && (
          <div className="empty">Create a bank account first — payments draw on an account.</div>
        )}
      </div>

      <div className="panel">
        <h2>All payments</h2>
        {payments.length === 0 ? (
          <div className="empty">No payments yet.</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Reference</th>
                <th>Counterparty</th>
                <th>From</th>
                <th className="num">Amount</th>
                <th>Method</th>
                <th>Status</th>
                <th>Sent</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {payments.map((p) => (
                <tr key={p.id}>
                  <td className="mono">{p.reference}</td>
                  <td>{p.counterparty}</td>
                  <td className="muted">{accountLabel(p.account_id)}</td>
                  <td className="num">{money(p.amount, p.currency)}</td>
                  <td>{p.payment_method}</td>
                  <td>
                    <span
                      className={`badge ${p.status === "sent" ? "badge-ok" : "badge-warn"}`}
                      title={p.bank_reference ? `bank ref ${p.bank_reference}` : "not sent"}
                    >
                      {p.status}
                    </span>
                  </td>
                  <td className="muted">{dateTime(p.sent_at)}</td>
                  <td className="num">
                    {p.status === "pending" ? (
                      <button
                        className="btn btn-sm"
                        onClick={() => onSend(p)}
                        disabled={sendingId === p.id}
                      >
                        {sendingId === p.id ? "Sending…" : "Send"}
                      </button>
                    ) : (
                      <span className="mono muted" title={p.outbox_file ?? undefined}>
                        {p.bank_reference}
                      </span>
                    )}
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
