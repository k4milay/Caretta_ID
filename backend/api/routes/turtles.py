"""Turtle CRUD routes — used by ProfileManagementAgent and the frontend."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from core.dependencies import turtle_repo
from models.schemas import TurtleCreate, TurtleRead
from repositories.turtle_repository import TurtleRepository

router = APIRouter(prefix="/turtles", tags=["turtles"])


@router.post("", response_model=TurtleRead, status_code=status.HTTP_201_CREATED)
async def create_turtle(body: TurtleCreate, repo: TurtleRepository = Depends(turtle_repo)):
    return await repo.create(name=body.name, notes=body.notes)


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
