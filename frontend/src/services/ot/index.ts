import { createApiAdapter } from "./apiAdapter";
import { createMockAdapter } from "./mockAdapter";
import type { OtAdapter } from "./adapter";

const getLocalOverride = () => {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem("ot_use_mock");
};

const isDev = import.meta.env.DEV;
const envDefault = (import.meta.env.VITE_OT_USE_MOCK ?? "true") !== "false";
const localOverride = isDev ? getLocalOverride() : null;
const useMock = localOverride ? localOverride === "true" : envDefault;

const adapter: OtAdapter = useMock ? createMockAdapter() : createApiAdapter();

export default adapter;
export type { OtAdapter, OtOverviewResponse } from "./adapter";
