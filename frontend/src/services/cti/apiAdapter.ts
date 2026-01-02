import type { CtiAdapter } from "./adapter";

export class CtiNotImplementedError extends Error {
  constructor() {
    super("CTI API adapter not implemented yet. Set VITE_CTI_USE_MOCK=true.");
    this.name = "CtiNotImplementedError";
  }
}

const notImplemented = (): never => {
  throw new CtiNotImplementedError();
};

export function createApiAdapter(): CtiAdapter {
  return {
    async getDashboard() {
      return notImplemented();
    },
    async getSearchResults() {
      return notImplemented();
    },
    async getEntityDetail() {
      return notImplemented();
    },
    async getGraphData() {
      return notImplemented();
    },
    async getAttackMatrix() {
      return notImplemented();
    },
    async getIndicatorsHub() {
      return notImplemented();
    },
    async getReports() {
      return notImplemented();
    },
    async getCases() {
      return notImplemented();
    },
    async getPlaybooks() {
      return notImplemented();
    },
    async getConnectors() {
      return notImplemented();
    },
    subscribeStreamEvents() {
      return () => undefined;
    },
  };
}
