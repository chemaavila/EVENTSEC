import { EmptyState } from "./EmptyState";

export const FeatureDisabledState = ({
  title,
  message,
}: {
  title: string;
  message?: string;
}) => (
  <EmptyState
    title={`${title} disabled`}
    message={
      message ??
      "This module is currently disabled. Enable the feature flag to access it."
    }
  />
);
