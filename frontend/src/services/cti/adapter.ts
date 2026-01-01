import type {
  CtiDashboardData,
  CtiEntityDetail,
  CtiAttackData,
  CtiGraphData,
  CtiIndicatorsData,
  CtiReportsData,
  CtiCasesData,
  CtiPlaybooksData,
  CtiConnectorsData,
  CtiSearchData,
  CtiStreamEvent,
} from "./types";

export type StreamEventHandler = (event: CtiStreamEvent) => void;

export interface CtiAdapter {
  getDashboard(): Promise<CtiDashboardData>;
  getSearchResults(): Promise<CtiSearchData>;
  getEntityDetail(): Promise<CtiEntityDetail>;
  getGraphData(): Promise<CtiGraphData>;
  getAttackMatrix(): Promise<CtiAttackData>;
  getIndicatorsHub(): Promise<CtiIndicatorsData>;
  getReports(): Promise<CtiReportsData>;
  getCases(): Promise<CtiCasesData>;
  getPlaybooks(): Promise<CtiPlaybooksData>;
  getConnectors(): Promise<CtiConnectorsData>;
  subscribeStreamEvents(handler: StreamEventHandler): () => void;
}
