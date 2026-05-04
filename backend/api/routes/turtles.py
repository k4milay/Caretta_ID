"""Turtle CRUD routes — used by ProfileManagementAgent and the frontend."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from agents.profile_management_agent import (
    ProfileManagementAgent,
    RegisterTurtleAction,
    UpdateTurtleAction,
)
from core.dependencies import profile_agent, turtle_repo
from models.schemas import TurtleCreate, TurtleRead, TurtleUpdate
from repositories.turtle_repository import TurtleRepository

router = APIRouter(
    prefix="/turtles",
    tags=["turtles"],
    responses={404: {"description": "Kaplumbağa bulunamadı"}},
)


@router.post("", response_model=TurtleRead, status_code=status.HTTP_201_CREATED)
async def create_turtle(
    body: TurtleCreate,
    agent: ProfileManagementAgent = Depends(profile_agent),
) -> TurtleRead:
    result = await agent.run(RegisterTurtleAction(name=body.name, notes=body.notes))
    if not result.ok:
        raise HTTPException(status_code=422, detail=result.error)
    return TurtleRead.model_validate(result.value.turtle)


@router.patch("/{turtle_id}", response_model=TurtleRead)
async def update_turtle(
    turtle_id: UUID,
    body: TurtleUpdate,
    agent: ProfileManagementAgent = Depends(profile_agent),
) -> TurtleRead:
    result = await agent.run(
        UpdateTurtleAction(turtle_id=turtle_id, name=body.name, notes=body.notes)
    )
    if not result.ok:
        raise HTTPException(status_code=422, detail=result.error)
    return TurtleRead.model_validate(result.value.turtle)


@router.get("", response_model=list[TurtleRead])
async def list_turtles(
    limit: int = 100,
    offset: int = 0,
    repo: TurtleRepository = Depends(turtle_repo),
):
    return await repo.list_all(limit=limit, offset=offset)


@router.get("/{turtle_id}", response_model=TurtleRead)
async def get_turtle(turtle_id: UUID, repo: TurtleRepository = Depends(turtle_repo)):
    turtle = await repo.get_by_id(turtle_id)
    if not turtle:
        raise HTTPException(status_code=404, detail="Turtle not found.")
    return turtle


@router.delete("/{turtle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_turtle(turtle_id: UUID, repo: TurtleRepository = Depends(turtle_repo)):
    deleted = await repo.delete(turtle_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Turtle not found.")
