from __future__ import annotations

import argparse
import re
import unicodedata
from pathlib import Path

import pandas as pd


ALIASES_BAIRROS = {
    "ALTO SANTA TERESINHA": "ALTO SANTA TEREZINHA",
    "ILHA DE JOANA BEZERRA": "ILHA JOANA BEZERRA",
    "POCO DA PANELA": "POCO",
    "SITIO DOS PINTOS": "SITIO DOS PINTOS SAO BRAS",
    "SITIO DOS PINTOS SAO BRAS": "SITIO DOS PINTOS SAO BRAS",
}
CSV_SEPARATOR = ";"


def find_root() -> Path:
    for path in [Path.cwd(), *Path.cwd().parents]:
        if (path / ".git").exists():
            return path
    return Path.cwd()


def normalizar_texto(value: object) -> str:
    text = "" if pd.isna(value) else str(value)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^A-Za-z0-9]+", " ", text).strip().upper()
    return re.sub(r"\s+", " ", text)


def read_csv_flex(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, sep=None, engine="python", encoding="utf-8-sig")


def periodo_do_dia(hour: int | float | None) -> str:
    if pd.isna(hour):
        return "sem horario"
    hour = int(hour)
    if 0 <= hour < 6:
        return "madrugada"
    if 6 <= hour < 12:
        return "manha"
    if 12 <= hour < 18:
        return "tarde"
    return "noite"


def carregar_mapa_bairros(path_bairros: Path) -> dict[str, str]:
    bairros = read_csv_flex(path_bairros)["bairro"].dropna().astype(str)
    mapping = {normalizar_texto(bairro): bairro for bairro in bairros}
    for origem, destino in ALIASES_BAIRROS.items():
        destino_padrao = mapping.get(normalizar_texto(destino))
        if destino_padrao:
            mapping[normalizar_texto(origem)] = destino_padrao
    return mapping


def main() -> None:
    parser = argparse.ArgumentParser(description="Limpa ocorrencias de seguranca por bairro.")
    parser.add_argument("--year", type=int, default=2025)
    args = parser.parse_args()

    root = find_root()
    raw_path = root / "data" / "raw" / "seguranca" / f"fogo_cruzado_recife_{args.year}.csv"
    output_path = root / "data" / "processed" / "ocorrencias_seguranca_recife.csv"
    unmatched_path = root / "data" / "processed" / "ocorrencias_seguranca_bairros_nao_mapeados.csv"

    df = read_csv_flex(raw_path)
    df = df.drop_duplicates(subset=["id"]).copy()

    df["data_ocorrencia"] = pd.to_datetime(df["data_ocorrencia"], errors="coerce", utc=True)
    df["ano"] = df["data_ocorrencia"].dt.year
    df["mes"] = df["data_ocorrencia"].dt.month
    df["hora"] = df["data_ocorrencia"].dt.hour
    df["periodo"] = df["hora"].apply(periodo_do_dia)

    for col in ["latitude", "longitude", "mortos", "feridos", "baleados"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    mapa_bairros = carregar_mapa_bairros(root / "data" / "processed" / "notas_renda.csv")
    df["bairro_normalizado"] = df["bairro_original"].apply(normalizar_texto)
    df["bairro"] = df["bairro_normalizado"].map(mapa_bairros)
    df["bairro_mapeado"] = df["bairro"].notna()

    nao_mapeados = (
        df.loc[~df["bairro_mapeado"], ["bairro_original", "bairro_normalizado"]]
        .drop_duplicates()
        .sort_values("bairro_original")
    )
    if not nao_mapeados.empty:
        nao_mapeados.to_csv(unmatched_path, index=False, sep=CSV_SEPARATOR, encoding="utf-8-sig")
        print(f"Bairros nao mapeados: {len(nao_mapeados)}")
        print(f"Revise: {unmatched_path.relative_to(root)}")

    df = df[df["bairro_mapeado"]].copy()
    df["motivo_principal"] = df["motivo_principal"].fillna("Nao informado")
    df["ocorrencia_com_vitima"] = df["baleados"] > 0

    keep_cols = [
        "id",
        "documento",
        "bairro",
        "bairro_original",
        "endereco",
        "latitude",
        "longitude",
        "data_ocorrencia",
        "ano",
        "mes",
        "hora",
        "periodo",
        "motivo_principal",
        "motivos_complementares",
        "acao_policial",
        "presenca_agente",
        "chacina",
        "mortos",
        "feridos",
        "baleados",
        "civis_mortos",
        "civis_feridos",
        "agentes_mortos",
        "agentes_feridos",
        "ocorrencia_com_vitima",
    ]
    df[keep_cols].to_csv(output_path, index=False, sep=CSV_SEPARATOR, encoding="utf-8-sig")

    print(f"Ocorrencias limpas: {len(df)}")
    print(f"Arquivo salvo em: {output_path.relative_to(root)}")


if __name__ == "__main__":
    main()
