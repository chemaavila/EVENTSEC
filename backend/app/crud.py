from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import models


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    stmt = select(models.User).where(models.User.email == email.lower())
    return db.execute(stmt).scalar_one_or_none()


def get_user_by_id(db: Session, user_id: int) -> Optional[models.User]:
    stmt = select(models.User).where(models.User.id == user_id)
    return db.execute(stmt).scalar_one_or_none()


def list_users(db: Session) -> List[models.User]:
    stmt = select(models.User).order_by(models.User.id)
    return list(db.scalars(stmt))


def create_user(db: Session, user: models.User) -> models.User:
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user: models.User) -> models.User:
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_tenant_storage_policy(
    db: Session, tenant_id: str
) -> Optional[models.TenantStoragePolicy]:
    stmt = select(models.TenantStoragePolicy).where(
        models.TenantStoragePolicy.tenant_id == tenant_id
    )
    return db.execute(stmt).scalar_one_or_none()


def upsert_tenant_storage_policy(
    db: Session, tenant_id: str, updates: dict
) -> models.TenantStoragePolicy:
    policy = get_tenant_storage_policy(db, tenant_id)
    if policy is None:
        policy = models.TenantStoragePolicy(tenant_id=tenant_id)
    for key, value in updates.items():
        setattr(policy, key, value)
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy


def list_tenant_usage(
    db: Session, tenant_id: str, day_from, day_to
) -> List[models.TenantUsageDaily]:
    stmt = (
        select(models.TenantUsageDaily)
        .where(models.TenantUsageDaily.tenant_id == tenant_id)
        .where(models.TenantUsageDaily.day >= day_from)
        .where(models.TenantUsageDaily.day <= day_to)
        .order_by(models.TenantUsageDaily.day)
    )
    return list(db.scalars(stmt))


def get_agent_by_name(db: Session, name: str) -> Optional[models.Agent]:
    stmt = select(models.Agent).where(models.Agent.name == name)
    return db.execute(stmt).scalar_one_or_none()


def get_agent_by_id(db: Session, agent_id: int) -> Optional[models.Agent]:
    stmt = select(models.Agent).where(models.Agent.id == agent_id)
    return db.execute(stmt).scalar_one_or_none()


def get_agent_by_api_key(db: Session, api_key: str) -> Optional[models.Agent]:
    stmt = select(models.Agent).where(models.Agent.api_key == api_key)
    return db.execute(stmt).scalar_one_or_none()


def list_agents(db: Session) -> List[models.Agent]:
    stmt = select(models.Agent).order_by(models.Agent.id)
    return list(db.scalars(stmt))


def create_agent(db: Session, agent: models.Agent) -> models.Agent:
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent


def update_agent(db: Session, agent: models.Agent) -> models.Agent:
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent


def list_alerts(db: Session) -> List[models.Alert]:
    stmt = select(models.Alert).order_by(models.Alert.created_at.desc())
    return list(db.scalars(stmt))


def get_alert(db: Session, alert_id: int) -> Optional[models.Alert]:
    stmt = select(models.Alert).where(models.Alert.id == alert_id)
    return db.execute(stmt).scalar_one_or_none()


def create_alert(db: Session, alert: models.Alert) -> models.Alert:
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


def update_alert(db: Session, alert: models.Alert) -> models.Alert:
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


def delete_alert(db: Session, alert: models.Alert) -> None:
    db.delete(alert)
    db.commit()


def list_workplans(
    db: Session,
    context_type: Optional[str] = None,
    context_id: Optional[int] = None,
) -> List[models.Workplan]:
    stmt = select(models.Workplan).order_by(models.Workplan.updated_at.desc())
    if context_type:
        stmt = stmt.where(models.Workplan.context_type == context_type)
    if context_id is not None:
        stmt = stmt.where(models.Workplan.context_id == context_id)
    return list(db.scalars(stmt))


def get_workplan_by_alert_id(db: Session, alert_id: int) -> Optional[models.Workplan]:
    stmt = select(models.Workplan).where(
        models.Workplan.context_type == "alert",
        models.Workplan.context_id == alert_id,
    )
    return db.execute(stmt).scalar_one_or_none()


def create_workplan(db: Session, workplan: models.Workplan) -> models.Workplan:
    db.add(workplan)
    db.commit()
    db.refresh(workplan)
    return workplan


def update_workplan(db: Session, workplan: models.Workplan) -> models.Workplan:
    db.add(workplan)
    db.commit()
    db.refresh(workplan)
    return workplan


def list_handovers(
    db: Session,
    analyst_user_id: Optional[int] = None,
    created_by: Optional[int] = None,
) -> List[models.Handover]:
    stmt = select(models.Handover).order_by(models.Handover.created_at.desc())
    if analyst_user_id is not None:
        stmt = stmt.where(models.Handover.analyst_user_id == analyst_user_id)
    if created_by is not None:
        stmt = stmt.where(models.Handover.created_by == created_by)
    return list(db.scalars(stmt))


def create_handover(db: Session, handover: models.Handover) -> models.Handover:
    db.add(handover)
    db.commit()
    db.refresh(handover)
    return handover


def get_handover(db: Session, handover_id: int) -> Optional[models.Handover]:
    stmt = select(models.Handover).where(models.Handover.id == handover_id)
    return db.execute(stmt).scalar_one_or_none()


def update_handover(db: Session, handover: models.Handover) -> models.Handover:
    db.add(handover)
    db.commit()
    db.refresh(handover)
    return handover


def list_workplan_items(db: Session, workplan_id: int) -> List[models.WorkplanItem]:
    stmt = (
        select(models.WorkplanItem)
        .where(models.WorkplanItem.workplan_id == workplan_id)
        .order_by(models.WorkplanItem.order_index.asc(), models.WorkplanItem.id.asc())
    )
    return list(db.scalars(stmt))


def create_workplan_item(
    db: Session, item: models.WorkplanItem
) -> models.WorkplanItem:
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_workplan_item(
    db: Session, item: models.WorkplanItem
) -> models.WorkplanItem:
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def delete_workplan_item(db: Session, item: models.WorkplanItem) -> None:
    db.delete(item)
    db.commit()


def get_workplan_flow(
    db: Session, workplan_id: int
) -> Optional[models.WorkplanFlow]:
    stmt = select(models.WorkplanFlow).where(
        models.WorkplanFlow.workplan_id == workplan_id
    )
    return db.execute(stmt).scalar_one_or_none()


def upsert_workplan_flow(
    db: Session, flow: models.WorkplanFlow
) -> models.WorkplanFlow:
    db.add(flow)
    db.commit()
    db.refresh(flow)
    return flow


def create_notification_event(
    db: Session, event: models.NotificationEvent
) -> models.NotificationEvent:
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def upsert_analytic_rule(
    db: Session, rule: models.AnalyticRule
) -> models.AnalyticRule:
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def upsert_correlation_rule(
    db: Session, rule: models.CorrelationRule
) -> models.CorrelationRule:
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def get_analytic_rule(db: Session, rule_id: int) -> Optional[models.AnalyticRule]:
    stmt = select(models.AnalyticRule).where(models.AnalyticRule.id == rule_id)
    return db.execute(stmt).scalar_one_or_none()


def get_correlation_rule(
    db: Session, rule_id: int
) -> Optional[models.CorrelationRule]:
    stmt = select(models.CorrelationRule).where(models.CorrelationRule.id == rule_id)
    return db.execute(stmt).scalar_one_or_none()


def list_analytic_rules(
    db: Session,
    search: Optional[str] = None,
    severity: Optional[str] = None,
    enabled: Optional[bool] = None,
) -> List[models.AnalyticRule]:
    stmt = select(models.AnalyticRule).order_by(models.AnalyticRule.created_at.desc())
    if search:
        stmt = stmt.where(models.AnalyticRule.title.ilike(f"%{search}%"))
    if severity:
        stmt = stmt.where(models.AnalyticRule.severity == severity)
    if enabled is not None:
        stmt = stmt.where(models.AnalyticRule.enabled == enabled)
    return list(db.scalars(stmt))


def list_correlation_rules(
    db: Session,
    search: Optional[str] = None,
    severity: Optional[str] = None,
    enabled: Optional[bool] = None,
) -> List[models.CorrelationRule]:
    stmt = select(models.CorrelationRule).order_by(
        models.CorrelationRule.created_at.desc()
    )
    if search:
        stmt = stmt.where(models.CorrelationRule.title.ilike(f"%{search}%"))
    if severity:
        stmt = stmt.where(models.CorrelationRule.severity == severity)
    if enabled is not None:
        stmt = stmt.where(models.CorrelationRule.enabled == enabled)
    return list(db.scalars(stmt))


def list_workgroups(db: Session) -> List[models.WorkGroup]:
    stmt = select(models.WorkGroup).order_by(models.WorkGroup.created_at.desc())
    return list(db.scalars(stmt))


def create_workgroup(db: Session, workgroup: models.WorkGroup) -> models.WorkGroup:
    db.add(workgroup)
    db.commit()
    db.refresh(workgroup)
    return workgroup


def list_alert_escalations(db: Session, alert_id: Optional[int] = None) -> List[models.AlertEscalation]:
    stmt = select(models.AlertEscalation).order_by(models.AlertEscalation.created_at.desc())
    if alert_id is not None:
        stmt = stmt.where(models.AlertEscalation.alert_id == alert_id)
    return list(db.scalars(stmt))


def create_alert_escalation(db: Session, escalation: models.AlertEscalation) -> models.AlertEscalation:
    db.add(escalation)
    db.commit()
    db.refresh(escalation)
    return escalation


def list_action_logs(db: Session) -> List[models.ActionLog]:
    stmt = select(models.ActionLog).order_by(models.ActionLog.created_at.desc())
    return list(db.scalars(stmt))


def create_action_log(db: Session, log: models.ActionLog) -> models.ActionLog:
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def list_warroom_notes(db: Session, alert_id: Optional[int] = None) -> List[models.WarRoomNote]:
    stmt = select(models.WarRoomNote).order_by(models.WarRoomNote.created_at.desc())
    if alert_id:
        stmt = stmt.where(models.WarRoomNote.alert_id == alert_id)
    return list(db.scalars(stmt))


def create_warroom_note(db: Session, note: models.WarRoomNote) -> models.WarRoomNote:
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


def list_sandbox_results(db: Session) -> List[models.SandboxResult]:
    stmt = select(models.SandboxResult).order_by(models.SandboxResult.created_at.desc())
    return list(db.scalars(stmt))


def create_sandbox_result(
    db: Session, result: models.SandboxResult
) -> models.SandboxResult:
    db.add(result)
    db.commit()
    db.refresh(result)
    return result


def list_indicators(db: Session) -> List[models.Indicator]:
    stmt = select(models.Indicator).order_by(models.Indicator.updated_at.desc())
    return list(db.scalars(stmt))


def create_indicator(db: Session, indicator: models.Indicator) -> models.Indicator:
    db.add(indicator)
    db.commit()
    db.refresh(indicator)
    return indicator


def update_indicator(db: Session, indicator: models.Indicator) -> models.Indicator:
    db.add(indicator)
    db.commit()
    db.refresh(indicator)
    return indicator


def list_bioc_rules(db: Session) -> List[models.BiocRule]:
    stmt = select(models.BiocRule).order_by(models.BiocRule.updated_at.desc())
    return list(db.scalars(stmt))


def create_bioc_rule(db: Session, rule: models.BiocRule) -> models.BiocRule:
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def update_bioc_rule(db: Session, rule: models.BiocRule) -> models.BiocRule:
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def list_analytics_rules(db: Session) -> List[models.AnalyticsRule]:
    stmt = select(models.AnalyticsRule).order_by(models.AnalyticsRule.updated_at.desc())
    return list(db.scalars(stmt))


def create_analytics_rule(
    db: Session, rule: models.AnalyticsRule
) -> models.AnalyticsRule:
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def update_analytics_rule(db: Session, rule: models.AnalyticsRule) -> models.AnalyticsRule:
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def list_endpoints(db: Session) -> List[models.Endpoint]:
    stmt = select(models.Endpoint).order_by(models.Endpoint.display_name.asc())
    return list(db.scalars(stmt))


def get_endpoint(db: Session, endpoint_id: int) -> Optional[models.Endpoint]:
    stmt = select(models.Endpoint).where(models.Endpoint.id == endpoint_id)
    return db.execute(stmt).scalar_one_or_none()


def get_endpoint_by_hostname(db: Session, hostname: str) -> Optional[models.Endpoint]:
    stmt = select(models.Endpoint).where(
        (models.Endpoint.hostname.ilike(hostname))
        | (models.Endpoint.display_name.ilike(hostname))
    )
    return db.execute(stmt).scalar_one_or_none()


def create_endpoint(db: Session, endpoint: models.Endpoint) -> models.Endpoint:
    db.add(endpoint)
    db.commit()
    db.refresh(endpoint)
    return endpoint


def update_endpoint(db: Session, endpoint: models.Endpoint) -> models.Endpoint:
    db.add(endpoint)
    db.commit()
    db.refresh(endpoint)
    return endpoint


def list_endpoint_actions(db: Session, endpoint_id: int) -> List[models.EndpointAction]:
    stmt = (
        select(models.EndpointAction)
        .where(models.EndpointAction.endpoint_id == endpoint_id)
        .order_by(models.EndpointAction.requested_at.desc())
    )
    return list(db.scalars(stmt))


def get_endpoint_action(db: Session, action_id: int) -> Optional[models.EndpointAction]:
    stmt = select(models.EndpointAction).where(models.EndpointAction.id == action_id)
    return db.execute(stmt).scalar_one_or_none()


def create_endpoint_action(db: Session, action: models.EndpointAction) -> models.EndpointAction:
    db.add(action)
    db.commit()
    db.refresh(action)
    return action


def update_endpoint_action(db: Session, action: models.EndpointAction) -> models.EndpointAction:
    db.add(action)
    db.commit()
    db.refresh(action)
    return action


def list_events(db: Session) -> List[models.Event]:
    stmt = select(models.Event).order_by(models.Event.created_at.desc())
    return list(db.scalars(stmt))


def create_event(db: Session, event: models.Event) -> models.Event:
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def list_detection_rules(db: Session) -> List[models.DetectionRule]:
    stmt = select(models.DetectionRule).order_by(models.DetectionRule.created_at.desc())
    return list(db.scalars(stmt))


def create_detection_rule(
    db: Session, rule: models.DetectionRule
) -> models.DetectionRule:
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def list_network_events(db: Session) -> List[models.NetworkEvent]:
    stmt = select(models.NetworkEvent).order_by(models.NetworkEvent.created_at.desc())
    return list(db.scalars(stmt))


def create_network_event(db: Session, event: models.NetworkEvent) -> models.NetworkEvent:
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def get_network_sensor_by_name(
    db: Session, name: str
) -> Optional[models.NetworkSensor]:
    stmt = select(models.NetworkSensor).where(models.NetworkSensor.name == name)
    return db.execute(stmt).scalar_one_or_none()


def list_network_sensors(db: Session) -> List[models.NetworkSensor]:
    stmt = select(models.NetworkSensor).order_by(models.NetworkSensor.name.asc())
    return list(db.scalars(stmt))


def create_network_sensor(
    db: Session, sensor: models.NetworkSensor
) -> models.NetworkSensor:
    db.add(sensor)
    db.commit()
    db.refresh(sensor)
    return sensor


def update_network_sensor(
    db: Session, sensor: models.NetworkSensor
) -> models.NetworkSensor:
    db.add(sensor)
    db.commit()
    db.refresh(sensor)
    return sensor


def create_network_ingest_errors(
    db: Session, errors: List[models.NetworkIngestError]
) -> List[models.NetworkIngestError]:
    db.add_all(errors)
    db.commit()
    return errors


def list_incidents(db: Session) -> List[models.Incident]:
    stmt = select(models.Incident).order_by(models.Incident.updated_at.desc())
    return list(db.scalars(stmt))


def get_incident(db: Session, incident_id: int) -> Optional[models.Incident]:
    stmt = select(models.Incident).where(models.Incident.id == incident_id)
    return db.execute(stmt).scalar_one_or_none()


def create_incident(db: Session, incident: models.Incident) -> models.Incident:
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident


def update_incident(db: Session, incident: models.Incident) -> models.Incident:
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident


def list_incident_items(db: Session, incident_id: int) -> List[models.IncidentItem]:
    stmt = (
        select(models.IncidentItem)
        .where(models.IncidentItem.incident_id == incident_id)
        .order_by(models.IncidentItem.created_at.asc(), models.IncidentItem.id.asc())
    )
    return list(db.scalars(stmt))


def create_incident_item(
    db: Session, item: models.IncidentItem
) -> models.IncidentItem:
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def create_response_action(
    db: Session, action: models.ResponseAction
) -> models.ResponseAction:
    db.add(action)
    db.commit()
    db.refresh(action)
    return action


def list_response_actions(db: Session) -> List[models.ResponseAction]:
    stmt = select(models.ResponseAction).order_by(models.ResponseAction.created_at.desc())
    return list(db.scalars(stmt))


def get_response_action(
    db: Session, action_id: int
) -> Optional[models.ResponseAction]:
    stmt = select(models.ResponseAction).where(models.ResponseAction.id == action_id)
    return db.execute(stmt).scalar_one_or_none()


def update_response_action(
    db: Session, action: models.ResponseAction
) -> models.ResponseAction:
    db.add(action)
    db.commit()
    db.refresh(action)
    return action


def create_inventory_snapshot(db: Session, snapshot: models.InventorySnapshot) -> models.InventorySnapshot:
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


def list_inventory_snapshots(
    db: Session,
    agent_id: int,
    category: Optional[str] = None,
    limit: Optional[int] = None,
) -> List[models.InventorySnapshot]:
    stmt = (
        select(models.InventorySnapshot)
        .where(models.InventorySnapshot.agent_id == agent_id)
        .order_by(models.InventorySnapshot.collected_at.desc())
    )
    if category:
        stmt = stmt.where(models.InventorySnapshot.category == category)
    if limit:
        stmt = stmt.limit(limit)
    return list(db.scalars(stmt))


def list_vulnerability_definitions(db: Session) -> List[models.VulnerabilityDefinition]:
    stmt = select(models.VulnerabilityDefinition).order_by(
        models.VulnerabilityDefinition.updated_at.desc()
    )
    return list(db.scalars(stmt))


def get_vulnerability_definition_by_cve(
    db: Session, cve_id: str
) -> Optional[models.VulnerabilityDefinition]:
    stmt = select(models.VulnerabilityDefinition).where(
        models.VulnerabilityDefinition.cve_id == cve_id
    )
    return db.execute(stmt).scalar_one_or_none()


def create_vulnerability_definition(
    db: Session, definition: models.VulnerabilityDefinition
) -> models.VulnerabilityDefinition:
    db.add(definition)
    db.commit()
    db.refresh(definition)
    return definition


def get_agent_vulnerability(
    db: Session,
    agent_id: int,
    definition_id: int,
) -> Optional[models.AgentVulnerability]:
    stmt = select(models.AgentVulnerability).where(
        models.AgentVulnerability.agent_id == agent_id,
        models.AgentVulnerability.definition_id == definition_id,
    )
    return db.execute(stmt).scalar_one_or_none()


def create_or_update_agent_vulnerability(
    db: Session,
    vulnerability: models.AgentVulnerability,
) -> models.AgentVulnerability:
    db.add(vulnerability)
    db.commit()
    db.refresh(vulnerability)
    return vulnerability


def list_agent_vulnerabilities(
    db: Session, agent_id: int
) -> List[models.AgentVulnerability]:
    stmt = (
        select(models.AgentVulnerability)
        .where(models.AgentVulnerability.agent_id == agent_id)
        .order_by(models.AgentVulnerability.detected_at.desc())
    )
    return list(db.scalars(stmt))


def create_sca_result(db: Session, result: models.SCAResult) -> models.SCAResult:
    db.add(result)
    db.commit()
    db.refresh(result)
    return result


def list_sca_results(db: Session, agent_id: int) -> List[models.SCAResult]:
    stmt = (
        select(models.SCAResult)
        .where(models.SCAResult.agent_id == agent_id)
        .order_by(models.SCAResult.collected_at.desc())
    )
    return list(db.scalars(stmt))
