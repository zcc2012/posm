"""
统一判定标准匹配修复补丁。

作用：
1. 覆盖 /api/pricing_standards/match 接口。
2. 所有工艺统一按：工艺类型 + 材料分类 + 长宽尺寸 + 数量范围 + 优先级 匹配。
3. 长宽支持正向与互换方向匹配，避免图纸横竖方向导致匹配错误。
4. 组合工艺会拆成基础工艺逐项匹配判定标准。

这个文件不破坏原 app.py，通过 run_fixed_pricing.py 启动时自动安装。
"""

from __future__ import annotations

import sqlite3
from typing import Any, Dict, Iterable, List, Optional, Tuple

from flask import jsonify, request

DB_PATH = "quotation_system.db"
INF = 999999999.0

PROCESS_TYPE_ALIASES = {
    "printing": ["printing", "print", "印刷", "画面", "四色", "专色", "uv印", "喷绘", "写真"],
    "cutting": ["cutting", "切割", "裁切", "裁", "分切"],
    "die-cutting": ["die-cutting", "die_cutting", "die cutting", "模切", "刀模", "啤", "啤机"],
    "varnish": ["varnish", "光油", "过油", "uv油", "上光"],
    "lamination": ["lamination", "覆膜", "过膜", "哑膜", "亮膜"],
    "hot-stamping": ["hot-stamping", "hot_stamping", "foil", "烫金", "烫银", "烫"],
    "embossing": ["embossing", "creasing", "压痕", "压线", "压凸", "凹凸"],
    "binding": ["binding", "装订", "胶装", "骑马钉"],
    "folding": ["folding", "折页", "折叠", "折"],
    "punching": ["punching", "打孔", "冲孔"],
    "wastage": ["wastage", "损耗"],
}


def split_base_processes(value: Any) -> List[str]:
    return [item.strip() for item in str(value or "").split(",") if item.strip()]


def to_number(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def normalize_max(value: Any) -> float:
    number = to_number(value, INF)
    return INF if number <= 0 else number


def normalize_process_type(text: Any) -> str:
    raw = str(text or "").strip().lower()
    if not raw:
        return ""

    raw_compact = raw.replace("_", "-").replace(" ", "-")
    for normalized, aliases in PROCESS_TYPE_ALIASES.items():
        if raw_compact == normalized:
            return normalized
        for alias in aliases:
            alias_text = str(alias).strip().lower()
            if not alias_text:
                continue
            if raw == alias_text or alias_text in raw:
                return normalized
    return raw_compact


def row_to_dict(cursor: sqlite3.Cursor, row: Iterable[Any]) -> Dict[str, Any]:
    columns = [col[0] for col in cursor.description]
    result = dict(zip(columns, row))
    for key in [
        "id",
        "material_category_id",
        "min_quantity",
        "max_quantity",
        "priority",
        "is_active",
        "wastage_0_100",
        "wastage_100_3000",
        "wastage_3000_plus",
    ]:
        if key in result and result[key] is not None:
            try:
                result[key] = int(result[key])
            except (TypeError, ValueError):
                pass
    for key in [
        "min_length",
        "max_length",
        "min_width",
        "max_width",
        "base_price",
        "square_price",
        "order_length_increase",
        "order_width_increase",
    ]:
        if key in result:
            result[key] = to_number(result[key], 0.0)
    return result


def get_table_columns(cursor: sqlite3.Cursor, table_name: str) -> List[str]:
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [row[1] for row in cursor.fetchall()]


def get_process_steps(cursor: sqlite3.Cursor, process_name: str) -> List[str]:
    """从工艺库读取组合工艺的基础工艺；没有组合时使用工艺名称本身。"""
    if not process_name:
        return []

    cursor.execute("SELECT base_processes FROM processes WHERE name = ? LIMIT 1", (process_name,))
    row = cursor.fetchone()
    if not row:
        cursor.execute("SELECT base_processes FROM processes WHERE ? LIKE '%' || name || '%' OR name LIKE '%' || ? || '%' LIMIT 1", (process_name, process_name))
        row = cursor.fetchone()

    if row and row[0]:
        steps = split_base_processes(row[0])
        if steps:
            return steps
    return [process_name]


def in_range(value: float, min_value: Any, max_value: Any) -> bool:
    low = to_number(min_value, 0.0)
    high = normalize_max(max_value)
    return low <= value <= high


def dimension_match(standard: Dict[str, Any], length: float, width: float) -> Tuple[bool, str]:
    """
    长宽判定：
    - 先按输入长宽正向匹配；
    - 正向不匹配时，自动尝试长宽互换匹配。
    这样可以避免 400x1080 与 1080x400 因方向不同导致选错标准。
    """
    min_l = standard.get("min_length", 0)
    max_l = standard.get("max_length", INF)
    min_w = standard.get("min_width", 0)
    max_w = standard.get("max_width", INF)

    direct = in_range(length, min_l, max_l) and in_range(width, min_w, max_w)
    if direct:
        return True, "direct"

    swapped = in_range(width, min_l, max_l) and in_range(length, min_w, max_w)
    if swapped:
        return True, "swapped"

    return False, "none"


def quantity_match(standard: Dict[str, Any], quantity: float) -> bool:
    min_q = to_number(standard.get("min_quantity"), 0.0)
    max_q = normalize_max(standard.get("max_quantity"))
    return min_q <= quantity <= max_q


def category_match(standard: Dict[str, Any], material_category_id: Optional[int]) -> bool:
    standard_category_id = standard.get("material_category_id")
    if standard_category_id in (None, "", 0, "0"):
        return True
    if material_category_id in (None, ""):
        return False
    try:
        return int(standard_category_id) == int(material_category_id)
    except (TypeError, ValueError):
        return False


def get_wastage_by_quantity(standard: Dict[str, Any], quantity: float) -> int:
    if quantity <= 100:
        return int(to_number(standard.get("wastage_0_100"), to_number(standard.get("wastage"), 0)))
    if quantity <= 3000:
        return int(to_number(standard.get("wastage_100_3000"), to_number(standard.get("wastage"), 0)))
    return int(to_number(standard.get("wastage_3000_plus"), to_number(standard.get("wastage"), 0)))


def standard_specificity_score(standard: Dict[str, Any], material_category_id: Optional[int], quantity: float) -> Tuple[float, float, float, float, float]:
    has_exact_category = 1.0 if standard.get("material_category_id") not in (None, "", 0, "0") else 0.0
    priority = to_number(standard.get("priority"), 1.0)

    length_span = normalize_max(standard.get("max_length")) - to_number(standard.get("min_length"), 0.0)
    width_span = normalize_max(standard.get("max_width")) - to_number(standard.get("min_width"), 0.0)
    quantity_span = normalize_max(standard.get("max_quantity")) - to_number(standard.get("min_quantity"), 0.0)

    # 范围越小越精确，所以取负值参与排序。
    size_specificity = -(max(length_span, 0.0) * max(width_span, 0.0))
    quantity_specificity = -max(quantity_span, 0.0)
    standard_id = to_number(standard.get("id"), 0.0)
    return (has_exact_category, priority, size_specificity, quantity_specificity, standard_id)


def load_active_standards(cursor: sqlite3.Cursor) -> List[Dict[str, Any]]:
    cursor.execute("SELECT * FROM pricing_standards WHERE COALESCE(is_active, 1) = 1")
    return [row_to_dict(cursor, row) for row in cursor.fetchall()]


def find_best_standard(
    standards: List[Dict[str, Any]],
    process_type: str,
    material_category_id: Optional[int],
    length: float,
    width: float,
    quantity: float,
) -> Optional[Dict[str, Any]]:
    normalized_type = normalize_process_type(process_type)
    matched: List[Dict[str, Any]] = []

    for standard in standards:
        standard_type = normalize_process_type(standard.get("type"))
        if standard_type != normalized_type:
            continue
        if not category_match(standard, material_category_id):
            continue
        if not quantity_match(standard, quantity):
            continue

        is_dimension_match, direction = dimension_match(standard, length, width)
        if not is_dimension_match:
            continue

        candidate = dict(standard)
        candidate["type"] = normalized_type
        candidate["original_type"] = standard.get("type")
        candidate["matched_direction"] = direction
        candidate["wastage"] = get_wastage_by_quantity(candidate, quantity)
        matched.append(candidate)

    if not matched:
        return None

    matched.sort(
        key=lambda item: standard_specificity_score(item, material_category_id, quantity),
        reverse=True,
    )
    return matched[0]


def build_match_response() -> Any:
    data = request.get_json(silent=True) or {}
    process_name = str(data.get("process_name") or "").strip()
    length = to_number(data.get("length"), 0.0)
    width = to_number(data.get("width"), 0.0)
    quantity = to_number(data.get("quantity"), 1.0)

    material_category_id_raw = data.get("material_category_id")
    try:
        material_category_id = int(material_category_id_raw) if material_category_id_raw not in (None, "") else None
    except (TypeError, ValueError):
        material_category_id = None

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        standards = load_active_standards(cursor)
        process_steps = get_process_steps(cursor, process_name)

        components: List[Dict[str, Any]] = []
        missing_steps: List[Dict[str, str]] = []

        for step in process_steps:
            step_type = normalize_process_type(step)
            if not step_type:
                continue
            standard = find_best_standard(standards, step_type, material_category_id, length, width, quantity)
            if standard:
                standard["component_name"] = step
                components.append(standard)
            else:
                missing_steps.append({"name": step, "type": step_type})

        if len(components) == 1 and not missing_steps:
            standard = components[0]
        elif components:
            standard = {
                "id": None,
                "type": "combined",
                "name": process_name or "组合工艺",
                "components": components,
                "missing_components": missing_steps,
                "matched_direction": components[0].get("matched_direction", "direct"),
                "wastage": max([int(to_number(item.get("wastage"), 0)) for item in components] or [0]),
            }
        else:
            standard = None

        return jsonify({
            "standard": standard,
            "debug": {
                "engine": "fixed-pricing-match-v1",
                "process_name": process_name,
                "process_steps": process_steps,
                "normalized_steps": [normalize_process_type(step) for step in process_steps],
                "material_category_id": material_category_id,
                "length": length,
                "width": width,
                "quantity": quantity,
                "missing_steps": missing_steps,
            }
        })
    finally:
        conn.close()


def install_pricing_match_fix(app) -> None:
    """替换原有 /api/pricing_standards/match 接口。"""
    replaced = False
    for rule in list(app.url_map.iter_rules()):
        if rule.rule == "/api/pricing_standards/match":
            app.view_functions[rule.endpoint] = build_match_response
            replaced = True

    if not replaced:
        app.add_url_rule(
            "/api/pricing_standards/match",
            "fixed_pricing_standards_match",
            build_match_response,
            methods=["POST"],
        )

    # 额外保留一个调试接口，方便确认当前命中了哪条标准。
    if "fixed_pricing_standards_debug_match" not in app.view_functions:
        app.add_url_rule(
            "/api/pricing_standards/debug_match",
            "fixed_pricing_standards_debug_match",
            build_match_response,
            methods=["POST"],
        )
