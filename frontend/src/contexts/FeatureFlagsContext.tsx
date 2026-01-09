import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { fetchFeatureFlags, type FeatureFlagsResponse } from "../services/api";
import { defaultFeatureFlags } from "../lib/featureFlags";

export type FeatureFlags = {
  intel: boolean;
  ot: boolean;
  emailActions: boolean;
  vulnIntel: boolean;
  threatmapFallbackCoords: boolean;
  detectionQueueMode?: string;
};

type FeatureFlagsContextValue = {
  flags: FeatureFlags;
  loading: boolean;
  error: string | null;
};

const FeatureFlagsContext = createContext<FeatureFlagsContextValue>({
  flags: defaultFeatureFlags,
  loading: true,
  error: null,
});

const mapFlags = (payload: FeatureFlagsResponse): FeatureFlags => ({
  intel: payload.feature_intel_enabled,
  ot: payload.feature_ot_enabled,
  emailActions: payload.feature_email_actions_enabled,
  vulnIntel: payload.vuln_intel_enabled,
  threatmapFallbackCoords: payload.threatmap_fallback_coords,
  detectionQueueMode: payload.detection_queue_mode,
});

export const FeatureFlagsProvider = ({
  children,
  initialFlags,
  disableFetch,
}: {
  children: React.ReactNode;
  initialFlags?: Partial<FeatureFlags>;
  disableFetch?: boolean;
}) => {
  const [flags, setFlags] = useState<FeatureFlags>({
    ...defaultFeatureFlags,
    ...initialFlags,
  });
  const [loading, setLoading] = useState(!disableFetch);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (disableFetch) return;
    let active = true;
    fetchFeatureFlags()
      .then((data) => {
        if (!active) return;
        setFlags({ ...defaultFeatureFlags, ...mapFlags(data) });
        setError(null);
      })
      .catch((err) => {
        if (!active) return;
        setError(err instanceof Error ? err.message : "Failed to load feature flags");
      })
      .finally(() => {
        if (!active) return;
        setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [disableFetch]);

  const value = useMemo(() => ({ flags, loading, error }), [flags, loading, error]);

  return (
    <FeatureFlagsContext.Provider value={value}>
      {children}
    </FeatureFlagsContext.Provider>
  );
};

export const useFeatureFlags = () => useContext(FeatureFlagsContext);
