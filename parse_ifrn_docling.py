#!/usr/bin/env python3
"""Extrai o resultado do IFRN 2026 a partir do PDF usando docling.

Este script evita o pipeline padrão do DocumentConverter (que exige modelos remotos)
e usa o backend local do docling-parse v4 para leitura precisa das células de texto.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

from docling.backend.docling_parse_v4_backend import DoclingParseV4DocumentBackend
from docling.datamodel.base_models import InputFormat
from docling.datamodel.document import InputDocument

INSCRICAO_RE = re.compile(r"^\d{7}-\d$")
CLASSIFICACAO_RE = re.compile(r"^\d+º$")
NUMERIC_RE = re.compile(r"^-?\d+(?:\.\d+)?$")

ROW_TOP_PADDING = 6.0
TABLE_HEADER_CUTOFF_Y = 45.0

OUTPUT_FIELDS = [
    "inscricao",
    "nome",
    "classificacao",
    "situacao",
    "escore_final",
    "escore_final_bonificado",
    "redacao",
    "escore_portugues",
    "escore_matematica",
    "escore_portugues_bonificado",
    "escore_matematica_bonificado",
    "oferta_numero",
    "oferta_texto",
    "curso",
    "forma",
    "campus",
    "turno",
    "lista",
    "pagina_pdf",
]


@dataclass
class Cell:
    text: str
    x: float
    y: float


@dataclass
class PageLayout:
    inscricao_x: float
    nome_x: float
    classificacao_x: float
    situacao_x: float
    score_anchors: list[tuple[str, float]]


def is_inscricao(value: str) -> bool:
    return bool(INSCRICAO_RE.fullmatch(value.strip()))


def is_numeric(value: str) -> bool:
    return bool(NUMERIC_RE.fullmatch(value.strip()))


def is_score_value(value: str) -> bool:
    value = value.strip()
    return value == "-" or is_numeric(value)


def normalize_spaces(value: str) -> str:
    return " ".join(value.split())


def sort_cells(cells: Iterable[Cell]) -> list[Cell]:
    return sorted(cells, key=lambda c: (c.y, c.x))


def parse_oferta(text: str) -> dict[str, str]:
    text = normalize_spaces(text)
    match = re.match(r"^n[ºo]\s*(\d+)\s+(.*)$", text, flags=re.IGNORECASE)
    if not match:
        return {}

    oferta_numero = match.group(1)
    oferta_texto = match.group(2).strip()

    parts = [p.strip() for p in oferta_texto.split(" - ")]
    curso_forma = parts[0] if parts else ""
    campus = parts[1] if len(parts) > 1 else ""
    turno = " - ".join(parts[2:]) if len(parts) > 2 else ""

    curso = curso_forma
    forma = ""
    if ", forma " in curso_forma:
        curso, forma = curso_forma.split(", forma ", 1)

    return {
        "oferta_numero": oferta_numero,
        "oferta_texto": oferta_texto,
        "curso": curso.strip(),
        "forma": forma.strip(),
        "campus": campus.strip(),
        "turno": turno.strip(),
    }


def find_first_x(
    cells: list[Cell], token: str, y_max: float = 170.0, exact: bool = False
) -> Optional[float]:
    token_lower = token.lower()
    for cell in sort_cells(cells):
        if cell.y > y_max:
            continue
        text = cell.text.lower()
        matched = text == token_lower if exact else token_lower in text
        if matched:
            return cell.x
    return None


def find_all_x(
    cells: list[Cell], token: str, y_max: float = 170.0, exact: bool = False
) -> list[float]:
    token_lower = token.lower()
    xs = []
    for c in cells:
        if c.y > y_max:
            continue
        text = c.text.lower()
        matched = text == token_lower if exact else token_lower in text
        if matched:
            xs.append(c.x)
    return sorted(xs)


def detect_layout(cells: list[Cell], previous: Optional[PageLayout]) -> PageLayout:
    inscricao_x = find_first_x(cells, "Inscrição", exact=True)
    nome_x = find_first_x(cells, "Nome", exact=True)
    classificacao_x = find_first_x(cells, "Classificação", exact=True)
    situacao_x = find_first_x(cells, "Situação", exact=True)
    redacao_x = find_first_x(cells, "Redação", exact=True)
    final_x = find_first_x(cells, "Final", exact=True)
    portugues_x = find_first_x(cells, "Português", exact=True)
    matematica_x = find_first_x(cells, "Matemática", exact=True)
    bonificados = find_all_x(cells, "Bonificado", exact=True)

    split_header_mode = (
        final_x is not None
        and portugues_x is not None
        and matematica_x is not None
        and len(bonificados) >= 3
    )

    if split_header_mode:
        score_anchors = [
            ("escore_final", final_x),
            ("escore_final_bonificado", bonificados[0]),
            ("redacao", redacao_x if redacao_x is not None else 0.0),
            ("escore_portugues", portugues_x),
            ("escore_matematica", matematica_x),
            ("escore_portugues_bonificado", bonificados[1]),
            ("escore_matematica_bonificado", bonificados[2]),
        ]
    else:
        escore_final_x = find_first_x(cells, "Escore Final", exact=True)
        escore_final_bon_x = find_first_x(cells, "Escore Final Bonificado", exact=True)
        escore_port_x = find_first_x(cells, "Escore Português", exact=True)
        escore_mat_x = find_first_x(cells, "Escore Matemática", exact=True)
        escore_port_bon_x = find_first_x(
            cells, "Escore Português Bonificado", exact=True
        )
        escore_mat_bon_x = find_first_x(
            cells, "Escore Matemática Bonificado", exact=True
        )
        if (
            escore_final_x is not None
            and escore_final_bon_x is not None
            and redacao_x is not None
            and escore_port_x is not None
            and escore_mat_x is not None
            and escore_port_bon_x is not None
            and escore_mat_bon_x is not None
        ):
            score_anchors = [
                ("escore_final", escore_final_x),
                ("escore_final_bonificado", escore_final_bon_x),
                ("redacao", redacao_x),
                ("escore_portugues", escore_port_x),
                ("escore_matematica", escore_mat_x),
                ("escore_portugues_bonificado", escore_port_bon_x),
                ("escore_matematica_bonificado", escore_mat_bon_x),
            ]
        else:
            score_anchors = []

    if (
        inscricao_x is None
        or nome_x is None
        or classificacao_x is None
        or situacao_x is None
        or redacao_x is None
        or not score_anchors
    ):
        if previous is None:
            raise RuntimeError(
                "Nao foi possivel detectar layout da tabela e nao ha layout anterior."
            )
        return previous
    return PageLayout(
        inscricao_x=inscricao_x,
        nome_x=nome_x,
        classificacao_x=classificacao_x,
        situacao_x=situacao_x,
        score_anchors=score_anchors,
    )


def parse_row_band(
    inscricao: str, row_y: float, row_cells: list[Cell], layout: PageLayout
) -> dict[str, Optional[str]]:
    ordered = sort_cells(row_cells)

    score_min_x = min(x for _, x in layout.score_anchors)
    name_left = layout.nome_x - 8.0
    name_right = layout.classificacao_x - 8.0
    class_left = layout.classificacao_x - 20.0
    class_right = layout.situacao_x - 8.0
    situ_left = layout.situacao_x - 10.0
    situ_right = score_min_x - 6.0

    name_parts = [
        c.text
        for c in ordered
        if name_left <= c.x < name_right and not is_inscricao(c.text)
    ]
    classificacao_parts = [c.text for c in ordered if class_left <= c.x < class_right]
    situacao_parts = [
        c.text
        for c in ordered
        if situ_left <= c.x < situ_right
        and not is_numeric(c.text)
        and not CLASSIFICACAO_RE.fullmatch(c.text)
    ]

    candidate_name = normalize_spaces(" ".join(name_parts))
    classificacao = normalize_spaces(
        " ".join([c for c in classificacao_parts if CLASSIFICACAO_RE.fullmatch(c)])
    )
    situacao = normalize_spaces(" ".join(situacao_parts))

    score_cells = [c for c in ordered if c.x >= score_min_x - 20.0 and is_score_value(c.text)]
    score_names = [score_name for score_name, _ in layout.score_anchors]

    best_scores: dict[str, str] = {}
    score_cells_by_x = sorted(score_cells, key=lambda c: c.x)
    if len(score_cells_by_x) >= 7:
        for score_name, cell in zip(score_names, score_cells_by_x[:7]):
            best_scores[score_name] = cell.text
    else:
        scored_candidates: dict[str, tuple[float, str]] = {}
        for cell in score_cells:
            anchor_name, anchor_x = min(
                layout.score_anchors, key=lambda anchor: abs(cell.x - anchor[1])
            )
            distance = abs(cell.x - anchor_x)
            if distance > 45.0:
                continue
            current = scored_candidates.get(anchor_name)
            candidate_penalty = distance + abs(cell.y - row_y) * 0.25
            if current is None or candidate_penalty < current[0]:
                scored_candidates[anchor_name] = (candidate_penalty, cell.text)
        for score_name in score_names:
            if score_name in scored_candidates:
                best_scores[score_name] = scored_candidates[score_name][1]

    row = {
        "inscricao": inscricao,
        "nome": candidate_name,
        "classificacao": classificacao,
        "situacao": situacao,
    }
    for score_name in score_names:
        raw = best_scores.get(score_name, "")
        row[score_name] = raw
    return row


def extract_rows_from_page(
    cells: list[Cell], layout: PageLayout
) -> list[dict[str, Optional[str]]]:
    inscricao_cells = sort_cells([c for c in cells if is_inscricao(c.text)])
    if not inscricao_cells:
        return []

    rows: list[dict[str, Optional[str]]] = []
    for idx, current in enumerate(inscricao_cells):
        next_y = inscricao_cells[idx + 1].y if idx + 1 < len(inscricao_cells) else math.inf
        row_start = current.y - ROW_TOP_PADDING
        row_end = next_y - ROW_TOP_PADDING
        row_cells = [
            c
            for c in cells
            if row_start <= c.y < row_end and c.y >= TABLE_HEADER_CUTOFF_Y
        ]
        rows.append(parse_row_band(current.text, current.y, row_cells, layout))
    return rows


def run(pdf_path: Path, csv_out: Path, jsonl_out: Path, max_pages: Optional[int]) -> None:
    input_doc = InputDocument(
        path_or_stream=pdf_path,
        format=InputFormat.PDF,
        backend=DoclingParseV4DocumentBackend,
    )
    if not input_doc.valid:
        raise RuntimeError(f"Falha ao abrir PDF: {pdf_path}")

    backend = input_doc._backend
    total_pages = input_doc.page_count
    page_limit = min(total_pages, max_pages) if max_pages else total_pages

    csv_out.parent.mkdir(parents=True, exist_ok=True)
    jsonl_out.parent.mkdir(parents=True, exist_ok=True)

    current_context: dict[str, str] = {}
    current_layout: Optional[PageLayout] = None
    all_rows: list[dict[str, str]] = []

    for page_ix in range(page_limit):
        page = backend.load_page(page_ix)
        raw_cells = list(page.get_text_cells())
        page_cells = []
        for raw in raw_cells:
            box = raw.rect.to_bounding_box()
            text = normalize_spaces(raw.text)
            if not text:
                continue
            page_cells.append(Cell(text=text, x=box.l, y=box.t))

        oferta_cell = next((c for c in page_cells if c.text.startswith("nº ")), None)
        lista_cell = next((c for c in page_cells if c.text.startswith("Lista ")), None)
        current_layout = detect_layout(page_cells, current_layout)

        page_context = dict(current_context)
        if oferta_cell:
            page_context.update(parse_oferta(oferta_cell.text))
        if lista_cell:
            page_context["lista"] = lista_cell.text
        if oferta_cell or lista_cell:
            current_context = dict(page_context)

        page_rows = extract_rows_from_page(page_cells, current_layout)
        for row in page_rows:
            output_row = {field: "" for field in OUTPUT_FIELDS}
            output_row.update(
                {
                    "inscricao": row.get("inscricao", "") or "",
                    "nome": row.get("nome", "") or "",
                    "classificacao": row.get("classificacao", "") or "",
                    "situacao": row.get("situacao", "") or "",
                    "escore_final": row.get("escore_final", "") or "",
                    "escore_final_bonificado": row.get("escore_final_bonificado", "") or "",
                    "redacao": row.get("redacao", "") or "",
                    "escore_portugues": row.get("escore_portugues", "") or "",
                    "escore_matematica": row.get("escore_matematica", "") or "",
                    "escore_portugues_bonificado": row.get("escore_portugues_bonificado", "") or "",
                    "escore_matematica_bonificado": row.get("escore_matematica_bonificado", "") or "",
                    "oferta_numero": page_context.get("oferta_numero", ""),
                    "oferta_texto": page_context.get("oferta_texto", ""),
                    "curso": page_context.get("curso", ""),
                    "forma": page_context.get("forma", ""),
                    "campus": page_context.get("campus", ""),
                    "turno": page_context.get("turno", ""),
                    "lista": page_context.get("lista", ""),
                    "pagina_pdf": str(page_ix + 1),
                }
            )
            all_rows.append(output_row)

        if (page_ix + 1) % 50 == 0 or page_ix + 1 == page_limit:
            print(f"[{page_ix + 1}/{page_limit}] linhas acumuladas: {len(all_rows)}")

        page.unload()

    with csv_out.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(all_rows)

    with jsonl_out.open("w", encoding="utf-8") as fp:
        for row in all_rows:
            fp.write(json.dumps(row, ensure_ascii=False) + "\n")

    missing_names = sum(1 for r in all_rows if not r["nome"])
    missing_score = sum(1 for r in all_rows if not r["escore_final"])
    print(f"Extração concluída. Total de registros: {len(all_rows)}")
    print(f"Sem nome: {missing_names} | Sem escore_final: {missing_score}")
    print(f"CSV: {csv_out}")
    print(f"JSONL: {jsonl_out}")
    backend.unload()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extrai resultado IFRN 2026 com docling.")
    parser.add_argument(
        "--pdf",
        type=Path,
        default=Path(
            "Integrado_IFRN_2026_-_Resultado_Final_-_Lista_de_Classificação.pdf"
        ),
        help="Caminho do PDF.",
    )
    parser.add_argument(
        "--csv-out",
        type=Path,
        default=Path("data/ifrn_2026_resultado.csv"),
        help="Saída CSV.",
    )
    parser.add_argument(
        "--jsonl-out",
        type=Path,
        default=Path("data/ifrn_2026_resultado.jsonl"),
        help="Saída JSONL.",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Limita páginas para teste (opcional).",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run(
        pdf_path=args.pdf,
        csv_out=args.csv_out,
        jsonl_out=args.jsonl_out,
        max_pages=args.max_pages,
    )
