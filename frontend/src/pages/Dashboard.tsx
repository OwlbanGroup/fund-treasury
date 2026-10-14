import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  getForecast,
  listAccounts,
  listEntities,
  listPayments,
  money,
  moneyCompact,
  shortDate,
  type Account,
  type Entity,
  type ForecastRow,
  type Payment,
} from "../api";

interface Totals {
  current: number;
  available: number;
  currency: string;
}

/** Sum balances per currency; returns the dominant (first) currency totals. */
function sumBalances(accounts: Account[]): Totals {
  let current = 0;
  let available = 0;
  let currency = "USD";
  for (const a of accounts) {
    current += Number(a.current_balance);
    available += Number(a.available_balance);
    if (!currency || currency === "USD") currency = a.currency;
  }
  return { current, available, currency };
}

export default function Dashboard() {
  const [entities, setEntities] = useState<Entity[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [forecast, setForecast] = useState<ForecastRow[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([listEntities(), listAccounts(), listPayments()])
      .then(([e, a, p]) => {
        setEntities(e);
        setAccounts(a);
        setPayments(p);
        if (e.length > 0) {
          getForecast(e[0].id).then(setForecast).catch(() => setForecast([]));
        }
      })
      .catch((err: Error) => setError(err.message));
  }, []);

  const totals = sumBalances(accounts);
  const pending = payments.filter((p) => p.status === "pending");
  const sent = payments.filter((p) => p.status === "sent");
  const pendingAmount = pending.reduce((s, p) => s + Number(p.amount), 0);
  const sentAmount = sent.reduce((s, p) => s + Number(p.amount), 0);
  const lastRow = forecast.at(-1);

  return (
    <>
      <h1>Dashboard</h1>
      <p className="page-sub">
        Treasury overview across {entities.length}{" "}
        {entities.length === 1 ? "entity" : "entities"} and{" "}
        {accounts.length} {accounts.length === 1 ? "account" : "accounts"}.
      </p>

      {error && <div className="error-box">{error}</div>}

      <div className="cards">
        <div className="card">
          <div className="card-label">Total current balance</div>
          <div className="card-value">
            {accounts.length ? moneyCompact(totals.current, totals.currency) : "—"}
          </div>
          <div className="card-note">
            {accounts.length
              ? `${money(totals.current, totals.currency)} · available ${money(totals.available, totals.currency)}`
              : "no accounts yet"}
          </div>
        </div>
        <div className="card">
          <div className="card-label">Pending payments</div>
          <div className="card-value">{pending.length}</div>
          <div className="card-note">
            {pending.length ? money(pendingAmount, "USD") : "nothing awaiting send"}
          </div>
        </div>
        <div className="card">
          <div className="card-label">Sent payments</div>
          <div className="card-value">{sent.length}</div>
          <div className="card-note">
            {sent.length ? money(sentAmount, "USD") + " dispatched" : "none dispatched"}
          </div>
        </div>
        <div className="card">
          <div className="card-label">Forecast (latest closing)</div>
          <div className="card-value">
            {lastRow ? moneyCompact(lastRow.closing_balance, lastRow.currency) : "—"}
          </div>
          <div className="card-note">
            {lastRow
              ? `as of ${shortDate(lastRow.as_of_date)} · ${entities[0]?.code ?? ""}`
              : "no forecast pulled"}
          </div>
        </div>
      </div>

      <div className="panel">
        <h2>Recent payments</h2>
        {payments.length === 0 ? (
          <div className="empty">
            No payments yet — create one on the <Link to="/payments">Payments</Link> page.
          </div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Reference</th>
                <th>Counterparty</th>
                <th className="num">Amount</th>
                <th>Method</th>
                <th>Status</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {payments.slice(0, 6).map((p) => (
                <tr key={p.id}>
                  <td className="mono">{p.reference}</td>
                  <td>{p.counterparty}</td>
                  <td className="num">{money(p.amount, p.currency)}</td>
                  <td>{p.payment_method}</td>
                  <td>
                    <span className={`badge ${p.status === "sent" ? "badge-ok" : "badge-warn"}`}>
                      {p.status}
                    </span>
                  </td>
                  <td className="muted">{shortDate(p.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}
