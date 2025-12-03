from datetime import datetime
from typing import List, Dict
import pandas as pd


def normalize_timestamp(ts: str) -> datetime:
    return pd.to_datetime(ts, errors="coerce")


def assign_phase(index: int, total: int) -> str:
    if total == 0:
        return "unknown"
    ratio = index / total
    if ratio < 0.2:
        return "detection"
    elif ratio < 0.8:
        return "mitigation"
    else:
        return "resolution"


def classify_event(message: str, source: str, level: str) -> str:
    m = message.lower()
    if "alert" in m or level == "critical":
        return "alert"
    if "warning" in m:
        return "warning"
    if "error" in m or level == "error":
        return "error"
    if "customer" in m:
        return "customer"
    if "restart" in m or "scal" in m:
        return "infra"
    return source.lower() if source else "unknown"


def build_timeline_from_dataframe(df: pd.DataFrame, source_name: str) -> List[Dict]:
    required_columns = {"timestamp", "message"}
    if not required_columns.issubset(df.columns):
        raise ValueError("CSV must contain at least timestamp and message fields.")

    df["timestamp"] = df["timestamp"].apply(normalize_timestamp)
    df = df.dropna(subset=["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)

    events = []
    total = len(df)

    for idx, row in df.iterrows():
        event = {
            "time": row["timestamp"].isoformat(),
            "message": row["message"],
            "event_type": classify_event(
                row.get("message", ""),
                row.get("source", ""),
                row.get("level", "")
            ),
            "phase": assign_phase(idx, total),
            "source": row.get("source", source_name),
            "level": row.get("level", ""),
        }
        events.append(event)

    return events