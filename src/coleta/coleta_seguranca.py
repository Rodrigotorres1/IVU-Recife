from __future__ import annotations

import argparse
import os
import time
from pathlib import Path
from typing import Any

import pandas as pd
import requests


API_URL = "https://api-service.fogocruzado.org.br/api/v2"
PUBLIC_API_SECRET = "3x4Aur@ircW4Pg@bOi55w3QOx6BjrLC*f47xV5aGGFtMEfn0^I"

PERNAMBUCO_ID = "813ca36b-91e3-4a18-b408-60b27a1942ef"
RECIFE_ID = "fb1c4e7d-1f61-4a86-b514-d93d533df7a3"

SDS_CVLI_URL = (
    "https://www.sds.pe.gov.br/images/indicadores/CVP/"
    "MICRODADOS_DE_CVLI_JAN_2004_A_ABR_2026.xlsx"
)
SDS_CVP_URL = (
    "https://www.sds.pe.gov.br/images/ESTAT%C3%8DSTICAS/GACE/"
    "Microdados_de_CVP_-_Dispon%C3%ADvel_janeiro_de_2014_a_abril_de_2026.xlsx"
)
CSV_SEPARATOR = ";"


def find_root() -> Path:
    for path in [Path.cwd(), *Path.cwd().parents]:
        if (path / ".git").exists():
            return path
    return Path.cwd()


def get_json(endpoint: str, params: dict[str, Any], api_secret: str) -> dict[str, Any]:
    response = requests.get(
        f"{API_URL}/{endpoint}",
        params=params,
        headers={"x-api-secret": api_secret},
        timeout=60,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("code", 200) >= 400:
        raise RuntimeError(payload)
    return payload


def nested_name(value: Any, key: str = "name") -> str:
    if isinstance(value, dict):
        return str(value.get(key) or "")
    return ""


def summarize_victims(victims: list[dict[str, Any]]) -> dict[str, int]:
    dead = 0
    wounded = 0
    civilians_dead = 0
    civilians_wounded = 0
    agents_dead = 0
    agents_wounded = 0

    for victim in victims:
        situation = str(victim.get("situation") or "").lower()
        person_type = str(victim.get("personType") or "").lower()

        is_dead = situation == "dead"
        is_wounded = situation == "wounded"
        is_agent = "agent" in person_type

        dead += int(is_dead)
        wounded += int(is_wounded)
        civilians_dead += int(is_dead and not is_agent)
        civilians_wounded += int(is_wounded and not is_agent)
        agents_dead += int(is_dead and is_agent)
        agents_wounded += int(is_wounded and is_agent)

    return {
        "mortos": dead,
        "feridos": wounded,
        "baleados": dead + wounded,
        "civis_mortos": civilians_dead,
        "civis_feridos": civilians_wounded,
        "agentes_mortos": agents_dead,
        "agentes_feridos": agents_wounded,
    }


def flatten_occurrence(item: dict[str, Any]) -> dict[str, Any]:
    context = item.get("contextInfo") or {}
    victims = item.get("victims") or []
    victim_counts = summarize_victims(victims)

    complementary = context.get("complementaryReasons") or []
    clippings = context.get("clippings") or []

    return {
        "id": item.get("id"),
        "documento": item.get("documentNumber"),
        "endereco": item.get("address"),
        "estado": nested_name(item.get("state")),
        "regiao": nested_name(item.get("region"), "region"),
        "cidade": nested_name(item.get("city")),
        "bairro_original": nested_name(item.get("neighborhood")),
        "sub_bairro": nested_name(item.get("subNeighborhood")),
        "localidade": nested_name(item.get("locality")),
        "latitude": item.get("latitude"),
        "longitude": item.get("longitude"),
        "data_ocorrencia": item.get("date"),
        "acao_policial": bool(item.get("policeAction")),
        "presenca_agente": bool(item.get("agentPresence")),
        "motivo_principal": nested_name(context.get("mainReason")),
        "motivos_complementares": " | ".join(nested_name(v) for v in complementary),
        "recortes": " | ".join(nested_name(v) for v in clippings),
        "chacina": bool(context.get("massacre")),
        "unidade_policial": context.get("policeUnit") or "",
        **victim_counts,
    }


def fetch_fogo_cruzado(year: int, api_secret: str, take: int = 200) -> pd.DataFrame:
    all_rows: list[dict[str, Any]] = []
    page = 1

    while True:
        payload = get_json(
            "occurrences",
            params={
                "initialdate": f"{year}-01-01",
                "finaldate": f"{year}-12-31",
                "idState": PERNAMBUCO_ID,
                "idCities": RECIFE_ID,
                "typeOccurrence": "all",
                "page": page,
                "take": take,
            },
            api_secret=api_secret,
        )
        data = payload.get("data") or []
        all_rows.extend(flatten_occurrence(item) for item in data)

        page_meta = payload.get("pageMeta") or {}
        if not page_meta.get("hasNextPage"):
            break

        page += 1
        time.sleep(0.15)

    return pd.DataFrame(all_rows)


def download_file(url: str, output_path: Path, overwrite: bool = False) -> None:
    if output_path.exists() and not overwrite:
        return

    response = requests.get(url, timeout=120)
    response.raise_for_status()
    output_path.write_bytes(response.content)


def main() -> None:
    parser = argparse.ArgumentParser(description="Coleta dados de seguranca para Recife.")
    parser.add_argument("--year", type=int, default=2025, help="Ano completo usado na analise.")
    parser.add_argument("--overwrite", action="store_true", help="Baixa novamente arquivos existentes.")
    args = parser.parse_args()

    root = find_root()
    raw_dir = root / "data" / "raw" / "seguranca"
    raw_dir.mkdir(parents=True, exist_ok=True)

    api_secret = os.getenv("FOGO_CRUZADO_API_SECRET", PUBLIC_API_SECRET)

    download_file(SDS_CVLI_URL, raw_dir / "microdados_cvli.xlsx", overwrite=args.overwrite)
    download_file(SDS_CVP_URL, raw_dir / "microdados_cvp.xlsx", overwrite=args.overwrite)

    ocorrencias = fetch_fogo_cruzado(args.year, api_secret=api_secret)
    output = raw_dir / f"fogo_cruzado_recife_{args.year}.csv"
    ocorrencias.to_csv(output, index=False, sep=CSV_SEPARATOR, encoding="utf-8-sig")

    print(f"Ocorrencias coletadas: {len(ocorrencias)}")
    print(f"Arquivo salvo em: {output.relative_to(root)}")


if __name__ == "__main__":
    main()
