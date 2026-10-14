import { useCallback, useEffect, useState } from "react";
import {
  getForecast,
  listEntities,
  money,
  pullForecast,
  shortDate,
  type Entity,
  type ForecastRow,
} from "../api";

const W = 860;
const H = 280;
const PAD = { top: 16, right: 16, bottom: 28, left: 70 };

/**
 * Line chart of closing balance with inflow/outflow bars, drawn as plain SVG
 * (no charting dependency).
 */
function ForecastChart({ rows, currency }: { rows: ForecastRow[]; currency: string }) {
  const innerW = W - PAD.left - PAD.right;
  const innerH = H - PAD.top - PAD.bottom;

  const closings = rows.map((r) => Number(r.closing_balance));
  const flows = rows.flatMap((r) => [Number(r.inflows), Number(r.outflows)]);
  const dataMin = Math.min(...closings, ...flows);
  const dataMax = Math.max(...closings, ...flows);
  // Nice-ish range with a little headroom.
  const lo = Math.min(0, dataMin);
  const hi = dataMax + (dataMax - lo) * 0.08 || 1;

  const x = (i: number) =>
    PAD.left + (rows.length === 1 ? innerW / 2 : (i / (rows.length - 1)) * innerW);
  const y = (v: number) => PAD.top + innerH - ((v - lo) / (hi - lo)) * innerH;

  const linePath = rows
    .map(
      (r, i) =>
        `${i === 0 ? "M" : "L"}${x(i).toFixed(1)},${y(Number(r.closing_balance)).toFixed(1)}`,
    )
    .join(" ");

  const barW = Math.max(4, Math.min(14, innerW / rows.length / 3));
  const ticks = 4;
  const gridVals = Array.from({ length: ticks + 1 }, (_, i) => lo + ((hi - lo) * i) / ticks);

  const fmtCompact = (v: number) =>
    new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 }).format(v);

  return (
    <div className="chart-wrap">
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label="Cash forecast chart">
        {gridVals.map((v) => (
          <g key={v}>
            <line
              x1={PAD.left}
              x2={W - PAD.right}
              y1={y(v)}
              y2={y(v)}
              stroke="#e3e8f0"
              strokeWidth={1}
            />
            <text x={PAD.left - 8} y={y(v) + 4} textAnchor="end" fontSize={11} fill="#66708a">
              {fmtCompact(v)}
            </text>
          </g>
        ))}
        {rows.map((r, i) => {
          const inflow = Number(r.inflows);
          const outflow = Number(r.outflows);
          const cx = x(i);
          return (
            <g key={r.id}>
              <rect
                x={cx - barW - 1}
                y={y(inflow)}
                width={barW}
                height={Math.max(0, PAD.top + innerH - y(inflow))}
                fill="#7fbfa0"
                opacity={0.55}
                rx={1.5}
              />
              <rect
                x={cx + 1}
                y={y(outflow)}
                width={barW}
                height={Math.max(0, PAD.top + innerH - y(outflow))}
                fill="#e2a1a1"
                opacity={0.55}
                rx={1.5}
              />
            </g>
          );
        })}
        <path d={linePath} fill="none" stroke="#2f5fda" strokeWidth={2.5} />
        {rows.map((r, i) => (
          <circle key={r.id} cx={x(i)} cy={y(Number(r.closing_balance))} r={3} fill="#2f5fda" />
        ))}
        {rows.map((r, i) =>
          i % Math.ceil(rows.length / 7 || 1) === 0 ? (
            <text
              key={`lbl-${r.id}`}
              x={x(i)}
              y={H - 8}
              textAnchor="middle"
              fontSize={11}
              fill="#66708a"
            >
              {new Date(r.as_of_date).toLocaleDateString("en-US", {
                month: "short",
                day: "numeric",
              })}
            </text>
          ) : null,
        )}
      </svg>
      <div className="chart-legend">
        <span>
          <span className="dot" style={{ background: "#2f5fda" }} />
          Closing balance ({currency})
        </span>
        <span>
          <span className="dot" style={{ background: "#7fbfa0" }} />
          Inflows
        </span>
        <span>
          <span className="dot" style={{ background: "#e2a1a1" }} />
          Outflows
        </span>
      </div>
    </div>
  );
}

export default function Forecast() {
  const [entities, setEntities] = useState<Entity[]>([]);
  const [entityId, setEntityId] = useState<number | "">("");
  const [rows, setRows] = useState<ForecastRow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [pulling, setPulling] = useState(false);

  useEffect(() => {
    listEntities()
      .then((e) => {
        setEntities(e);
        if (e.length > 0) setEntityId(e[0].id);
      })
      .catch((err: Error) => setError(err.message));
  }, []);

  const refresh = useCallback(() => {
    if (entityId === "") {
      setRows([]);
      return;
    }
    getForecast(entityId)
      .then((r) => {
        setRows(r);
        setError(null);
      })
      .catch((err: Error) => setError(err.message));
  }, [entityId]);

  useEffect(refresh, [refresh]);

  const onPull = async () => {
    if (entityId === "") return;
    setPulling(true);
    setError(null);
    setNotice(null);
    try {
      const res = await pullForecast(entityId);
      setNotice(
        res.rows_imported > 0
          ? `Pulled ${res.rows_imported} rows from ${res.source} as of ${shortDate(res.as_of_date)}.`
          : "Pull returned no rows.",
      );
      refresh();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setPulling(false);
    }
  };

  const first = rows[0];
  const last = rows.at(-1);
  const totalIn = rows.reduce((s, r) => s + Number(r.inflows), 0);
  const totalOut = rows.reduce((s, r) => s + Number(r.outflows), 0);
  const currency = first?.currency ?? "USD";

  return (
    <>
      <h1>Cash forecast</h1>
      <p className="page-sub">
        14-day forecast pulled from the (mock) Kyriba client and stored locally.
      </p>

      <div className="toolbar">
        <label className="field" htmlFor="f-entity" style={{ margin: 0 }}>
          Entity
        </label>
        <select
          id="f-entity"
          value={entityId}
          onChange={(e) => setEntityId(e.target.value === "" ? "" : Number(e.target.value))}
          style={{ width: 260 }}
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
        <button className="btn" onClick={onPull} disabled={pulling || entityId === ""}>
          {pulling ? "Pulling…" : "Pull forecast"}
        </button>
      </div>

      {error && <div className="error-box">{error}</div>}
      {notice && <div className="success-box">{notice}</div>}

      {entities.length === 0 && (
        <div className="panel">
          <div className="empty">Create an entity first — forecasts belong to an entity.</div>
        </div>
      )}

      {rows.length > 0 && (
        <>
          <div className="cards">
            <div className="card">
              <div className="card-label">Opening ({shortDate(first!.as_of_date)})</div>
              <div className="card-value">{money(first!.opening_balance, currency)}</div>
            </div>
            <div className="card">
              <div className="card-label">Total inflows</div>
              <div className="card-value">{money(totalIn, currency)}</div>
            </div>
            <div className="card">
              <div className="card-label">Total outflows</div>
              <div className="card-value">{money(totalOut, currency)}</div>
            </div>
            <div className="card">
              <div className="card-label">Closing ({shortDate(last!.as_of_date)})</div>
              <div className="card-value">{money(last!.closing_balance, currency)}</div>
            </div>
          </div>

          <div className="panel">
            <h2>Projected balance</h2>
            <ForecastChart rows={rows} currency={currency} />
          </div>

          <div className="panel">
            <h2>Daily detail</h2>
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th className="num">Opening</th>
                  <th className="num">Inflows</th>
                  <th className="num">Outflows</th>
                  <th className="num">Closing</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.id}>
                    <td>{shortDate(r.as_of_date)}</td>
                    <td className="num">{money(r.opening_balance, r.currency)}</td>
                    <td className="num">{money(r.inflows, r.currency)}</td>
                    <td className="num">{money(r.outflows, r.currency)}</td>
                    <td className="num">
                      <strong>{money(r.closing_balance, r.currency)}</strong>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {rows.length === 0 && entityId !== "" && entities.length > 0 && (
        <div className="panel">
          <div className="empty">
            No stored forecast for this entity yet — press “Pull forecast”.
          </div>
        </div>
      )}

    </>
  );
}

