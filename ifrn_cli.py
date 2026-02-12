#!/usr/bin/env python3
"""Consulta simples no terminal por inscricao."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

DEFAULT_CSV = Path("data/ifrn_2026_resultado.csv")


def normalize_inscricao(value: str) -> str:
    digits = re.sub(r"\D", "", value or "")
    if len(digits) >= 8:
        return f"{digits[:7]}-{digits[7]}"
    return value.strip()


def load_matches(csv_path: Path, inscricao: str) -> list[dict[str, str]]:
    wanted = normalize_inscricao(inscricao)
    matches: list[dict[str, str]] = []
    with csv_path.open("r", encoding="utf-8", newline="") as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            if normalize_inscricao(row.get("inscricao", "")) == wanted:
                matches.append(row)
    return matches


def print_result(rows: list[dict[str, str]]) -> None:
    if not rows:
        print("Inscricao nao encontrada.")
        return

    print(f"Encontrado: {len(rows)} registro(s)")
    for idx, row in enumerate(rows, start=1):
        print("")
        print(f"[{idx}] Inscricao: {row.get('inscricao', '')}")
        print(f"Nome: {row.get('nome', '')}")
        print(f"Curso: {row.get('curso', '')}")
        print(f"Escola/Campus: {row.get('campus', '')}")
        print(f"Turno: {row.get('turno', '')}")
        print(f"Lista: {row.get('lista', '')}")
        print(f"Classificacao: {row.get('classificacao', '')}")
        print(f"Situacao: {row.get('situacao', '')}")
        print(f"Escore Final: {row.get('escore_final', '')}")
        print(f"Escore Final Bonificado: {row.get('escore_final_bonificado', '')}")
        print(f"Redacao: {row.get('redacao', '')}")
        print(f"Escore Portugues: {row.get('escore_portugues', '')}")
        print(f"Escore Matematica: {row.get('escore_matematica', '')}")
        print(
            "Escore Portugues Bonificado: "
            f"{row.get('escore_portugues_bonificado', '')}"
        )
        print(
            "Escore Matematica Bonificado: "
            f"{row.get('escore_matematica_bonificado', '')}"
        )
        print(f"Pagina PDF: {row.get('pagina_pdf', '')}")


def run_interactive(csv_path: Path) -> None:
    print("Modo interativo. Digite a inscricao (ou 'sair').")
    while True:
        raw = input("> ").strip()
        if raw.lower() in {"sair", "exit", "quit"}:
            return
        if not raw:
            continue
        rows = load_matches(csv_path, raw)
        print_result(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Consulta simples do IFRN 2026.")
    parser.add_argument(
        "--csv",
        type=Path,
        default=DEFAULT_CSV,
        help="Caminho do CSV gerado pelo parser.",
    )
    parser.add_argument(
        "--inscricao",
        type=str,
        default=None,
        help="Inscricao para consulta direta.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if not args.csv.exists():
        raise SystemExit(f"CSV nao encontrado: {args.csv}")
    if args.inscricao:
        print_result(load_matches(args.csv, args.inscricao))
    else:
        run_interactive(args.csv)
