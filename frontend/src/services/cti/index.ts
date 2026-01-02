import { createApiAdapter } from "./apiAdapter";
import { createMockAdapter } from "./mockAdapter";
import type { CtiAdapter } from "./adapter";

const getLocalOverride = () => {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem("cti_use_mock");
};

const envDefault = (import.meta.env.VITE_CTI_USE_MOCK ?? "true") !== "false";
const localOverride = getLocalOverride();
const useMock = localOverride ? localOverride === "true" : envDefault;

const adapter: CtiAdapter = useMock ? createMockAdapter() : createApiAdapter();

export default adapter;
export type { CtiAdapter } from "./adapter";
export type * from "./types";
