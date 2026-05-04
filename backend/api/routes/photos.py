"""Photo management routes — upload a photo for a registered turtle."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status

from agents.profile_management_agent import AddPhotoAction, ProfileManagementAgent
from core.dependencies import profile_agent
from models.schemas import PhotoRead

router = APIRouter(prefix="/turtles/{turtle_id}/photos", tags=["photos"])

_MAX_BYTES = 20 * 1024 * 1024


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
