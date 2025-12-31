from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, models, schemas
from ..auth import get_current_admin_user, get_current_user
from ..database import get_db

router = APIRouter(prefix="/vulnerabilities", tags=["vulnerabilities"])


@router.get("/definitions", response_model=List[schemas.VulnerabilityDefinition])
def list_definitions(
    db: Session = Depends(get_db),
    current_user: schemas.UserProfile = Depends(get_current_user),
) -> List[schemas.VulnerabilityDefinition]:
    definitions = crud.list_vulnerability_definitions(db)
    return [
        schemas.VulnerabilityDefinition.model_validate(item) for item in definitions
    ]


@router.post("/definitions", response_model=schemas.VulnerabilityDefinition)
def create_definition(
    payload: schemas.VulnerabilityDefinitionCreate,
    db: Session = Depends(get_db),
    current_user: schemas.UserProfile = Depends(get_current_admin_user),
) -> schemas.VulnerabilityDefinition:
    if crud.get_vulnerability_definition_by_cve(db, payload.cve_id):
        raise HTTPException(status_code=400, detail="CVE already exists")
    definition = models.VulnerabilityDefinition(
        cve_id=payload.cve_id,
        title=payload.title,
        description=payload.description,
        severity=payload.severity,
        affected_products=payload.affected_products,
    )
    created = crud.create_vulnerability_definition(db, definition)
    return schemas.VulnerabilityDefinition.model_validate(created)


@router.get("/agents/{agent_id}", response_model=List[schemas.AgentVulnerability])
def list_agent_vulnerabilities(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.UserProfile = Depends(get_current_user),
) -> List[schemas.AgentVulnerability]:
    if not crud.get_agent_by_id(db, agent_id):
        raise HTTPException(status_code=404, detail="Agent not found")
    vulns = crud.list_agent_vulnerabilities(db, agent_id)
    return [schemas.AgentVulnerability.model_validate(item) for item in vulns]


@router.post(
    "/agents/{agent_id}/evaluate", response_model=List[schemas.AgentVulnerability]
)
def evaluate_agent_vulnerabilities(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.UserProfile = Depends(get_current_user),
) -> List[schemas.AgentVulnerability]:
    agent = crud.get_agent_by_id(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    software_snapshots = crud.list_inventory_snapshots(
        db, agent_id=agent_id, category="software"
    )
    definitions = crud.list_vulnerability_definitions(db)

    matches: List[schemas.AgentVulnerability] = []
    for definition in definitions:
        affected = definition.affected_products or []
        for snapshot in software_snapshots:
            name = snapshot.data.get("name", "").lower()
            version = str(snapshot.data.get("version", "")).lower()
            if not name:
                continue
            for product in affected:
                product_name = str(product.get("name", "")).lower()
                product_version = str(product.get("version", "")).lower()
                if product_name and product_name != name:
                    continue
                if product_version and product_version not in ("*", version):
                    continue

                existing = crud.get_agent_vulnerability(db, agent_id, definition.id)
                if existing:
                    matches.append(schemas.AgentVulnerability.model_validate(existing))
                    break

                evidence = {
                    "software": snapshot.data,
                    "matched_product": product,
                }
                vuln = models.AgentVulnerability(
                    agent_id=agent_id,
                    definition_id=definition.id,
                    status="open",
                    evidence=evidence,
                )
                created = crud.create_or_update_agent_vulnerability(db, vuln)
                matches.append(schemas.AgentVulnerability.model_validate(created))
                break

    return matches
