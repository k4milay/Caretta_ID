"""Fotoğraf yönetim rotaları — kaplumbağa fotoğrafı yükleme ve listeleme."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, UploadFile, status

from agents.profile_management_agent import AddPhotoAction, ProfileManagementAgent
from core.dependencies import photo_repo, profile_agent
from repositories.photo_repository import PhotoRepository
from models.schemas import PhotoRead

router = APIRouter(prefix="/turtles/{turtle_id}/photos", tags=["photos"])

_MAX_BYTES = 20 * 1024 * 1024  # 20 MB dosya boyutu sınırı


@router.get(
    "",
    response_model=list[PhotoRead],
    summary="Kaplumbağa Fotoğraflarını Listele",
)
async def list_photos(
    turtle_id: UUID,
    repo: PhotoRepository = Depends(photo_repo),
) -> list[PhotoRead]:
    """Bir kaplumbağaya ait tüm fotoğrafları döndürür."""
    photos = await repo.list_by_turtle(turtle_id)
    return [PhotoRead.model_validate(p) for p in photos]


@router.post(
    "",
    response_model=PhotoRead,
    status_code=status.HTTP_201_CREATED,
    summary="Fotoğraf Yükle ve Gömme Vektörü Oluştur",
    description=(
        "Kaplumbağa profiline fotoğraf ekler. Yükleme tamamlandığında "
        "görüntü otomatik olarak ön işlemden geçirilir ve pgvector HNSW "
        "indeksindeki gömme vektörü güncellenir. Böylece yeni fotoğraf "
        "anında tanımlama araması kapsamına girer."
    ),
)
async def add_photo(
    turtle_id: UUID,
    file: UploadFile,
    region: str = Query(default="head"),
    agent: ProfileManagementAgent = Depends(profile_agent),
) -> PhotoRead:
    """Upload a photo, preprocess, embed, and attach to a turtle profile."""
    raw = await file.read()
    if len(raw) > _MAX_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 20 MB limit.")

    result = await agent.run(
        AddPhotoAction(turtle_id=turtle_id, image_bytes=raw, region=region)
    )
    if not result.ok:
        raise HTTPException(status_code=422, detail=result.error)

    return PhotoRead.model_validate(result.value.photo)


@router.delete(
    "/{photo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Fotoğraf Sil",
)
async def delete_photo(
    turtle_id: UUID,
    photo_id: UUID,
    repo: PhotoRepository = Depends(photo_repo),
) -> Response:
    """Bir kaplumbağaya ait fotoğrafı ve gömme vektörünü siler."""
    deleted = await repo.delete_by_id(photo_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Fotoğraf bulunamadı.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
