import json
import logging
from uuid import uuid4
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db import get_db
from app.models.scan import Scan
from app.schemas.scan import ScanResponse, StatisticsResponse
from app.services.extractor import extract_fields
from app.services.image_service import image_extension
from app.services.ocr_service import ocr_image
from app.services.report_service import create_report
from app.services.rules import evaluate, score_results

router = APIRouter()
logger = logging.getLogger(__name__)

def serialize(scan: Scan):
    return {
        "id": scan.id,
        "filename": scan.filename,
        "created_at": scan.created_at,
        "extracted_text": scan.extracted_text,
        "extracted": json.loads(scan.extracted_json or "{}"),
        "results": json.loads(scan.results_json or "[]"),
        "score": scan.score,
        "status": scan.status,
        "report_url": (
            f"/api/v1/reports/{scan.id}"
            if scan.report_path
            else None
        ),
    }

@router.post("/scan", response_model=ScanResponse)
async def scan(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    data = await file.read()
    if len(data) > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="Uploaded image exceeds the configured size limit.",
        )

    try:
        extension = image_extension(data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    original_name = (file.filename or f"product{extension}").replace("\\", "/")
    display_name = original_name.rsplit("/", maxsplit=1)[-1][:255]
    if not display_name:
        display_name = f"product{extension}"

    stored_name = f"{uuid4().hex}{extension}"
    upload_path = settings.upload_dir / stored_name
    upload_path.parent.mkdir(parents=True, exist_ok=True)
    upload_path.write_bytes(data)

    text, warnings = ocr_image(data)
    extracted = extract_fields(text)
    results = evaluate(extracted)

    for warning in warnings:
        results.append(
            {
                "code": "OCR-01",
                "name": "OCR quality",
                "status": "WARNING",
                "severity": "WARNING",
                "message": warning,
                "evidence": "",
                "weight": 0,
            }
        )

    score, status = score_results(results)
    
    record = Scan(
        filename=display_name,
        image_path=str(upload_path),
        extracted_text=text,
        extracted_json=json.dumps(extracted),
        results_json=json.dumps(results),
        score=score,
        status=status,
    )

    try:
        db.add(record)
        db.commit()
        db.refresh(record)
    except SQLAlchemyError as exc:
        db.rollback()
        upload_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=500,
            detail="Could not save the scan. Please try again.",
        ) from exc

    try:
        record.report_path = create_report(
            record.id,
            display_name,
            text,
            extracted,
            results,
            score,
            status,
        )
        db.commit()
        db.refresh(record)
    except Exception:
        logger.exception("Could not create report for scan %s", record.id)
        db.rollback()
        db.refresh(record)

    return serialize(record)

@router.post("/analyze", response_model=ScanResponse)
async def analyze(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    return await scan(file, db)

@router.get("/scans")
def scans(
    limit: int = 20,
    db: Session = Depends(get_db),
):
    limit = max(1, min(limit, 100))
    records = (
        db.query(Scan)
        .order_by(Scan.created_at.desc())
        .limit(limit)
        .all()
    )
    return [serialize(record) for record in records]

@router.get("/scans/{scan_id}")
def scan_detail(
    scan_id: int,
    db: Session = Depends(get_db),
):
    record = db.get(Scan, scan_id)
    if not record:
        raise HTTPException(
            status_code=404,
            detail="Scan not found",
        )
    return serialize(record)

@router.get("/reports/{scan_id}")
def report(
    scan_id: int,
    db: Session = Depends(get_db),
):
    record = db.get(Scan, scan_id)
    if not record or not record.report_path:
        raise HTTPException(
            status_code=404,
            detail="Report not found",
        )
        
    report_path = settings.project_path(record.report_path).resolve()
    try:
        report_path.relative_to(settings.report_dir.resolve())
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Report not found") from exc
        
    if not report_path.is_file():
        raise HTTPException(status_code=404, detail="Report not found")
        
    return FileResponse(
        report_path,
        media_type="application/pdf",
        filename=f"packsure_report_{scan_id}.pdf",
    )

@router.get("/statistics", response_model=StatisticsResponse)
def statistics(db: Session = Depends(get_db)):
    records = db.query(Scan).all()
    total = len(records)
    return {
        "total_scans": total,
        "compliant": sum(record.status == "PASS" for record in records),
        "failed": sum(record.status == "FAIL" for record in records),
        "needs_review": sum(record.status == "NEEDS REVIEW" for record in records),
        "average_score": round(
            sum(record.score for record in records) / total,
            1,
        ) if total else 0,
    }