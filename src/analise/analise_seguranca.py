from __future__ import annotations

import argparse
import re
import unicodedata
from pathlib import Path

import folium
import pandas as pd
from folium.plugins import HeatMap


CSV_SEPARATOR = ";"


def find_root() -> Path:
    for path in [Path.cwd(), *Path.cwd().parents]:
        if (path / ".git").exists():
            return path
    return Path.cwd()


def normalizar_coluna(value: object) -> str:
    text = "" if pd.isna(value) else str(value)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^A-Za-z0-9]+", " ", text).strip().upper()
    return re.sub(r"\s+", " ", text)


def coluna(df: pd.DataFrame, nome_normalizado: str) -> str:
    for column in df.columns:
        if normalizar_coluna(column) == nome_normalizado:
            return column
    raise KeyError(f"Coluna nao encontrada: {nome_normalizado}")


def read_csv_flex(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, sep=None, engine="python", encoding="utf-8-sig")


def formatar_dado(row: pd.Series) -> str:
    ocorrencias = int(row["ocorrencias"])
    baleados = int(row["baleados"])
    palavra_ocorrencia = "ocorrencia" if ocorrencias == 1 else "ocorrencias"
    palavra_baleado = "baleado" if baleados == 1 else "baleados"
    return f"{ocorrencias} {palavra_ocorrencia} e {baleados} {palavra_baleado}"


def calcular_notas(df: pd.DataFrame, bairros_referencia: pd.Series) -> pd.DataFrame:
    agregada = (
        df.groupby("bairro", as_index=False)
        .agg(
            ocorrencias=("id", "nunique"),
            mortos=("mortos", "sum"),
            feridos=("feridos", "sum"),
            baleados=("baleados", "sum"),
            acoes_policiais=("acao_policial", "sum"),
            chacinas=("chacina", "sum"),
        )
    )

    base = pd.DataFrame({"bairro": bairros_referencia})
    base = base.merge(agregada, on="bairro", how="left").fillna(0)

    numeric_cols = ["ocorrencias", "mortos", "feridos", "baleados", "acoes_policiais", "chacinas"]
    for col in numeric_cols:
        base[col] = base[col].astype(int)

    base["indice_risco"] = (
        base["ocorrencias"]
        + (2 * base["mortos"])
        + base["feridos"]
        + (0.5 * base["acoes_policiais"])
        + (3 * base["chacinas"])
    )

    min_risco = base["indice_risco"].min()
    max_risco = base["indice_risco"].max()
    if max_risco == min_risco:
        base["nota_dimensao"] = 10.0
    else:
        base["nota_dimensao"] = 10 - ((base["indice_risco"] - min_risco) / (max_risco - min_risco) * 10)

    base["nota_dimensao"] = base["nota_dimensao"].round(2)
    base["dado_principal"] = base.apply(formatar_dado, axis=1)
    return base.sort_values(["nota_dimensao", "bairro"], ascending=[False, True])


def gerar_mapa_hotspots(df: pd.DataFrame, output_path: Path) -> None:
    mapa_df = df[(df["latitude"].notna()) & (df["longitude"].notna())].copy()
    mapa_df = mapa_df[(mapa_df["latitude"] != 0) & (mapa_df["longitude"] != 0)]

    if mapa_df.empty:
        return

    center = [mapa_df["latitude"].mean(), mapa_df["longitude"].mean()]
    mapa = folium.Map(location=center, zoom_start=12, tiles="cartodbpositron")

    heat_data = mapa_df[["latitude", "longitude", "baleados"]].copy()
    heat_data["peso"] = heat_data["baleados"].clip(lower=1)

    HeatMap(
        heat_data[["latitude", "longitude", "peso"]].values.tolist(),
        radius=16,
        blur=22,
        min_opacity=0.25,
    ).add_to(mapa)

    top_ocorrencias = mapa_df.sort_values(["baleados", "mortos"], ascending=False).head(40)
    for _, row in top_ocorrencias.iterrows():
        popup = (
            f"<strong>{row['bairro']}</strong><br>"
            f"{row['motivo_principal']}<br>"
            f"Mortos: {int(row['mortos'])} | Feridos: {int(row['feridos'])}<br>"
            f"{row['data_ocorrencia']}"
        )
        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=4 + min(int(row["baleados"]), 8),
            color="#7f1d1d",
            fill=True,
            fill_color="#ef4444",
            fill_opacity=0.72,
            popup=folium.Popup(popup, max_width=320),
        ).add_to(mapa)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    mapa.save(output_path)


def gerar_contexto_sds(raw_dir: Path, output_path: Path, year: int) -> None:
    cvli_path = raw_dir / "microdados_cvli.xlsx"
    cvp_path = raw_dir / "microdados_cvp.xlsx"
    rows: list[dict[str, object]] = []

    if cvli_path.exists():
        cvli = pd.read_excel(cvli_path, sheet_name="Plan1")
        col_municipio = coluna(cvli, "MUNICIPIO")
        col_ano = coluna(cvli, "ANO")
        col_total = coluna(cvli, "TOTAL DE VITIMAS")
        cvli_recife = cvli[
            (cvli[col_municipio].astype(str).str.upper() == "RECIFE")
            & (pd.to_numeric(cvli[col_ano], errors="coerce") == year)
        ]
        rows.append(
            {
                "fonte": "SDS-PE",
                "indicador": "CVLI",
                "ano": year,
                "municipio": "Recife",
                "total": int(pd.to_numeric(cvli_recife[col_total], errors="coerce").fillna(0).sum()),
            }
        )

    if cvp_path.exists():
        cvp = pd.read_excel(cvp_path, sheet_name="microdados cvp")
        col_municipio = coluna(cvp, "MUNICIPIO")
        col_ano = coluna(cvp, "ANO")
        col_total = coluna(cvp, "TOTAL")
        cvp_recife = cvp[
            (cvp[col_municipio].astype(str).str.upper() == "RECIFE")
            & (pd.to_numeric(cvp[col_ano], errors="coerce") == year)
        ]
        rows.append(
            {
                "fonte": "SDS-PE",
                "indicador": "CVP",
                "ano": year,
                "municipio": "Recife",
                "total": int(pd.to_numeric(cvp_recife[col_total], errors="coerce").fillna(0).sum()),
            }
        )

    if rows:
        pd.DataFrame(rows).to_csv(output_path, index=False, sep=CSV_SEPARATOR, encoding="utf-8-sig")


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera notas e mapa da dimensao seguranca.")
    parser.add_argument("--year", type=int, default=2025)
    args = parser.parse_args()

    root = find_root()
    processed_dir = root / "data" / "processed"
    docs_dir = root / "docs"

    ocorrencias_path = processed_dir / "ocorrencias_seguranca_recife.csv"
    bairros_referencia_path = processed_dir / "notas_renda.csv"
    bairros_referencia = read_csv_flex(bairros_referencia_path)["bairro"]

    df = read_csv_flex(ocorrencias_path)
    for col in ["latitude", "longitude", "mortos", "feridos", "baleados"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    notas = calcular_notas(df, bairros_referencia)
    notas_saida = notas[["bairro", "nota_dimensao", "dado_principal"]]

    notas_saida.to_csv(processed_dir / "notas_seguranca.csv", index=False, sep=CSV_SEPARATOR, encoding="utf-8-sig")
    notas.to_csv(processed_dir / "recife_seguranca_bairros.csv", index=False, sep=CSV_SEPARATOR, encoding="utf-8-sig")
    notas.to_csv(processed_dir / "seguranca_por_bairro.csv", index=False, sep=CSV_SEPARATOR, encoding="utf-8-sig")

    gerar_mapa_hotspots(df, docs_dir / "mapa_hotspots_seguranca.html")
    gerar_contexto_sds(
        root / "data" / "raw" / "seguranca",
        processed_dir / "seguranca_contexto_sds_recife_2025.csv",
        args.year,
    )
    try:
        notas_saida.to_csv(processed_dir / "notas_seguran\u00e7a.csv", index=False, sep=CSV_SEPARATOR, encoding="utf-8-sig")
    except PermissionError as exc:
        raise SystemExit(
            "Nao foi possivel substituir data/processed/notas_seguran\u00e7a.csv. "
            "Feche esse CSV no Excel/VSCode/OneDrive e execute a analise novamente."
        ) from exc

    print(f"Bairros no notas_seguranca.csv: {len(notas_saida)}")
    print(f"Maior risco: {notas.sort_values('indice_risco', ascending=False).iloc[0]['bairro']}")
    print("Arquivo salvo em: data/processed/notas_seguran\u00e7a.csv")


if __name__ == "__main__":
    main()
