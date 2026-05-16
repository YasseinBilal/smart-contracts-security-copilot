import json

from fastapi import APIRouter, Depends
from sqlalchemy import select, func, Integer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.scan import Scan
from app.models.finding import Finding

router = APIRouter()


@router.get("/eval")
async def get_eval_metrics(db: AsyncSession = Depends(get_db)):
    # Total scans and average severity counts
    scans_result = await db.execute(
        select(
            func.count(Scan.id).label("total_scans"),
            func.avg(Scan.critical_count).label("avg_critical"),
            func.avg(Scan.high_count).label("avg_high"),
            func.avg(Scan.medium_count).label("avg_medium"),
            func.avg(Scan.total_tokens).label("avg_tokens"),
        ).where(Scan.status == "completed")
    )
    scan_stats = scans_result.one()

    # False positive rate
    fp_result = await db.execute(
        select(
            func.count(Finding.id).label("total"),
            func.sum(Finding.false_positive.cast(Integer)).label("fp_count"),
        )
    )
    fp_stats = fp_result.one()

    total = fp_stats.total or 1
    fp_rate = round((fp_stats.fp_count or 0) / total * 100, 1)

    # Average latencies per node (from node_latencies JSON field)
    latencies_result = await db.execute(
        select(Scan.node_latencies).where(
            Scan.status == "completed",
            Scan.node_latencies.isnot(None),
        ).limit(50)
    )
    latency_rows = latencies_result.scalars().all()

    avg_latencies: dict[str, float] = {}
    if latency_rows:
        node_sums: dict[str, list[float]] = {}
        for row in latency_rows:
            try:
                parsed = json.loads(row)
                for node, lat in parsed.items():
                    node_sums.setdefault(node, []).append(float(lat))
            except (json.JSONDecodeError, TypeError):
                pass
        avg_latencies = {
            node: round(sum(vals) / len(vals), 3)
            for node, vals in node_sums.items()
        }

    return {
        "total_scans": scan_stats.total_scans or 0,
        "avg_findings_per_scan": {
            "critical": round(float(scan_stats.avg_critical or 0), 2),
            "high": round(float(scan_stats.avg_high or 0), 2),
            "medium": round(float(scan_stats.avg_medium or 0), 2),
        },
        "false_positive_rate_pct": fp_rate,
        "avg_tokens_per_scan": round(float(scan_stats.avg_tokens or 0)),
        "avg_node_latencies_sec": avg_latencies,
    }
