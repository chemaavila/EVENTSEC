interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_THREATMAP_WS_URL?: string;
  readonly VITE_EMAIL_PROTECT_BASE_URL?: string;
  readonly VITE_CTI_USE_MOCK?: "true" | "false";
  readonly VITE_ENABLE_OT_UI?: "true" | "false";
  readonly VITE_OT_USE_MOCK?: "true" | "false";
  readonly VITE_UI_DEBUG?: "true" | "false";
  readonly VITE_THREATMAP_STALE_MS?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
