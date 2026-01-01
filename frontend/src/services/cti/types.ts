export type CtiTrend = "up" | "down" | "flat";

export type CtiTag = {
  label: string;
  textColor: string;
  background: string;
  borderColor: string;
};

export type CtiKpi = {
  id: string;
  label: string;
  value: string;
  icon: string;
  trend: {
    direction: CtiTrend;
    label: string;
  };
};

export type CtiConfidence = {
  score: number;
  barColor: string;
};

export type CtiRecentIntelItem = {
  id: string;
  icon: string;
  iconBackground: string;
  iconColor: string;
  name: string;
  source: string;
  confidence: CtiConfidence;
  tags: CtiTag[];
  updatedAt: string;
};

export type CtiTechnique = {
  id: string;
  label: string;
  count: number;
  intensity: number;
};

export type CtiStreamEvent = {
  id: string;
  icon: string;
  iconBackground: string;
  iconColor: string;
  message: string;
  timestamp: string;
};

export type CtiDashboardData = {
  kpis: CtiKpi[];
  recentIntel: CtiRecentIntelItem[];
  topTechniques: CtiTechnique[];
  streamEvents: CtiStreamEvent[];
};

export type CtiSearchTlp = "red" | "amber" | "green" | "white";

export type CtiSearchResult = {
  id: string;
  typeIcon: string;
  typeIconBackground: string;
  typeIconColor: string;
  value: string;
  summary: string;
  confidence: {
    label: string;
    background: string;
    textColor: string;
    borderColor: string;
  };
  reliability: string;
  tlp: CtiSearchTlp;
  source: string;
  lastSeen: string;
};

export type CtiSearchData = {
  results: CtiSearchResult[];
  total: number;
  durationSeconds: number;
};

export type CtiEntityTimelineItem = {
  id: string;
  title: string;
  timestamp: string;
  description: string;
  dotColor: string;
};

export type CtiEntityLinkedItem = {
  id: string;
  icon: string;
  iconColor: string;
  title: string;
  subtitle: string;
};

export type CtiEntityCase = {
  id: string;
  severity: string;
  severityColor: string;
  summary: string;
  updatedAt?: string;
  showClock?: boolean;
};

export type CtiEntityDetail = {
  id: string;
  typeLabel: string;
  statusText: string;
  firstSeenLabel: string;
  description: string;
  externalReferences: string[];
  technicalDetails: {
    asn: string;
    country: string;
    countryCode: string;
    firstSeen: string;
    lastSeen: string;
    reverseDns: string;
  };
  timeline: CtiEntityTimelineItem[];
  linkedEntities: CtiEntityLinkedItem[];
  mitreTechniques: string[];
  mitreDescription: string;
  linkedCases: CtiEntityCase[];
  locationLabel: string;
};

export type CtiGraphNode = {
  id: string;
  label: string;
  type: string;
  x: string;
  y: string;
  icon: string;
  borderColor: string;
  textColor: string;
  score?: number;
  tooltip?: {
    title: string;
    subtitle: string;
    riskLabel: string;
    riskColor: string;
  };
};

export type CtiGraphEdge = {
  id: string;
  x1: string;
  y1: string;
  x2: string;
  y2: string;
  color: string;
  width: number;
  dashed?: boolean;
};

export type CtiGraphConnection = {
  id: string;
  icon: string;
  iconColor: string;
  label: string;
  relation: string;
};

export type CtiGraphData = {
  nodes: CtiGraphNode[];
  edges: CtiGraphEdge[];
  selectedNode: {
    id: string;
    riskScore: string;
    riskNote: string;
    properties: Array<{ label: string; value: string; copyable?: boolean }>;
    location: string;
    asn: string;
    firstSeen: string;
    connections: CtiGraphConnection[];
  };
};

export type CtiAttackTechnique = {
  id: string;
  name: string;
  count?: number;
  severity?: "high" | "medium" | "low" | "none";
  active?: boolean;
  highlighted?: boolean;
};

export type CtiAttackTactic = {
  id: string;
  name: string;
  detectedCount: number;
  techniques: CtiAttackTechnique[];
};

export type CtiAttackLinkedIntel = {
  id: string;
  title: string;
  category: string;
  relevance?: "high" | "medium" | "low";
  note?: string;
};

export type CtiAttackSighting = {
  id: string;
  timestamp: string;
  title: string;
  host: string;
  high?: boolean;
};

export type CtiAttackDetail = {
  code: string;
  title: string;
  confidenceLabel: string;
  alertsCount: number;
  description: string;
  linkedIntel: CtiAttackLinkedIntel[];
  sightings: CtiAttackSighting[];
};

export type CtiAttackData = {
  tactics: CtiAttackTactic[];
  selected: CtiAttackDetail;
};

export type CtiIndicatorRow = {
  id: string;
  value: string;
  typeLabel: string;
  typeIcon: string;
  lastSeen: string;
  enrichmentStatus: "complete" | "enriching" | "failed";
  riskLabel?: string;
  riskScore?: number;
  riskSeverity?: "high" | "critical" | "low";
  selected?: boolean;
};

export type CtiIndicatorsDrawer = {
  id: string;
  riskScore: number;
  riskLabel: string;
  confidence: string;
  firstSeen: string;
  lastSeen: string;
  source: string;
  country: string;
  tags: string[];
  incidents: Array<{ id: string; summary: string }>;
};

export type CtiIndicatorsData = {
  observablesCount: string;
  indicatorsCount: string;
  rows: CtiIndicatorRow[];
  drawer: CtiIndicatorsDrawer;
};

export type CtiReportMarker = {
  label: string;
  color: string;
  textColor: string;
};

export type CtiReportListItem = {
  id: string;
  source: string;
  sourceIcon: string;
  title: string;
  summary: string;
  markers: CtiReportMarker[];
  createdAt: string;
  objects: number;
  selected?: boolean;
};

export type CtiReportObservable = {
  id: string;
  icon: string;
  color: string;
  value: string;
  type: string;
};

export type CtiReportRelationship = {
  id: string;
  icon: string;
  color: string;
  label: string;
  value: string;
};

export type CtiReportsData = {
  reports: CtiReportListItem[];
  detail: {
    id: string;
    title: string;
    summary: string;
    observablesCount: number;
    observables: CtiReportObservable[];
    relationships: CtiReportRelationship[];
    ingested: string;
    updated: string;
  };
};

export type CtiCaseRow = {
  id: string;
  title: string;
  status: string;
  statusStyle: "open" | "in-progress" | "closed";
  severity: string;
  severityColor: string;
  assignee: string;
  assigneeAvatar?: string;
  assigneeInitials?: string;
  entities: number;
  lastUpdated: string;
  selected?: boolean;
};

export type CtiCaseChecklistItem = {
  id: string;
  text: string;
  completed: boolean;
  note?: string;
};

export type CtiCaseTimelineItem = {
  id: string;
  author: string;
  time: string;
  content: string;
  highlight?: boolean;
  system?: boolean;
  critical?: boolean;
};

export type CtiCasesData = {
  cases: CtiCaseRow[];
  detail: {
    id: string;
    severity: string;
    title: string;
    checklistProgress: string;
    checklist: CtiCaseChecklistItem[];
    timeline: CtiCaseTimelineItem[];
  };
};

export type CtiPlaybookStep = {
  id: string;
  label: string;
  title: string;
  subtitle: string;
  icon: string;
  accent: string;
};

export type CtiPlaybookComponent = {
  id: string;
  title: string;
  subtitle?: string;
  icon: string;
  color?: string;
};

export type CtiPlaybookExecution = {
  id: string;
  time: string;
  status: string;
  color: string;
  active?: boolean;
};

export type CtiPlaybookLogLine = {
  time: string;
  level: string;
  message: string;
};

export type CtiPlaybooksData = {
  title: string;
  status: string;
  description: string;
  quotaUsage: number;
  quotaLabel: string;
  steps: CtiPlaybookStep[];
  branches: CtiPlaybookStep[];
  components: {
    logic: CtiPlaybookComponent[];
    actions: CtiPlaybookComponent[];
  };
  executions: CtiPlaybookExecution[];
  logLines: CtiPlaybookLogLine[];
  exception: string;
};

export type CtiConnectorStat = {
  id: string;
  label: string;
  value: string;
  icon: string;
  color: string;
};

export type CtiConnectorItem = {
  id: string;
  name: string;
  subtitle: string;
  type: string;
  status: string;
  statusColor: string;
  lastSync: string;
  selected?: boolean;
};

export type CtiConnectorDetail = {
  name: string;
  status: string;
  version: string;
  apiEndpoint: string;
  clientId: string;
  apiKeyMasked: string;
  syncInterval: string;
  heartbeat: string;
  heartbeatTime: string;
  lastExecution: string;
  lastExecutionDetail: string;
  logs: string[];
};

export type CtiConnectorsData = {
  stats: CtiConnectorStat[];
  connectors: CtiConnectorItem[];
  detail: CtiConnectorDetail;
  assistant: {
    title: string;
    message: string;
    subtitle: string;
    progress: number;
  };
};
