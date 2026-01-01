import { createApiAdapter } from "./apiAdapter";
import { createMockAdapter } from "./mockAdapter";
import type { CtiAdapter } from "./adapter";

const useMock = (import.meta.env.VITE_CTI_USE_MOCK ?? "true") !== "false";

const adapter: CtiAdapter = useMock ? createMockAdapter() : createApiAdapter();

export default adapter;
export type { CtiAdapter } from "./adapter";
export type * from "./types";
