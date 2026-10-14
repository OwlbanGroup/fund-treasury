"""Entity CRUD endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.entity import Entity
from ..schemas import EntityCreate, EntityOut, EntityUpdate

router = APIRouter(prefix="/entities", tags=["entities"])


@router.get("", response_model=list[EntityOut])
def list_entities(db: Session = Depends(get_db)) -> list[Entity]:
    return list(db.scalars(select(Entity).order_by(Entity.code)))


@router.post("", response_model=EntityOut, status_code=status.HTTP_201_CREATED)
def create_entity(payload: EntityCreate, db: Session = Depends(get_db)) -> Entity:
    existing = db.scalar(select(Entity).where(Entity.code == payload.code))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Entity code '{payload.code}' already exists",
        )
    entity = Entity(**payload.model_dump())
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return entity


@router.get("/{entity_id}", response_model=EntityOut)
def get_entity(entity_id: int, db: Session = Depends(get_db)) -> Entity:
    entity = db.get(Entity, entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity


@router.patch("/{entity_id}", response_model=EntityOut)
def update_entity(
    entity_id: int, payload: EntityUpdate, db: Session = Depends(get_db)
) -> Entity:
    entity = db.get(Entity, entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(entity, field, value)
    db.commit()
    db.refresh(entity)
    return entity


@router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entity(entity_id: int, db: Session = Depends(get_db)) -> Response:
    entity = db.get(Entity, entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    db.delete(entity)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
