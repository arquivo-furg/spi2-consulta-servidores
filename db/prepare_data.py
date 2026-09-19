"""Limpa os arquivos públicos e gera o CSV usado na importação."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path


HEADERS = ("origem", "arquivo_origem", "linha_origem", "nome", "cargo", "orgao", "uf")
# Quantidade de colunas e posições de nome/cargo/órgão/UF nos arquivos de origem.
# Aposentados não fornece UF; nenhuma sigla é inferida para preencher a lacuna.
SOURCE_COLUMNS = {
    "aposentados": (18, 0, 6, 3, None),
    "carreiras": (8, 0, 3, 5, 4),
}


def clean(value: str) -> str:
    return " ".join(value.strip("\x00 \t\r\n").split())


def prepare_file(path: Path, origem: str, writer: csv.writer, seen: set[bytes] | None = None) -> dict[str, int]:
    expected, nome_col, cargo_col, orgao_col, uf_col = SOURCE_COLUMNS[origem]
    counts = {
        "registros_origem": 0,
        "estrutura_invalida": 0,
        "nulos_obrigatorios": 0,
        "uf_invalida": 0,
        "duplicados": 0,
        "tratados": 0,
    }
    if seen is None:
        seen = set()

    with path.open("r", encoding="latin-1", newline="") as source:
        for line_number, raw in enumerate(source, start=1):
            row = next(csv.reader([raw], delimiter=";"))
            if not row or not any(value.strip() for value in row):
                continue
            if origem == "carreiras" and (row[0].startswith("CARREIRA.") or row[0].casefold() == "nome"):
                continue
            # O TXT de carreiras traz um ponto e vírgula extra no fim da linha.
            if origem == "carreiras" and len(row) == expected + 1 and not clean(row[-1]):
                row.pop()

            counts["registros_origem"] += 1
            if len(row) != expected:
                counts["estrutura_invalida"] += 1
                continue

            nome, cargo, orgao = (clean(row[index]) for index in (nome_col, cargo_col, orgao_col))
            uf = clean(row[uf_col]).upper() if uf_col is not None else ""
            if not nome or not cargo or not orgao:
                counts["nulos_obrigatorios"] += 1
                continue
            if uf and (len(uf) != 2 or not uf.isalpha()):
                counts["uf_invalida"] += 1
                continue

            # Detecta repetidos pelos campos aproveitados, sem guardar a linha inteira.
            # Ao reunir os meses, o mesmo registro não deve aparecer uma vez por mês.
            fingerprint = hashlib.blake2b(
                "\0".join((nome, cargo, orgao, uf)).encode("utf-8"), digest_size=16
            ).digest()
            if fingerprint in seen:
                counts["duplicados"] += 1
                continue
            seen.add(fingerprint)

            writer.writerow((origem, path.name, line_number, nome, cargo, orgao, uf))
            counts["tratados"] += 1

    return counts


def source_files(path: Path, prefix: str, suffix: str) -> dict[str, Path]:
    paths = [path] if path.is_file() else sorted(path.glob(f"{prefix}_*.{suffix}"))
    if not paths:
        raise ValueError(f"nenhum arquivo de {prefix} encontrado em {path}")
    months = {}
    for source in paths:
        match = re.fullmatch(rf"{prefix}_((?:0[1-9]|1[0-2])\d{{4}})\.{suffix}", source.name, re.IGNORECASE)
        if not match:
            raise ValueError(f"nome de arquivo inesperado: {source.name}")
        months[match.group(1)] = source
    return months


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aposentados", type=Path, required=True)
    parser.add_argument("--carreiras", type=Path, required=True)
    parser.add_argument("--saida", type=Path, required=True)
    args = parser.parse_args()

    try:
        sources = {
            "aposentados": source_files(args.aposentados, "APOSENTADOS", "csv"),
            "carreiras": source_files(args.carreiras, "CARREIRA", "txt"),
        }
        if sources["aposentados"].keys() != sources["carreiras"].keys():
            raise ValueError("as duas fontes devem cobrir as mesmas competencias; mantenha também os arquivos vazios")
    except ValueError as error:
        parser.error(str(error))
    months = sorted(sources["aposentados"], key=lambda month: month[2:] + month[:2])

    args.saida.parent.mkdir(parents=True, exist_ok=True)
    with args.saida.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.writer(destination)
        writer.writerow(HEADERS)
        seen: set[bytes] = set()
        results = {
            origem: {sources[origem][month].name: prepare_file(sources[origem][month], origem, writer, seen)
                     for month in months}
            for origem in sources
        }
    print(json.dumps({"competencias": months, "arquivos": results}, ensure_ascii=False))


if __name__ == "__main__":
    main()
