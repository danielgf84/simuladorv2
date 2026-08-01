import os
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Simulador RUF - UFPE", layout="wide")

DIMENSOES = ["ensino", "pesquisa", "mercado", "inovacao", "internacionalizacao"]
NOME_UFPE = "UNIVERSIDADE FEDERAL DE PERNAMBUCO"
LABELS_DIMENSOES = {
    "ensino": "Ensino",
    "pesquisa": "Pesquisa",
    "mercado": "Mercado de Trabalho",
    "inovacao": "Inovação",
    "internacionalizacao": "Internacionalização",
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CAMINHO_CSV = os.path.join(BASE_DIR, "..", "dados", "base_lkv_edicao_atual.csv")


@st.cache_data
def carregar_dados():
    df = pd.read_csv(CAMINHO_CSV)
    df["nota_final"] = df[DIMENSOES].sum(axis=1)
    df = df.sort_values("nota_final", ascending=False).reset_index(drop=True)
    df["posicao"] = df.index + 1
    return df


def simular_ranking_ufpe(variacoes_percentuais, base):
    simulado = base.copy()
    linha_ufpe = simulado["instituicao"] == NOME_UFPE
    for dim, variacao_pct in variacoes_percentuais.items():
        valor_atual = simulado.loc[linha_ufpe, dim].values[0]
        simulado.loc[linha_ufpe, dim] = valor_atual * (1 + variacao_pct / 100)
    simulado["nota_final"] = simulado[DIMENSOES].sum(axis=1)
    simulado = simulado.sort_values("nota_final", ascending=False).reset_index(drop=True)
    simulado["posicao"] = simulado.index + 1
    return simulado


base_lkv = carregar_dados()
linha_ufpe_atual = base_lkv[base_lkv["instituicao"] == NOME_UFPE].iloc[0]

st.title("Simulador de Ranking RUF — UFPE")
st.caption(
    "Simule o impacto de variações de desempenho nas 5 dimensões do "
    "Ranking Universitário Folha (RUF) sobre a posição da UFPE."
)

st.subheader("Situação atual (última edição disponível)")

col_pos, col1, col2, col3, col4, col5 = st.columns(6)
with col_pos:
    st.metric("Posição no RUF", f"{int(linha_ufpe_atual['posicao'])}º")
for col, dim in zip([col1, col2, col3, col4, col5], DIMENSOES):
    with col:
        st.metric(LABELS_DIMENSOES[dim], f"{linha_ufpe_atual[dim]:.2f}")

st.divider()

st.subheader("Defina as variações simuladas")
st.caption(
    "Ajuste o quanto cada dimensão da UFPE variaria (%) em relação à última edição. "
    "Faixa permitida: -20% a +20%."
)

variacoes = {}
sliders_cols = st.columns(5)
for col, dim in zip(sliders_cols, DIMENSOES):
    with col:
        variacoes[dim] = st.slider(
            LABELS_DIMENSOES[dim],
            min_value=-20,
            max_value=20,
            value=0,
            step=1,
            format="%d%%",
            key=f"slider_{dim}",
        )

simular = st.button("Simular", type="primary", use_container_width=True)

if simular:
    resultado = simular_ranking_ufpe(variacoes, base_lkv)
    linha_resultado = resultado[resultado["instituicao"] == NOME_UFPE].iloc[0]
    posicao_simulada = int(linha_resultado["posicao"])
    nota_simulada = float(linha_resultado["nota_final"])
    posicao_atual = int(linha_ufpe_atual["posicao"])
    delta_posicoes = posicao_atual - posicao_simulada

    st.divider()
    st.subheader("Resultado da simulação")

    res_col1, res_col2, res_col3 = st.columns(3)
    with res_col1:
        st.metric(
            "Posição projetada",
            f"{posicao_simulada}º",
            delta=f"{delta_posicoes:+d} posições" if delta_posicoes != 0 else "sem alteração",
        )
    with res_col2:
        st.metric(
            "Nota final projetada",
            f"{nota_simulada:.2f}",
            delta=f"{nota_simulada - linha_ufpe_atual['nota_final']:+.2f}",
        )
    with res_col3:
        st.metric("Posição atual (referência)", f"{posicao_atual}º")

    st.subheader("Top 20 instituições no ranking simulado")

    top20 = resultado.head(20).copy()
    top20_exibir = top20[["posicao", "instituicao", "nota_final"] + DIMENSOES].rename(
        columns={
            "posicao": "Posição",
            "instituicao": "Instituição",
            "nota_final": "Nota Final",
            **LABELS_DIMENSOES,
        }
    )

    def destacar_ufpe(row):
        if row["Instituição"] == NOME_UFPE:
            return ["background-color: #fde68a"] * len(row)
        return [""] * len(row)

    st.dataframe(
        top20_exibir.style.apply(destacar_ufpe, axis=1).format(
            {
                "Nota Final": "{:.2f}",
                "Ensino": "{:.2f}",
                "Pesquisa": "{:.2f}",
                "Mercado de Trabalho": "{:.2f}",
                "Inovação": "{:.2f}",
                "Internacionalização": "{:.2f}",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

    if posicao_simulada > 20:
        st.info(
            f"A UFPE ficou na posição {posicao_simulada}º no cenário simulado, "
            "fora do Top 20 exibido acima."
        )
