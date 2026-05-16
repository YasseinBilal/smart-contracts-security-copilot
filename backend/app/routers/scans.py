from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.scan import Scan
from app.schemas.scan import ScanSummary, ScanDetail

router = APIRouter()


@router.get("/scans", response_model=list[ScanSummary])
async def list_scans(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Scan).order_by(Scan.created_at.desc()).limit(50)
    )
    return result.scalars().all()


@router.get("/scans/{scan_id}", response_model=ScanDetail)
async def get_scan(scan_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Scan)
        .options(selectinload(Scan.findings))
        .where(Scan.id == scan_id)
    )
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan
