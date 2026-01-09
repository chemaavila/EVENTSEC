export const defaultFeatureFlags = {
  intel: (import.meta.env.VITE_FEATURE_INTEL ?? "false") === "true",
  ot: (import.meta.env.VITE_FEATURE_OT ?? "false") === "true",
  emailActions: (import.meta.env.VITE_FEATURE_EMAIL_ACTIONS ?? "false") === "true",
  vulnIntel: (import.meta.env.VITE_FEATURE_VULN_INTEL ?? "false") === "true",
  threatmapFallbackCoords:
    (import.meta.env.VITE_THREATMAP_FALLBACK_COORDS ?? "false") === "true",
};
