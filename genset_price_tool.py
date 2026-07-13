#!/usr/bin/env python3
"""
Extract genset price rows from price_list_genset.xlsx and build a small
offline calculator.

The workbook already contains cached values for formulas, so this script reads
the xlsx XML directly and does not need Excel, openpyxl, or pandas.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET


MAIN_PRICE_HEADERS = {
    "主推型号",
    "柴油机功率",
    "发电机功率",
    "成本核算",
    "工厂底价",
    "销售底价",
}

NS = {
    "a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}


def column_index(column: str) -> int:
    value = 0
    for char in column:
        value = value * 26 + ord(char) - 64
    return value


def column_name(index: int) -> str:
    value = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        value = chr(65 + remainder) + value
    return value


def cell_ref_to_coord(ref: str) -> tuple[int, int]:
    match = re.match(r"([A-Z]+)(\d+)", ref)
    if not match:
        raise ValueError(f"Bad cell reference: {ref}")
    return int(match.group(2)), column_index(match.group(1))


def first_number(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip().replace(",", "")
    if not text:
        return None
    match = re.search(r"[-+]?\d+(?:\.\d+)?", text)
    if not match:
        return None
    return float(match.group(0))


def is_formula(value: Any) -> bool:
    return isinstance(value, str) and value.startswith("=")


@dataclass
class Cell:
    value: str = ""
    formula: str = ""
    cached: str = ""


class WorkbookReader:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.zip = zipfile.ZipFile(path)
        self.shared_strings = self._read_shared_strings()
        self.sheets = self._read_sheets()

    def close(self) -> None:
        self.zip.close()

    def _read_shared_strings(self) -> list[str]:
        if "xl/sharedStrings.xml" not in self.zip.namelist():
            return []
        root = ET.fromstring(self.zip.read("xl/sharedStrings.xml"))
        values = []
        for si in root.findall("a:si", NS):
            values.append(
                "".join(
                    node.text or ""
                    for node in si.iter(
                        "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t"
                    )
                )
            )
        return values

    def _read_sheets(self) -> list[tuple[str, str]]:
        workbook = ET.fromstring(self.zip.read("xl/workbook.xml"))
        rels = ET.fromstring(self.zip.read("xl/_rels/workbook.xml.rels"))
        relmap = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels}
        sheets = []
        for sheet in workbook.find("a:sheets", NS):
            rid = sheet.attrib[
                "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
            ]
            sheets.append((sheet.attrib["name"], "xl/" + relmap[rid].lstrip("/")))
        return sheets

    def read_sheet(self, sheet_path: str) -> dict[tuple[int, int], Cell]:
        root = ET.fromstring(self.zip.read(sheet_path))
        cells: dict[tuple[int, int], Cell] = {}
        for cell in root.findall(".//a:c", NS):
            ref = cell.attrib.get("r")
            if not ref:
                continue
            row, col = cell_ref_to_coord(ref)
            formula_node = cell.find("a:f", NS)
            value_node = cell.find("a:v", NS)
            cached = value_node.text if value_node is not None and value_node.text else ""
            formula = formula_node.text or "" if formula_node is not None else ""
            value = cached
            if formula_node is not None:
                value = "=" + formula
            elif cell.attrib.get("t") == "s" and cached.isdigit():
                index = int(cached)
                value = self.shared_strings[index] if index < len(self.shared_strings) else cached
            cells[(row, col)] = Cell(value=value, formula=formula, cached=cached)
        return cells


def numeric_cell(cells: dict[tuple[int, int], Cell], row: int, col: int) -> float:
    cell = cells.get((row, col), Cell())
    source = cell.cached or cell.value
    return first_number(source) or 0.0


def display_cell(cells: dict[tuple[int, int], Cell], row: int, col: int) -> str:
    cell = cells.get((row, col), Cell())
    if cell.cached and is_formula(cell.value):
        return cell.cached
    return cell.value


def find_header(cells: dict[tuple[int, int], Cell]) -> tuple[int, dict[str, int]] | None:
    rows = sorted({row for row, _ in cells})
    for row in rows[:12]:
        headers: dict[str, int] = {}
        for (r, col), cell in cells.items():
            if r != row:
                continue
            text = str(cell.value).strip()
            if text:
                headers[text] = col
        if len(MAIN_PRICE_HEADERS.intersection(headers)) >= 4:
            return row, headers
    return None


def nearest_section(cells: dict[tuple[int, int], Cell], row: int, header_row: int) -> str:
    for r in range(row - 1, header_row, -1):
        text = str(display_cell(cells, r, 1)).strip()
        if text and first_number(text) is None:
            return text
    return ""


def calculate_price(cells: dict[tuple[int, int], Cell], row: int, cols: dict[str, int]) -> dict[str, float]:
    component_names = [
        "5/6节距全铜",
        "半铜      有刷电机",
        "水箱",
        "水箱价格",
        "水箱涨后价格",
        "组装成套",
        "电气成套",
        "柴油机",
        "电瓶",
        "油箱",
        "消音器",
        "调试费",
    ]
    components = sum(numeric_cell(cells, row, cols[name]) for name in component_names if name in cols)
    if not components:
        components = numeric_cell(cells, row, cols.get("成本核算", 0))
        cost = components
    else:
        cost = components * 1.05
    factory = cost * 1.10
    sales = cost * 1.15
    return {
        "component_total": round(components, 2),
        "calculated_cost": round(cost, 2),
        "calculated_factory_floor": round(factory, 2),
        "calculated_sales_floor": round(sales, 2),
    }


def extract_records(xlsx_path: Path) -> list[dict[str, Any]]:
    reader = WorkbookReader(xlsx_path)
    records: list[dict[str, Any]] = []
    try:
        for sheet_name, sheet_path in reader.sheets:
            cells = reader.read_sheet(sheet_path)
            found = find_header(cells)
            if not found:
                continue
            header_row, cols = found
            required = {"主推型号", "发电机功率", "成本核算"}
            if not required.issubset(cols):
                continue
            max_row = max((row for row, _ in cells), default=0)
            for row in range(header_row + 1, max_row + 1):
                model = str(display_cell(cells, row, cols["主推型号"])).strip()
                genset_power_raw = str(display_cell(cells, row, cols["发电机功率"])).strip()
                if not model or not genset_power_raw:
                    continue
                genset_kw = first_number(genset_power_raw)
                if genset_kw is None:
                    continue
                calculated = calculate_price(cells, row, cols)
                default_alternator_raw = numeric_cell(cells, row, cols.get("5/6节距全铜", 0))
                assembly_raw = numeric_cell(cells, row, cols.get("组装成套", 0))
                silencer_raw = numeric_cell(cells, row, cols.get("消音器", 0))
                cost_raw = numeric_cell(cells, row, cols.get("成本核算", 0))
                factory_raw = numeric_cell(cells, row, cols.get("工厂底价", 0))
                sales_raw = numeric_cell(cells, row, cols.get("销售底价", 0))
                records.append(
                    {
                        "brand": sheet_name,
                        "section": nearest_section(cells, row, header_row),
                        "model": model,
                        "engine_power": str(display_cell(cells, row, cols.get("柴油机功率", 0))).strip(),
                        "engine_kw": first_number(display_cell(cells, row, cols.get("柴油机功率", 0))),
                        "engine_price": round(numeric_cell(cells, row, cols.get("柴油机", 0)), 2) if "柴油机" in cols else "",
                        "genset_power": genset_power_raw,
                        "genset_kw": genset_kw,
                        "component_total": calculated["component_total"],
                        "default_alternator_price": round(default_alternator_raw, 2) if default_alternator_raw else "",
                        "assembly_cost": round(assembly_raw, 2) if assembly_raw else "",
                        "silencer_cost": round(silencer_raw, 2) if silencer_raw else "",
                        "cost_book": round(cost_raw, 2) if cost_raw else "",
                        "factory_floor_book": round(factory_raw, 2) if factory_raw else "",
                        "sales_floor_book": round(sales_raw, 2) if sales_raw else "",
                        "cost_calculated": calculated["calculated_cost"],
                        "factory_floor_calculated": calculated["calculated_factory_floor"],
                        "sales_floor_calculated": calculated["calculated_sales_floor"],
                        "source_sheet": sheet_name,
                        "source_row": row,
                    }
                )
    finally:
        reader.close()
    return records


def looks_like_alternator_model(value: Any) -> bool:
    text = str(value).strip()
    if len(text) < 2 or len(text) > 45:
        return False
    blocked = [
        "model",
        "型号",
        "功率",
        "价格",
        "price",
        "kw",
        "kva",
        "rmb",
        "备注",
        "序号",
        "容量",
        "机座",
        "单价",
        "出厂",
        "采购",
        "销售",
        "发电机",
        "价格表",
        "公司",
        "中心高",
        "单位",
        "cont",
        "standby",
    ]
    lowered = text.lower()
    if any(word in lowered for word in blocked):
        return False
    if first_number(text) is not None and re.fullmatch(r"[\d.]+\s*(kw|kva)?(?:\([^)]*\))?", lowered):
        return False
    return bool(re.search(r"[A-Za-z]", text) and re.search(r"\d", text))


def extract_alternator_records(xlsx_path: Path) -> list[dict[str, Any]]:
    """Extract alternator records: prefer B=model, E=power_kw, N=price when both are numbers;
    otherwise fall back to scanning for model+price rows. 50Hz data."""
    if not xlsx_path.exists():
        return []

    reader = WorkbookReader(xlsx_path)
    records: list[dict[str, Any]] = []
    seen: set[tuple[str, int, int]] = set()
    # Keywords that indicate non-data rows
    skip_keywords = [
        "备注", "备注:", "价格有效", "制表日期", "型号", "item", "model",
        "序号", "机座", "功率", "型号/Model", "含税", "电机价格", "单位",
        "rpm", "r/min", "50hz", "60hz",
    ]
    try:
        for sheet_name, sheet_path in reader.sheets:
            cells = reader.read_sheet(sheet_path)
            max_row = max((row for row, _ in cells), default=0)
            max_col = max((col for _, col in cells), default=0)
            # Pass 1: rows where B/E/N are clean numbers (低压利莱森玛 style)
            for row in range(1, max_row + 1):
                model_raw = display_cell(cells, row, 2).strip()   # B
                e_raw = display_cell(cells, row, 5).strip()      # E
                n_raw = display_cell(cells, row, 14).strip()     # N
                if not model_raw:
                    continue
                e_num = first_number(e_raw)
                n_num = first_number(n_raw)
                if e_num is None or n_num is None:
                    continue
                # Valid power range and reasonable price
                if not (0.5 <= e_num <= 3000) or n_num < 100:
                    continue
                lower = model_raw.lower()
                if any(kw in lower for kw in skip_keywords):
                    continue
                key = (sheet_name, row, 2)
                if key in seen:
                    continue
                seen.add(key)
                records.append({
                    "brand": sheet_name,
                    "model": model_raw,
                    "power_kw": e_num,
                    "power_text": e_raw,
                    "price": round(n_num, 2),
                    "price_text": n_raw,
                    "source_sheet": sheet_name,
                    "source_row": row,
                    "source_col": "B",
                    "price_col": "N",
                })

            # Pass 2: fall back to full sheet scan for other brands
            for row in range(1, max_row + 1):
                model_cols = [
                    col for col in range(1, max_col + 1)
                    if looks_like_alternator_model(display_cell(cells, row, col))
                ]
                for index, col in enumerate(model_cols):
                    model = str(display_cell(cells, row, col)).strip()
                    end_col = model_cols[index + 1] - 1 if index + 1 < len(model_cols) else min(max_col, col + 12)
                    values = []
                    for value_col in range(col + 1, end_col + 1):
                        raw = display_cell(cells, row, value_col)
                        number = first_number(raw)
                        if number is not None:
                            values.append((value_col, number, str(raw).strip()))
                    if not values:
                        continue
                    price_candidates = [item for item in values if item[1] >= 1000]
                    if not price_candidates:
                        continue
                    price_col, price, price_raw = price_candidates[-1]
                    power_candidates = [
                        item for item in values
                        if item[0] < price_col and 1 <= item[1] <= 5000 and item[1] < price
                    ]
                    if not power_candidates:
                        continue
                    power_col, power, power_raw = power_candidates[0]
                    if price < max(3000, power * 3):
                        continue
                    key = (sheet_name, row, col)
                    if key in seen:
                        continue
                    seen.add(key)
                    records.append({
                        "brand": sheet_name,
                        "model": model,
                        "power_kw": power,
                        "power_text": power_raw,
                        "price": round(price, 2),
                        "price_text": price_raw,
                        "source_sheet": sheet_name,
                        "source_row": row,
                        "source_col": column_name(col),
                        "price_col": column_name(price_col),
                    })
    finally:
        reader.close()
    return records


def parse_power_range(value: Any) -> tuple[float, float] | None:
    text = str(value).strip().replace("ＫＷ", "KW").replace("kw", "KW").replace("Kw", "KW")
    numbers = [float(item) for item in re.findall(r"\d+(?:\.\d+)?", text)]
    if not numbers:
        return None
    if len(numbers) >= 2:
        return numbers[0], numbers[1]
    number = numbers[0]
    if text.startswith(">") or text.startswith("＞"):
        return number, 99999.0
    return number, number


# 箱体 section header 识别列表（按优先级从长到短排列，避免子串误匹配）
BOX_SECTION_HEADERS = [
    "移动式静音箱（底座油箱）（减成套费）",
    "固定式静音集装箱（不减成套费）",
    "固定式静音箱（减成套费）",
    "固定式防雨罩（底座油箱）（减成套费）",
    "移动拖车（挂式油箱）（不减成套费）",
    "只是  移动底盘（不含防雨罩静音箱）",
    "只是 高速移动底盘（60-80码 不含防雨罩静音箱）",
]


def extract_canopy_records(xlsx_path: Path) -> list[dict[str, Any]]:
    reader = WorkbookReader(xlsx_path)
    records: list[dict[str, Any]] = []
    try:
        target = None
        for sheet_name, sheet_path in reader.sheets:
            if sheet_name == "箱体":
                target = sheet_path
                break
        if not target:
            return records
        cells = reader.read_sheet(target)
        max_row = max((row for row, _ in cells), default=0)
        section = ""
        active = False
        for row in range(1, max_row + 1):
            first = str(display_cell(cells, row, 1)).strip()
            if first:
                # 检查是否为新的 section header
                matched = None
                for header in BOX_SECTION_HEADERS:
                    if header in first:
                        matched = first  # 用完整文本作为 section 名
                        break
                if matched is not None:
                    section = matched
                    active = True
                    continue
                # 跳过表头行
                if first in {"功率", "规格", "单位", "备注"}:
                    continue
                # 遇到注释行则结束当前 section
                if active and first.startswith("（"):
                    active = False
                    continue
            if not active:
                continue
            power_text = first
            power_range = parse_power_range(power_text)
            price = numeric_cell(cells, row, 3)
            if not power_range or not price:
                continue
            min_kw, max_kw = power_range
            records.append(
                {
                    "type": section,
                    # 标题含"减成套费"且不含"不减"则扣减；其余不减
                    "deduct": "减成套费" in section and "不减" not in section,
                    "power_text": power_text,
                    "min_kw": min_kw,
                    "max_kw": max_kw,
                    "price": round(price, 2),
                    "size": str(display_cell(cells, row, 4)).strip(),
                    "weight": str(display_cell(cells, row, 5)).strip(),
                    "tank_l": str(display_cell(cells, row, 6)).strip(),
                    "remark": str(display_cell(cells, row, 7)).strip(),
                    "source_sheet": "箱体",
                    "source_row": row,
                }
            )
    finally:
        reader.close()
    return records


def write_csv(records: list[dict[str, Any]], path: Path) -> None:
    fields = [
        "brand",
        "section",
        "model",
        "engine_power",
        "engine_kw",
        "engine_price",
        "genset_power",
        "genset_kw",
        "component_total",
        "default_alternator_price",
        "assembly_cost",
        "silencer_cost",
        "cost_book",
        "factory_floor_book",
        "sales_floor_book",
        "cost_calculated",
        "factory_floor_calculated",
        "sales_floor_calculated",
        "source_sheet",
        "source_row",
    ]
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)


def write_json(records: list[dict[str, Any]], path: Path) -> None:
    path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")


def write_alternator_csv(records: list[dict[str, Any]], path: Path) -> None:
    fields = [
        "brand",
        "model",
        "power_kw",
        "power_text",
        "price",
        "price_text",
        "source_sheet",
        "source_row",
        "source_col",
        "price_col",
    ]
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)


def write_canopy_csv(records: list[dict[str, Any]], path: Path) -> None:
    fields = [
        "type",
        "deduct",
        "power_text",
        "min_kw",
        "max_kw",
        "price",
        "size",
        "weight",
        "tank_l",
        "remark",
        "source_sheet",
        "source_row",
    ]
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)


def write_html(
    records: list[dict[str, Any]],
    alternator_records: list[dict[str, Any]],
    canopy_records: list[dict[str, Any]],
    path: Path,
) -> None:
    data = json.dumps(records, ensure_ascii=False)
    alternator_data = json.dumps(alternator_records, ensure_ascii=False)
    canopy_data = json.dumps(canopy_records, ensure_ascii=False)
    brands = sorted({record["brand"] for record in records})
    if "东康" in brands and "重康" in brands:
        brands.remove("重康")
        brands.insert(brands.index("东康") + 1, "重康")
    alternator_brands = sorted({record["brand"] for record in alternator_records})
    opts = []
    for brand in brands:
        sel = ' selected' if brand == '上柴' else ''
        opts.append(f'<option value="{html.escape(brand)}"{sel}>{html.escape(brand)}</option>')
    brand_options = "\n".join(opts)
    alternator_brand_options = "\n".join(
        f'<option value="{html.escape(brand)}">{html.escape(brand)}</option>' for brand in alternator_brands
    )
    path.write_text(
        f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Genset Price Calculator</title>
<style>
:root {{ color-scheme: light; font-family: Arial, Helvetica, sans-serif; }}
body {{ margin: 0; background: #f6f7f9; color: #172026; }}
main {{ max-width: 1280px; margin: 0 auto; padding: 24px; }}
.titlebar {{ display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }}
h1 {{ margin: 0; font-size: 28px; font-weight: 700; }}
h2 {{ margin: 34px 0 16px; font-size: 22px; font-weight: 700; }}
.controls {{ display: grid; grid-template-columns: repeat(9, minmax(120px, 1fr)); gap: 10px; margin-bottom: 18px; }}
label {{ display: grid; gap: 6px; font-size: 12px; color: #52616b; font-weight: 700; }}
input, select {{ height: 38px; border: 1px solid #cfd6dd; border-radius: 6px; padding: 0 10px; background: white; color: #172026; }}
.summary {{ display: flex; gap: 16px; align-items: center; margin-bottom: 12px; color: #52616b; }}
button {{ height: 38px; border: 1px solid #1f6feb; border-radius: 6px; background: #1f6feb; color: white; font-weight: 700; cursor: pointer; }}
table {{ width: 100%; border-collapse: collapse; background: white; border: 1px solid #dde3ea; }}
th, td {{ padding: 8px 10px; border-bottom: 1px solid #edf1f5; text-align: left; font-size: 13px; vertical-align: top; }}
table.genset th:nth-child(3), table.genset td:nth-child(3) {{ width: 8.5em; }}  /* Model */
table.genset th:last-child, table.genset td:last-child {{ width: 5.5em; }}  /* Source */
th {{ position: sticky; top: 0; background: #edf2f7; z-index: 1; }}
td.num, th.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
tr:hover {{ background: #f3f8ff; }}
tr.selected {{ background: #cce0ff; }}
tr.selected:hover {{ background: #b0d0ff; }}
td .cv {{ cursor: pointer; position: relative; }}
td .cv:hover {{ background: #cce0ff; border-radius: 3px; }}
td .cv .cp {{ display: none; position: absolute; bottom: 110%; left: 50%; transform: translateX(-50%); background: #333; color: #fff; font-size: 11px; padding: 3px 7px; border-radius: 4px; white-space: nowrap; z-index: 10; }}
td .cv .cp::after {{ content: ''; position: absolute; top: 100%; left: 50%; transform: translateX(-50%); border: 4px solid transparent; border-top-color: #333; }}
td .cv:hover .cp {{ display: block; }}
td .cv.done .cp {{ background: #2ea44f; }}
td .cv.done .cp::after {{ border-top-color: #2ea44f; }}
.table-wrap {{ max-height: 72vh; overflow: auto; border-radius: 8px; }}
@media (max-width: 900px) {{ .controls {{ grid-template-columns: 1fr 1fr; }} main {{ padding: 14px; }} }}
</style>
</head>
<body>
<main>
<div class="titlebar"><h1>Genset Price Calculator</h1></div>
<section class="controls">
<label>Engine Brand<select id="brand"><option value="">All brands</option>{brand_options}</select></label>
<label>Power kW<input id="power" type="number" min="0" step="1" placeholder="e.g. 100"></label>
<label>Tolerance kW<input id="tolerance" type="number" min="0" step="1" value="0"></label>
<label>Alternator Brand<select id="gensetAltBrand"><option value="">Default alternator</option>{alternator_brand_options}</select></label>
<label>Silent Canopy<select id="canopy"><option value="">No silent canopy</option><option value="fixed">固定式静音箱（减成套费）</option><option value="container">固定式静音集装箱（不减成套费）</option><option value="mobile_box">移动式静音箱（底座油箱）（减成套费）</option><option value="raincover_fixed">固定式防雨罩（底座油箱）（减成套费）</option><option value="trailer">移动拖车（挂式油箱）（不减成套费）</option><option value="chassis">只是  移动底盘（不含防雨罩静音箱）</option><option value="chassis_fast">只是 高速移动底盘（60-80码 不含防雨罩静音箱）</option></select></label>
<label>Freight CNY<input id="freight" type="number" min="0" step="100" value="0" placeholder="0"></label>
<label>Search<input id="search" type="search" placeholder="model or section"></label>
<label>Profit %<input id="markup" type="number" min="0" step="0.1" value="0"></label>
<label>Exchange Rate<input id="rate" type="number" min="0.1" step="0.01" value="6.8" placeholder="6.8"></label>
</section>
<div class="summary"><strong id="count"></strong><span>Sales price uses factory price plus profit.</span><button id="copy">Copy</button><button id="reset">Reset</button></div>
<div style="background:#fff8e1;border:1px solid #ffe082;padding:10px 14px;border-radius:6px;margin-bottom:10px;font-size:12px;color:#7b5e00;">
<strong>注意：</strong><br>
1，请查询后先验证原来EXCEL表里面的数据；<br>
2，配电柜，控制模块，附属件等暂未包含。
</div>
<div class="table-wrap">
<table class="genset">
<thead><tr>
<th>Brand</th><th>Section</th><th>Model</th><th>Engine Power</th><th class="num">Engine Price</th><th>Genset Power</th>
<th class="num">Default Alternator</th><th>Selected Alternator</th><th class="num">Alternator Price</th>
<th>Silent Canopy</th><th class="num">Box Price</th><th class="num">Deduct</th>
<th class="num">Freight</th><th class="num">Cost</th><th class="num">Sales</th>
<th class="num">USD</th>
<th>Source</th>
</tr></thead>
<tbody id="rows"></tbody>
</table>
</div>
<h2>Alternator Price Calculator</h2>
<section class="controls">
<label>Alternator Brand<select id="altBrand"><option value="">All brands</option>{alternator_brand_options}</select></label>
<label>Power kW<input id="altPower" type="number" min="0" step="1" placeholder="e.g. 100"></label>
<label>Tolerance kW<input id="altTolerance" type="number" min="0" step="1" value="0"></label>
<label>Search<input id="altSearch" type="search" placeholder="model"></label>
<label>Profit %<input id="altMarkup" type="number" min="0" step="0.1" value="0"></label>
</section>
<div class="summary"><strong id="altCount"></strong><span>Alternator custom price uses listed price plus profit.</span><button id="altCopy">Copy alternator prices</button><button id="altReset">Reset</button></div>
<div class="table-wrap">
<table>
<thead><tr>
<th>Brand</th><th>Model</th><th class="num">Power kW</th><th class="num">Price</th><th class="num">Sales</th><th>Source</th>
</tr></thead>
<tbody id="altRows"></tbody>
</table>
</div>
</main>
<script>
const records = {data};
const alternatorRecords = {alternator_data};
const canopyRecords = {canopy_data};
const state = {{
  brand: document.getElementById('brand'),
  power: document.getElementById('power'),
  tolerance: document.getElementById('tolerance'),
  gensetAltBrand: document.getElementById('gensetAltBrand'),
  canopy: document.getElementById('canopy'),
  freight: document.getElementById('freight'),
  rate: document.getElementById('rate'),
  search: document.getElementById('search'),
  markup: document.getElementById('markup'),
  rows: document.getElementById('rows'),
  count: document.getElementById('count')
}};
const altState = {{
  brand: document.getElementById('altBrand'),
  power: document.getElementById('altPower'),
  tolerance: document.getElementById('altTolerance'),
  search: document.getElementById('altSearch'),
  markup: document.getElementById('altMarkup'),
  rows: document.getElementById('altRows'),
  count: document.getElementById('altCount')
}};
const money = value => value === '' || value == null ? '' : Number(value).toFixed(0);
function findAlternator(brand, power) {{
  if (!brand || !power) return null;
  const matches = alternatorRecords
    .filter(row => row.brand === brand)
    .map(row => ({{...row, diff: Math.abs(Number(row.power_kw) - Number(power))}}))
    .sort((a, b) => a.diff - b.diff || Number(a.power_kw) - Number(b.power_kw));
  return matches[0] || null;
}}
function findCanopy(canopyType, power) {{
  if (!canopyType) return null;
  const sectionMap = {{
    fixed: "固定式静音箱（减成套费）",
    container: "固定式静音集装箱（不减成套费）",
    mobile_box: "移动式静音箱（底座油箱）（减成套费）",
    raincover_fixed: "固定式防雨罩（底座油箱）（减成套费）",
    trailer: "移动拖车（挂式油箱）（不减成套费）",
    chassis: "只是  移动底盘（不含防雨罩静音箱）",
    chassis_fast: "只是 高速移动底盘（60-80码 不含防雨罩静音箱）",
  }};
  const section = sectionMap[canopyType] || "";
  const byType = canopyRecords.filter(row => row.type === section);
  const exact = byType.find(row => Number(power) >= Number(row.min_kw) && Number(power) <= Number(row.max_kw));
  if (exact) return exact;
  return byType
    .map(row => ({{...row, diff: Math.min(Math.abs(Number(power) - Number(row.min_kw)), Math.abs(Number(power) - Number(row.max_kw)))}}))
    .sort((a, b) => a.diff - b.diff)[0] || null;
}}
document.addEventListener('click', e => {{
  const el = e.target.closest('td .cv');
  if (!el) return;
  const val = el.dataset.v;
  navigator.clipboard.writeText(val);
  const cp = el.querySelector('.cp');
  if (!cp) return;
  cp.textContent = '✓';
  el.classList.add('done');
  setTimeout(() => {{ cp.textContent = 'Copy'; el.classList.remove('done'); }}, 1200);
}});
document.addEventListener('click', e => {{
  const tr = e.target.closest('table.genset tbody tr');
  if (!tr || tr.querySelector('td[colspan]')) return;
  document.querySelectorAll('table.genset tr.selected').forEach(r => r.classList.remove('selected'));
  tr.classList.add('selected');
}});
[state['brand'], state['power'], state['tolerance'], state['gensetAltBrand'], state['canopy'], state['freight'], state['search'], state['markup'], state['rate']].forEach(el => {{
  el.addEventListener('input', render);
  el.addEventListener('change', render);
}});
[altState['brand'], altState['power'], altState['tolerance'], altState['search'], altState['markup']].forEach(el => {{
  el.addEventListener('input', renderAlternators);
  el.addEventListener('change', renderAlternators);
}});
function render() {{
  const brand = state['brand'].value;
  const alternatorBrand = state['gensetAltBrand'].value;
  const useCanopy = Boolean(state['canopy'].value);
  const power = Number(state['power'].value);
  const tolerance = Number(state['tolerance'].value || 0);
  const term = state['search'].value.trim().toLowerCase();
  const markup = Number(state['markup'].value || 0) / 100;
  const freight = Number(state['freight'].value || 0);
  const rate = Number(state['rate'].value || 6.8);
  if (!brand && !state['power'].value && !term) {{
    state['rows'].innerHTML = '<tr><td colspan="16" style="text-align:center;color:#999;padding:20px;">请选择发动机品牌或输入功率进行筛选</td></tr>';
    state['count'].textContent = '';
    window.currentRows = [];
    return;
  }}
  let rows = records.filter(row => {{
    if (brand && row.brand !== brand) return false;
    if (state['power'].value && Math.abs(Number(row.genset_kw) - power) > tolerance) return false;
    if (term && !(row.model + ' ' + (row.section || '') + ' ' + row.brand).toLowerCase().includes(term)) return false;
    return true;
  }}).sort((a, b) => a.genset_kw - b.genset_kw || a.brand.localeCompare(b.brand));
  window.currentRows = rows;
  state['count'].textContent = `${{rows.length}} matching rows`;
  state['rows'].innerHTML = rows.slice(0, 500).map(row => {{
    const selectedAlt = findAlternator(alternatorBrand, row.genset_kw);
    const selectedCanopy = useCanopy ? findCanopy(state['canopy'].value, row.genset_kw) : null;
    const defaultAlt = Number(row.default_alternator_price || 0);
    const selectedAltPrice = selectedAlt ? Number(selectedAlt.price || 0) : 0;
    const canopyPrice = selectedCanopy ? Number(selectedCanopy.price || 0) : 0;
    const canopyDeduct = (selectedCanopy && selectedCanopy.deduct) ? Number(row.assembly_cost || 0) + Number(row.silencer_cost || 0) : 0;
    const baseCost = Number(row.cost_calculated || row.cost_book || 0);
    const adjustedCost = baseCost - (selectedAlt ? defaultAlt : 0) + (selectedAlt ? selectedAltPrice : 0) - canopyDeduct + (selectedCanopy ? canopyPrice : 0) + freight;
    const adjusted = Boolean(selectedAlt || selectedCanopy || freight);
    const cost = adjusted ? adjustedCost : (row.cost_book || row.cost_calculated);
    const factory = adjusted ? adjustedCost * 1.10 : (row.factory_floor_book || row.factory_floor_calculated);
    const custom = Number(cost || 0) * (1 + markup);
    const rowJson = encodeURIComponent(JSON.stringify(row));
    const h = v => String(v == null ? '' : v).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    return '<tr data-row="' + rowJson + '"><td>' + h(row.brand) + '</td><td>' + h(row.section || '') + '</td><td>' + h(row.model) + '</td>' +
      '<td>' + h(row.engine_power || '') + '</td><td class="num">' + (row.engine_price ? money(row.engine_price) : '') + '</td><td>' + h(row.genset_power) + '</td>' +
      '<td class="num">' + (defaultAlt ? money(defaultAlt) : '') + '</td>' +
      '<td>' + (selectedAlt ? (selectedAlt.brand + ' / ' + selectedAlt.model + ' (' + selectedAlt.power_kw + 'kW)') : '') + '</td>' +
      '<td class="num">' + (selectedAlt ? money(selectedAltPrice) : '') + '</td>' +
      '<td>' + (selectedCanopy ? (selectedCanopy.power_text + ' / ' + selectedCanopy.size) : '') + '</td>' +
      '<td class="num">' + (selectedCanopy ? money(canopyPrice) : '') + '</td>' +
      '<td class="num">' + (selectedCanopy && selectedCanopy.deduct ? money(canopyDeduct) : '') + '</td>' +
      '<td class="num">' + (freight ? money(freight) : '') + '</td>' +
      '<td class="num"><span class="cv" data-v="' + money(cost) + '"><span class="cp">Copy</span>' + money(cost) + '</span></td>' +
      '<td class="num"><span class="cv" data-v="' + money(custom) + '"><span class="cp">Copy</span>' + money(custom) + '</span></td>' +
      '<td class="num"><span class="cv" data-v="' + (Number(custom) / rate).toFixed(0) + '"><span class="cp">Copy</span>' + (Number(custom) / rate).toFixed(0) + '</span></td>' +
      '<td>' + h(row.source_sheet) + '!' + h(row.source_row) + '</td></tr>';
  }}).join('');
  renderAlternators();
}}
function renderAlternators() {{
  const altPower = Number(altState.power.value);
  const altTolerance = Number(altState.tolerance.value || 0);
  const altTerm = altState.search.value.trim().toLowerCase();
  const altMarkup = Number(altState.markup.value || 0) / 100;
  let altRows = alternatorRecords.filter(row => {{
    if (row.brand !== altState.brand.value) return false;
    if (altState.power.value && Math.abs(Number(row.power_kw) - altPower) > altTolerance) return false;
    if (altTerm && !(row.model + ' ' + row.brand).toLowerCase().includes(altTerm)) return false;
    return true;
  }}).sort((a, b) => Number(a.power_kw) - Number(b.power_kw) || a.brand.localeCompare(b.brand));
  window.currentAlternatorRows = altRows;
  altState.count.textContent = `${{altRows.length}} matching rows`;
  altState.rows.innerHTML = altRows.slice(0, 500).map(row => {{
    const custom = Number(row.price || 0) * (1 + altMarkup);
    const p = v => v == null || v === '' ? '' : String(v);
    return '<tr><td>' + p(row.brand) + '</td><td>' + p(row.model) + '</td><td class="num">' + (row.price ? Number(row.price).toFixed(0) : '') + '</td><td class="num">' + Number(custom).toFixed(0) + '</td><td>' + p(row.source_sheet) + '!' + p(row.source_col) + p(row.source_row) + '</td></tr>';
  }}).join('');
}}
document.getElementById('reset').addEventListener('click', () => {{
  state['brand'].value = ''; state['power'].value = ''; state['tolerance'].value = '0'; state['gensetAltBrand'].value = ''; state['canopy'].value = ''; state['freight'].value = '0'; state['rate'].value = '6.8'; state['search'].value = ''; state['markup'].value = '0'; render(); renderAlternators();
}});
document.getElementById('copy').addEventListener('click', async () => {{
  const selRow = document.querySelector('table.genset tr.selected');
  if (selRow && selRow.dataset.row) {{
    const r = JSON.parse(selRow.dataset.row);
    const rate = Number(state['rate'].value || 6.8);
    const markup = Number(state['markup'].value || 0) / 100;
    const alternatorBrand = state['gensetAltBrand'].value;
    const selectedAlt = findAlternator(alternatorBrand, r.genset_kw);
    const freight = Number(state['freight'].value || 0);
    const baseCost = Number(r.cost_calculated || r.cost_book || 0);
    const defaultAlt = Number(r.default_alternator_price || 0);
    const selectedAltPrice = selectedAlt ? Number(selectedAlt.price || 0) : 0;
    const adjustedCost = baseCost - (selectedAlt ? defaultAlt : 0) + selectedAltPrice + freight;
    const adjusted = Boolean(selectedAlt || freight);
    const factory = adjusted ? adjustedCost * 1.10 : Number(r.factory_floor_book || r.factory_floor_calculated || 0);
    const custom = Number(cost || 0) * (1 + markup);
    const usd = (Number(custom) / rate).toFixed(0);
    const dict = {{
      "ENGINE MODEL": r.model,
      "ENGINE POWER": r.engine_power || '',
      "GENSET POWER": r.genset_power,
      "USD": usd
    }};
    await navigator.clipboard.writeText(JSON.stringify(dict, null, 2));
    const btn = document.getElementById('copy');
    btn.textContent = 'Copied';
    setTimeout(() => {{ btn.textContent = 'Copy'; }}, 1200);
    return;
  }}
  const markup = Number(state['markup'].value || 0) / 100;
  const freight = Number(state['freight'].value || 0);
  const rows = (window.currentRows || []).slice(0, 500);
  const alternatorBrand = state['gensetAltBrand'].value;
  const useCanopy = Boolean(state['canopy'].value);
  const rate = Number(state['rate'].value || 6.8);
  const tab = String.fromCharCode(9);
  const nl = String.fromCharCode(10);
  const lines = [['Brand','Section','Model','Engine Power','Engine Price','Genset Power','Default Alt','Selected Alt','Alt Price','Silent Box','Box Price','Deduct','Freight','Cost','Sales','USD','Source'].join(tab)];
  rows.forEach(row => {{
    const selectedAlt = findAlternator(alternatorBrand, row.genset_kw);
    const selectedCanopy = useCanopy ? findCanopy(state['canopy'].value, row.genset_kw) : null;
    const defaultAlt = Number(row.default_alternator_price || 0);
    const selectedAltPrice = selectedAlt ? Number(selectedAlt.price || 0) : 0;
    const canopyPrice = selectedCanopy ? Number(selectedCanopy.price || 0) : 0;
    const canopyDeduct = (selectedCanopy && selectedCanopy.deduct) ? Number(row.assembly_cost || 0) + Number(row.silencer_cost || 0) : 0;
    const baseCost = Number(row.cost_calculated || row.cost_book || 0);
    const adjustedCost = baseCost - (selectedAlt ? defaultAlt : 0) + (selectedAlt ? selectedAltPrice : 0) - canopyDeduct + (selectedCanopy ? canopyPrice : 0) + freight;
    const adjusted = Boolean(selectedAlt || selectedCanopy || freight);
    const cost = adjusted ? adjustedCost : Number(row.cost_book || row.cost_calculated || 0);
    const factory = adjusted ? adjustedCost * 1.10 : Number(row.factory_floor_book || row.factory_floor_calculated || 0);
    const custom = Number(cost || 0) * (1 + markup);
    lines.push([
      row.brand,
      row.section || '',
      row.model,
      row.engine_power || '',
      row.engine_price ? Number(row.engine_price).toFixed(0) : '',
      row.genset_power,
      defaultAlt ? defaultAlt.toFixed(0) : '',
      selectedAlt ? (selectedAlt.brand + ' / ' + selectedAlt.model + ' (' + selectedAlt.power_kw + 'kW)') : '',
      selectedAlt ? selectedAltPrice.toFixed(0) : '',
      selectedCanopy ? (selectedCanopy.power_text + ' / ' + selectedCanopy.size) : '',
      selectedCanopy ? canopyPrice.toFixed(0) : '',
      selectedCanopy && selectedCanopy.deduct ? canopyDeduct.toFixed(0) : '',
      freight ? freight.toFixed(0) : '',
      Number(cost).toFixed(0),
      custom.toFixed(0),
      (Number(custom) / rate).toFixed(0),
      row.source_sheet + '!' + row.source_row
    ].join(tab));
  }});
  await navigator.clipboard.writeText(lines.join(nl));
  const btn = document.getElementById('copy');
  btn.textContent = 'Copied';
  setTimeout(() => {{ btn.textContent = 'Copy'; }}, 1200);
}});
document.getElementById('altReset').addEventListener('click', () => {{
  altState['brand'].value = ''; altState['power'].value = ''; altState['tolerance'].value = '0'; altState['search'].value = ''; altState['markup'].value = '0'; renderAlternators();
}});
document.getElementById('altCopy').addEventListener('click', async () => {{
  const markup = Number(altState.markup.value || 0) / 100;
  const rows = (window.currentAlternatorRows || []).slice(0, 500);
  const tab = String.fromCharCode(9);
  const nl = String.fromCharCode(10);
  const lines = [['Brand','Model','Power kW','Price','Sales','Source'].join(tab)];
  rows.forEach(row => {{
    const custom = Number(row.price || 0) * (1 + markup);
    lines.push([
      row.brand,
      row.model,
      row.power_kw,
      Number(row.price || 0).toFixed(0),
      custom.toFixed(0),
      row.source_sheet + '!' + row.source_col + row.source_row
    ].join(tab));
  }});
  await navigator.clipboard.writeText(lines.join(nl));
  document.getElementById('altCopy').textContent = 'Copied';
  setTimeout(() => document.getElementById('altCopy').textContent = 'Copy alternator prices', 1200);
}});
state.rows.innerHTML = '<tr><td colspan="16" style="text-align:center;color:#999;padding:20px;">请选择发动机品牌或输入功率进行筛选</td></tr>';
altState.rows.innerHTML = '';
</script>
</body>
</html>
""",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build genset pricing outputs from xlsx.")
    parser.add_argument("--xlsx", default="price_list_genset.xlsx", help="source workbook")
    parser.add_argument("--alternator-xlsx", default="price_list_alternator.xlsx", help="alternator workbook")
    parser.add_argument("--out-dir", default=".", help="output directory")
    args = parser.parse_args()

    xlsx_path = Path(args.xlsx)
    alternator_xlsx_path = Path(args.alternator_xlsx)
    out_dir = Path(args.out_dir)
    records = extract_records(xlsx_path)
    alternator_records = extract_alternator_records(alternator_xlsx_path)
    canopy_records = extract_canopy_records(xlsx_path)
    write_csv(records, out_dir / "genset_price_catalog.csv")
    write_json(records, out_dir / "genset_price_catalog.json")
    write_alternator_csv(alternator_records, out_dir / "alternator_price_catalog.csv")
    write_json(alternator_records, out_dir / "alternator_price_catalog.json")
    write_canopy_csv(canopy_records, out_dir / "canopy_price_catalog.csv")
    write_json(canopy_records, out_dir / "canopy_price_catalog.json")
    write_html(records, alternator_records, canopy_records, out_dir / "genset_price_calculator.html")
    print(f"Extracted {len(records)} price rows")
    print(f"Extracted {len(alternator_records)} alternator rows")
    print(f"Extracted {len(canopy_records)} canopy rows")
    print("Wrote genset_price_catalog.csv")
    print("Wrote genset_price_catalog.json")
    print("Wrote alternator_price_catalog.csv")
    print("Wrote alternator_price_catalog.json")
    print("Wrote canopy_price_catalog.csv")
    print("Wrote canopy_price_catalog.json")
    print("Wrote genset_price_calculator.html")


if __name__ == "__main__":
    main()

