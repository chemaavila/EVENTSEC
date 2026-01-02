import React from "react";

type ErrorBoundaryProps = {
  children: React.ReactNode;
};

type ErrorBoundaryState = {
  hasError: boolean;
  error?: Error;
};

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = {
    hasError: false,
  };

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error("Unhandled UI error", error, info);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: undefined });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="state state-error" role="alert">
          <div className="state-title">Something went wrong</div>
          <div className="state-text">
            An unexpected error occurred. Try reloading or return to the dashboard.
          </div>
          {this.state.error && (
            <details className="state-details">
              <summary>Error details</summary>
              <pre>{this.state.error.message}</pre>
            </details>
          )}
          <div className="state-action">
            <button type="button" className="btn btn-ghost btn-sm" onClick={this.handleReset}>
              Retry
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
