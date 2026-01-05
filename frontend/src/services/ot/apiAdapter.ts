import type { OtAdapter } from "./adapter";

export class OtNotImplementedError extends Error {
  constructor() {
    super("OT API adapter not implemented yet. Set VITE_OT_USE_MOCK=true.");
    this.name = "OtNotImplementedError";
  }
}

const notImplemented = (): never => {
  throw new OtNotImplementedError();
};

export function createApiAdapter(): OtAdapter {
  return {
    async getOtOverview() {
      return notImplemented();
    },
    async listOtAssets() {
      return notImplemented();
    },
    async getOtAsset() {
      return notImplemented();
    },
    async listOtCommunications() {
      return notImplemented();
    },
    async listOtDetections() {
      return notImplemented();
    },
    async getOtDetection() {
      return notImplemented();
    },
    async listOtSensors() {
      return notImplemented();
    },
    async getOtSensor() {
      return notImplemented();
    },
    async createPcapJob() {
      return notImplemented();
    },
    async listPcapJobs() {
      return notImplemented();
    },
    async getPcapJob() {
      return notImplemented();
    },
  };
}
