from __future__ import annotations

import math
from collections import Counter
from statistics import mean, variance
from typing import Any, Dict, List, Tuple, Optional


def _to_float(val: Any) -> Optional[float]:
    if val is None:
        return None
    try:
        if isinstance(val, (int, float)):
            return float(val)
        s = str(val).strip().replace(",", "")
        if s == "" or s.lower() in {"nan", "none", "null"}:
            return None
        return float(s)
    except Exception:
        return None


def analyze_text(text: str) -> Dict[str, Any]:
    words = [w for w in text.split() if w.strip()]
    lines = text.splitlines()
    sample = " ".join(words[:50])
    return {
        "char_count": len(text),
        "word_count": len(words),
        "line_count": len(lines),
        "sample": sample,
    }


def analyze_table(rows: List[List[Any]], columns: List[str]) -> Dict[str, Any]:
    col_stats: Dict[str, Any] = {}
    numeric_cols: List[str] = []
    non_numeric_cols: List[str] = []

    # Transpose with ragged rows handling
    for idx, col in enumerate(columns):
        values = [row[idx] if idx < len(row) else None for row in rows]
        nums = [x for x in (_to_float(v) for v in values) if x is not None]
        non_null = [v for v in values if v not in (None, "")]
        col_info: Dict[str, Any] = {
            "non_null_count": len(non_null),
            "unique_count": len(set(non_null)),
        }
        if len(nums) >= 2:
            numeric_cols.append(col)
            col_info.update(
                {
                    "min": min(nums),
                    "max": max(nums),
                    "sum": sum(nums),
                    "mean": mean(nums),
                    "variance": variance(nums) if len(nums) > 1 else 0.0,
                }
            )
        else:
            non_numeric_cols.append(col)
            # Top 5 frequent values
            top = Counter(non_null).most_common(5)
            col_info["top_values"] = [[str(k), int(v)] for k, v in top]
        col_stats[col] = col_info

    # Simple correlations for numeric columns (Pearson)
    correlations: Dict[str, Dict[str, float]] = {}
    def pearson(xs: List[float], ys: List[float]) -> Optional[float]:
        if len(xs) < 2 or len(ys) < 2 or len(xs) != len(ys):
            return None
        mx, my = mean(xs), mean(ys)
        num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        denx = math.sqrt(sum((x - mx) ** 2 for x in xs))
        deny = math.sqrt(sum((y - my) ** 2 for y in ys))
        if denx == 0 or deny == 0:
            return None
        return num / (denx * deny)

    # Build aligned numeric vectors per pair
    for i, c1 in enumerate(numeric_cols):
        correlations[c1] = {}
        idx1 = columns.index(c1)
        v1_all = [_to_float(row[idx1]) if idx1 < len(row) else None for row in rows]
        for c2 in numeric_cols[i + 1 :]:
            idx2 = columns.index(c2)
            v2_all = [_to_float(row[idx2]) if idx2 < len(row) else None for row in rows]
            paired = [(x, y) for x, y in zip(v1_all, v2_all) if x is not None and y is not None]
            xs = [x for x, _ in paired]
            ys = [y for _, y in paired]
            r = pearson(xs, ys)
            if r is not None:
                correlations[c1][c2] = r

    summary_text_lines: List[str] = [
        f"Rows analyzed: {len(rows)}; Columns: {len(columns)}",
        f"Numeric columns: {', '.join(numeric_cols) if numeric_cols else 'None'}",
        f"Categorical columns: {', '.join(non_numeric_cols) if non_numeric_cols else 'None'}",
    ]

    return {
        "row_count": len(rows),
        "column_count": len(columns),
        "columns": columns,
        "column_stats": col_stats,
        "correlations": correlations,
        "summary_text": "\n".join(summary_text_lines),
    }


def analyze_json(data: Any) -> Dict[str, Any]:
    # Key frequency and schema inference
    key_counter: Counter[str] = Counter()

    def walk(obj, path: str = ""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                key_counter[k] += 1
                walk(v, f"{path}.{k}" if path else k)
        elif isinstance(obj, list):
            for v in obj:
                walk(v, path)

    walk(data)
    top_keys = key_counter.most_common(20)

    return {
        "top_keys": [[k, int(v)] for k, v in top_keys],
        "distinct_keys": len(key_counter),
    }

