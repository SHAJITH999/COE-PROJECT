"""
SQLite Database Helper for Human Approval Workflow.

Manages recommendation approvals, rejections, and override audit trail.
"""

import sqlite3
import json
from datetime import datetime, UTC
from pathlib import Path
from typing import Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = PROJECT_ROOT / "outputs" / "approvals.db"

# Configurable high-impact thresholds
HIGH_IMPACT_CONFIG = {
    "critical_urgency": ["Critical"],
    "high_urgency": ["High"],
    "min_quantity_threshold": 20,
    "min_cost_threshold": 50000.0,
}


def init_db(db_path: Optional[Path] = None) -> None:
    """Initialize the SQLite database and approvals table if not already existing."""
    path = db_path or DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS approvals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recommendation_id TEXT NOT NULL UNIQUE,
            status TEXT NOT NULL DEFAULT 'PENDING',
            original_recommendation TEXT,
            override_reason TEXT,
            timestamp TEXT,
            is_high_impact INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


def is_high_impact(rec: Dict) -> bool:
    """
    Determine if a recommendation is high-impact based on configurable thresholds.
    """
    urgency = str(rec.get("Service_Urgency", ""))
    quantity = float(rec.get("Recommended_Quantity", 0))
    cost = float(rec.get("Estimated_Cost", 0))

    if urgency in HIGH_IMPACT_CONFIG["critical_urgency"]:
        return True
    if quantity >= HIGH_IMPACT_CONFIG["min_quantity_threshold"]:
        return True
    if cost >= HIGH_IMPACT_CONFIG["min_cost_threshold"]:
        return True
    return False


def seed_recommendations(recs: List[Dict], db_path: Optional[Path] = None) -> None:
    """Insert recommendation IDs into the DB with PENDING status if not already present."""
    path = db_path or DB_PATH
    init_db(path)
    conn = sqlite3.connect(str(path))
    cursor = conn.cursor()
    for rec in recs:
        rec_id = str(rec.get("Recommendation_ID", ""))
        if not rec_id:
            continue
        high = 1 if is_high_impact(rec) else 0
        cursor.execute("""
            INSERT OR IGNORE INTO approvals
            (recommendation_id, status, original_recommendation, timestamp, is_high_impact)
            VALUES (?, 'PENDING', ?, ?, ?)
        """, (rec_id, json.dumps(rec), datetime.now(UTC).isoformat(), high))
    conn.commit()
    conn.close()


def record_decision(
    recommendation_id: str,
    decision: str,
    override_reason: Optional[str] = None,
    db_path: Optional[Path] = None
) -> bool:
    """
    Record an APPROVED, REJECTED, or OVERRIDDEN decision for a recommendation.
    Returns True if the recommendation was found and updated.
    """
    path = db_path or DB_PATH
    conn = sqlite3.connect(str(path))
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM approvals WHERE recommendation_id = ?", (recommendation_id,)
    )
    row = cursor.fetchone()
    if row is None:
        conn.close()
        return False

    cursor.execute("""
        UPDATE approvals
        SET status = ?, override_reason = ?, timestamp = ?
        WHERE recommendation_id = ?
    """, (decision, override_reason, datetime.now(UTC).isoformat(), recommendation_id))
    conn.commit()
    conn.close()
    return True


def get_approval_status(recommendation_id: str, db_path: Optional[Path] = None) -> Optional[Dict]:
    """Return status record for a recommendation ID, or None if not found."""
    path = db_path or DB_PATH
    if not path.exists():
        return None
    conn = sqlite3.connect(str(path))
    cursor = conn.cursor()
    cursor.execute(
        "SELECT recommendation_id, status, override_reason, timestamp, is_high_impact "
        "FROM approvals WHERE recommendation_id = ?", (recommendation_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if row is None:
        return None
    return {
        "recommendation_id": row[0],
        "status": row[1],
        "override_reason": row[2],
        "timestamp": row[3],
        "is_high_impact": bool(row[4]),
    }


def get_all_approvals(db_path: Optional[Path] = None) -> List[Dict]:
    """Return all approval records from the database."""
    path = db_path or DB_PATH
    if not path.exists():
        return []
    conn = sqlite3.connect(str(path))
    cursor = conn.cursor()
    cursor.execute(
        "SELECT recommendation_id, status, override_reason, timestamp, is_high_impact "
        "FROM approvals ORDER BY id"
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "recommendation_id": r[0],
            "status": r[1],
            "override_reason": r[2],
            "timestamp": r[3],
            "is_high_impact": bool(r[4]),
        }
        for r in rows
    ]
