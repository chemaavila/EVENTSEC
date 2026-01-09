export type AttackType =
  | "Web"
  | "DDoS"
  | "Intrusion"
  | "Scanner"
  | "Anonymizer"
  | "Bot"
  | "Malware"
  | "Phishing"
  | "DNS"
  | "Email";

export type Endpoint = {
  ip?: string | null;
  asn?: { asn?: string | null; org?: string | null } | null;
  geo?: {
    lat?: number | null;
    lon?: number | null;
    country?: string | null;
    city?: string | null;
    approx?: boolean | null;
  } | null;
};

export type AttackEvent = {
  id: string;
  ts: string;
  attack_type: AttackType;
  severity: number;
  volume?: { pps?: number | null; bps?: number | null } | null;
  src: Endpoint;
  dst: Endpoint;
  tags: string[];
  confidence: number; // 0..1
  source: string;
  real: boolean;
  ttl_ms: number;
  expires_at: string;
  is_major: boolean;
  seq?: number | null;
  server_ts?: string | null;
};
