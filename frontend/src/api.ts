/**
 * Typed client for the Fund Treasury API.
 *
 * Mirrors the Pydantic response schemas in ../backend/app/schemas/*. Decimal
 * fields serialise as JSON strings, so money types are `string` here and parsed
 * only for display/aggregation.
 */

/** Base URL. Empty in dev (Vite proxies API paths to the backend). */
const BASE: string = (import.meta.env.VITE_API_URL as string | undefined) ?? "";

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...init,
    });
  } catch {
    throw new ApiError(0, "Cannot reach the API — is the backend running?");
  }
  if (!res.ok) {
    let detail = res.statusText || `HTTP ${res.status}`;
    try {
      const body: unknown = await res.json();
      const d = (body as { detail?: unknown })?.detail;
      if (typeof d === "string") detail = d;
      else if (d != null) detail = JSON.stringify(d);
    } catch {
      /* non-JSON error body — keep statusText */
    }
    throw new ApiError(res.status, detail);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

// --- Types (mirror backend schemas) ----------------------------------------

export interface Entity {
  id: number;
  name: string;
  code: string;
  base_currency: string;
  created_at: string;
}

export interface Account {
  id: number;
  entity_id: number;
  bank_name: string;
  account_number_masked: string;
  account_type: string;
  currency: string;
  current_balance: string;
  available_balance: string;
  status: string;
  created_at: string;
}

export interface Payment {
  id: number;
  account_id: number;
  currency: string;
  amount: string;
  counterparty: string;
  reference: string;
  payment_method: string;
  status: string;
  outbox_file: string | null;
  bank_reference: string | null;
  note: string | null;
  created_at: string;
  sent_at: string | null;
}

export interface PaymentSendResponse {
  payment: Payment;
  bank_reference: string;
  outbox_file: string | null;
}

export interface ForecastRow {
  id: number;
  entity_id: number;
  as_of_date: string;
  currency: string;
  opening_balance: string;
  inflows: string;
  outflows: string;
  closing_balance: string;
  created_at: string;
}

export interface ForecastPullResponse {
  entity_id: number;
  rows_imported: number;
  as_of_date: string;
  source: string;
}

export interface Health {
  status: string;
  kyriba_mode: string;
  bank_mode: string;
  database: string;
}

export interface EntityCreate {
  name: string;
  code: string;
  base_currency: string;
}

export interface AccountCreate {
  entity_id: number;
  bank_name: string;
  account_number_masked: string;
  account_type: string;
  currency: string;
  current_balance: string;
  available_balance: string;
}

export interface PaymentCreate {
  account_id: number;
  amount: string;
  counterparty: string;
  reference: string;
  payment_method: string;
  note?: string;
}

// --- Health -----------------------------------------------------------------

export const getHealth = () => request<Health>("/health");

// --- Entities ---------------------------------------------------------------

export const listEntities = () => request<Entity[]>("/entities");

export const createEntity = (payload: EntityCreate) =>
  request<Entity>("/entities", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const deleteEntity = (id: number) =>
  request<void>(`/entities/${id}`, { method: "DELETE" });

// --- Accounts ---------------------------------------------------------------

export const listAccounts = (entityId?: number) =>
  request<Account[]>(
    entityId == null ? "/accounts" : `/accounts?entity_id=${entityId}`,
  );

export const createAccount = (payload: AccountCreate) =>
  request<Account>("/accounts", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const deleteAccount = (id: number) =>
  request<void>(`/accounts/${id}`, { method: "DELETE" });

// --- Payments ---------------------------------------------------------------

export const listPayments = (accountId?: number) =>
  request<Payment[]>(
    accountId == null ? "/payments" : `/payments?account_id=${accountId}`,
  );

export const createPayment = (payload: PaymentCreate) =>
  request<Payment>("/payments", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const sendPayment = (id: number) =>
  request<PaymentSendResponse>(`/payments/${id}/send`, { method: "POST" });

// --- Forecast ---------------------------------------------------------------

export const pullForecast = (entityId: number) =>
  request<ForecastPullResponse>(`/entities/${entityId}/forecast/pull`, {
    method: "POST",
  });

export const getForecast = (entityId: number) =>
  request<ForecastRow[]>(`/entities/${entityId}/forecast`);

// --- Formatting helpers -----------------------------------------------------

const moneyFmt = (currency: string) =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: currency || "USD",
    maximumFractionDigits: 2,
  });

/** Format a decimal-string amount, e.g. "1234.5" -> "$1,234.50". */
export function money(value: string | number, currency = "USD"): string {
  const n = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(n)) return "—";
  return moneyFmt(currency).format(n);
}

/** Compact form for dashboard cards, e.g. "$1.25M". */
export function moneyCompact(value: string | number, currency = "USD"): string {
  const n = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(n)) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: currency || "USD",
    notation: "compact",
    maximumFractionDigits: 2,
  }).format(n);
}

/** "2026-10-13" -> "Oct 13, 2026"; tolerates full ISO timestamps. */
export function shortDate(value: string): string {
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

/** "2026-10-13T19:39:53" -> "Oct 13, 2026, 7:39 PM". */
export function dateTime(value: string | null): string {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

