import type { CtiAdapter } from "./adapter";

export function createApiAdapter(): CtiAdapter {
  return {
    async getDashboard() {
      throw new Error("CTI API adapter not implemented yet. Set VITE_CTI_USE_MOCK=true.");
    },
    async getSearchResults() {
      throw new Error("CTI API adapter not implemented yet. Set VITE_CTI_USE_MOCK=true.");
    },
    async getEntityDetail() {
      throw new Error("CTI API adapter not implemented yet. Set VITE_CTI_USE_MOCK=true.");
    },
    async getGraphData() {
      throw new Error("CTI API adapter not implemented yet. Set VITE_CTI_USE_MOCK=true.");
    },
    async getAttackMatrix() {
      throw new Error("CTI API adapter not implemented yet. Set VITE_CTI_USE_MOCK=true.");
    },
    async getIndicatorsHub() {
      throw new Error("CTI API adapter not implemented yet. Set VITE_CTI_USE_MOCK=true.");
    },
    async getReports() {
      throw new Error("CTI API adapter not implemented yet. Set VITE_CTI_USE_MOCK=true.");
    },
    async getCases() {
      throw new Error("CTI API adapter not implemented yet. Set VITE_CTI_USE_MOCK=true.");
    },
    async getPlaybooks() {
      throw new Error("CTI API adapter not implemented yet. Set VITE_CTI_USE_MOCK=true.");
    },
    async getConnectors() {
      throw new Error("CTI API adapter not implemented yet. Set VITE_CTI_USE_MOCK=true.");
    },
    subscribeStreamEvents() {
      return () => undefined;
    },
  };
}
