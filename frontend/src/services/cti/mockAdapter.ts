import type { CtiAdapter, StreamEventHandler } from "./adapter";
import type { CtiStreamEvent } from "./types";
import { dashboardFixture } from "../../fixtures/cti/dashboard";
import { searchResultsFixture } from "../../fixtures/cti/search_results";
import { entityDetailFixture } from "../../fixtures/cti/entity_detail";
import { graphFixture } from "../../fixtures/cti/graph";
import { attackMatrixFixture } from "../../fixtures/cti/attack_matrix";
import { indicatorsFixture } from "../../fixtures/cti/indicators";
import { reportsFixture } from "../../fixtures/cti/reports";
import { casesFixture } from "../../fixtures/cti/cases";
import { playbooksFixture } from "../../fixtures/cti/playbooks";
import { connectorsFixture } from "../../fixtures/cti/connectors";

const streamTemplates: Array<Omit<CtiStreamEvent, "id" | "timestamp">> = [
  {
    icon: "shield",
    iconBackground: "var(--alpha-14-165-233-0_12)",
    iconColor: "var(--palette-38bdf8)",
    message: "New inbound indicator batch tagged to Campaign \u0023210.",
  },
  {
    icon: "report",
    iconBackground: "var(--alpha-234-179-8-0_12)",
    iconColor: "var(--palette-f59e0b)",
    message: "Analyst X published a new intelligence report for review.",
  },
  {
    icon: "biotech",
    iconBackground: "var(--alpha-16-185-129-0_12)",
    iconColor: "var(--palette-10b981)",
    message: "Automated enrichment added 8 related domains to Case \u0023405.",
  },
];

const timeLabels = ["Just now", "1m ago", "2m ago", "4m ago", "7m ago", "10m ago"];

function createStreamEvent(index: number): CtiStreamEvent {
  const template = streamTemplates[index % streamTemplates.length];
  return {
    id: `stream-${Date.now()}-${index}`,
    ...template,
    timestamp: timeLabels[index % timeLabels.length],
  };
}

export function createMockAdapter(): CtiAdapter {
  return {
    async getDashboard() {
      return dashboardFixture;
    },
    async getSearchResults() {
      return searchResultsFixture;
    },
    async getEntityDetail() {
      return entityDetailFixture;
    },
    async getGraphData() {
      return graphFixture;
    },
    async getAttackMatrix() {
      return attackMatrixFixture;
    },
    async getIndicatorsHub() {
      return indicatorsFixture;
    },
    async getReports() {
      return reportsFixture;
    },
    async getCases() {
      return casesFixture;
    },
    async getPlaybooks() {
      return playbooksFixture;
    },
    async getConnectors() {
      return connectorsFixture;
    },
    subscribeStreamEvents(handler: StreamEventHandler) {
      let counter = 0;
      const interval = window.setInterval(() => {
        handler(createStreamEvent(counter));
        counter += 1;
      }, 12000);

      return () => {
        window.clearInterval(interval);
      };
    },
  };
}
