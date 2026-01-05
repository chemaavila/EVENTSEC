export const isOtUiEnabled = () =>
  (import.meta.env.VITE_ENABLE_OT_UI ?? "false") === "true";
