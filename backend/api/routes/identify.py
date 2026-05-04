from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status

from agents.orchestrator_agent import IdentifyInput, OrchestratorAgent
from core.config import get_settings
from core.dependencies import orchestrator
from models.schemas import IdentificationResponse

router = APIRouter(prefix="/identify", tags=["identification"])

_MAX_UPLOAD_BYTES = 20 * 1024 * 1024


@router.post(
    "",
    response_model=IdentificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Kaplumbağayı Tanımla",
    description=(
        "Bir kaplumbağa fotoğrafı yükleyin. Sistem baş bölgesini segmente eder, "
        "512 boyutlu bir gömme vektörü oluşturur ve pgvector HNSW indeksinde "
        "kosinüs benzerliği araması yapar. Eşik altındaki sonuçlar filtrelenir."
    ),
)
async def identify_turtle(
    file: UploadFile,
    region: str = Query(default="head", description="Anatomical region: 'head' or 'carapace'"),
    top_k: int = Query(default=5, ge=1, le=20),
    threshold: float = Query(default=None),
    agent: OrchestratorAgent = Depends(orchestrator),
) -> IdentificationResponse:
    """Upload a turtle photo and receive ranked identity matches."""
    raw = await file.read()
    if len(raw) > _MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 20 MB limit.")

    effective_threshold = threshold if threshold is not None else get_settings().similarity_threshold

    result = await agent.run(
        IdentifyInput(
            image_bytes=raw,
            region=region,
            top_k=top_k,
            threshold=effective_threshold,
        )
    )

    if not result.ok:
        raise HTTPException(status_code=422, detail=result.error)

    return result.value
