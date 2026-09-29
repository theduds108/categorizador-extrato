"""
Categorizador de Extrato Bancário — interface Streamlit.
"""

from pathlib import Path

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from categorizador import carregar_extrato, formatar_moeda

EXEMPLO = Path(__file__).parent / "sample_data" / "extrato_exemplo.csv"

MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]

PALETA = ["#1d4ed8", "#0891b2", "#059669", "#d97706", "#dc2626", "#7c3aed", "#db2777", "#475569"]

st.set_page_config(page_title="Categorizador de Extrato", layout="wide")

st.markdown(
    """
    <style>
      .block-container { padding-top: 2.5rem; max-width: 1200px; }
      h1 { font-weight: 600; letter-spacing: -0.02em; }
      [data-testid="stMetric"] {
          background: #ffffff; border: 1px solid #e4e7ec; border-radius: 8px; padding: 16px 20px;
      }
      [data-testid="stMetricLabel"] p { color: #475467; font-size: 0.85rem; }
      #MainMenu, footer, [data-testid="stToolbar"] { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)


def estilizar(fig: go.Figure) -> go.Figure:
    fig.update_layout(
        font=dict(family="Inter, system-ui, sans-serif", size=13, color="#344054"),
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=8, r=8, t=8, b=8),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title_text=""),
        hoverlabel=dict(bgcolor="white", font_size=12),
        separators=",.",
        height=380,
    )
    fig.update_xaxes(showgrid=False, linecolor="#e4e7ec")
    fig.update_yaxes(gridcolor="#f2f4f7", zeroline=False)
    return fig


# ---------- Sidebar ----------

with st.sidebar:
    st.subheader("Extrato")
    arquivo = st.file_uploader(
        "Arquivo CSV", type=["csv"], help="Colunas obrigatórias: data, descricao, valor"
    )
    st.caption("Sem arquivo, o painel usa um extrato de exemplo com três meses de movimentação.")

# ---------- Dados ----------

try:
    df = carregar_extrato(arquivo if arquivo is not None else EXEMPLO)
except ValueError as erro:
    st.error(str(erro))
    st.stop()

if df.empty:
    st.warning("Nenhuma transação válida encontrada no arquivo.")
    st.stop()

gastos = df[df["valor"] < 0].assign(valor_abs=lambda d: d["valor"].abs())
receitas = df[df["valor"] > 0]

# ---------- Cabeçalho ----------

st.title("Categorizador de Extrato")
inicio, fim = df["data"].min(), df["data"].max()
st.caption(f"Período analisado: {inicio:%d/%m/%Y} a {fim:%d/%m/%Y} · {len(df)} transações")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Entradas", formatar_moeda(receitas["valor"].sum()))
c2.metric("Saídas", formatar_moeda(gastos["valor_abs"].sum()))
c3.metric("Saldo do período", formatar_moeda(df["valor"].sum()))
maior = gastos.groupby("categoria")["valor_abs"].sum().idxmax() if not gastos.empty else "—"
c4.metric("Maior categoria de gasto", maior)

st.write("")

# ---------- Gráficos ----------

col_a, col_b = st.columns([5, 7], gap="large")

with col_a:
    st.markdown("**Gastos por categoria**")
    por_categoria = (
        gastos.groupby("categoria")["valor_abs"].sum().sort_values().reset_index()
    )
    fig = px.bar(
        por_categoria, x="valor_abs", y="categoria", orientation="h",
        color_discrete_sequence=[PALETA[0]],
        labels={"valor_abs": "", "categoria": ""},
    )
    fig.update_traces(
        hovertemplate="%{y}: R$ %{x:,.2f}<extra></extra>",
        texttemplate="R$ %{x:,.0f}", textposition="outside", cliponaxis=False,
    )
    fig.update_xaxes(showticklabels=False, range=[0, por_categoria["valor_abs"].max() * 1.28])
    st.plotly_chart(estilizar(fig), use_container_width=True, config={"displayModeBar": False})

with col_b:
    st.markdown("**Evolução mensal por categoria**")
    por_mes = gastos.groupby(["mes", "categoria"])["valor_abs"].sum().reset_index()
    por_mes["rotulo_mes"] = por_mes["mes"].apply(lambda d: f"{MESES[d.month - 1]}/{d:%y}")
    fig = px.bar(
        por_mes, x="rotulo_mes", y="valor_abs", color="categoria",
        color_discrete_sequence=PALETA,
        labels={"valor_abs": "", "rotulo_mes": "", "categoria": ""},
    )
    fig.update_traces(hovertemplate="%{fullData.name}: R$ %{y:,.2f}<extra></extra>")
    fig.update_yaxes(tickprefix="R$ ", tickformat=",.0f")
    st.plotly_chart(estilizar(fig), use_container_width=True, config={"displayModeBar": False})

# ---------- Tabela ----------

st.markdown("**Transações**")

categorias = sorted(df["categoria"].unique())
filtro = st.multiselect("Filtrar categorias", categorias, placeholder="Todas as categorias")
tabela = df if not filtro else df[df["categoria"].isin(filtro)]

st.dataframe(
    tabela[["data", "descricao", "categoria", "valor"]].sort_values("data", ascending=False),
    use_container_width=True,
    hide_index=True,
    column_config={
        "data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
        "descricao": st.column_config.TextColumn("Descrição"),
        "categoria": st.column_config.TextColumn("Categoria"),
        "valor": st.column_config.NumberColumn("Valor (R$)", format="%.2f"),
    },
)

st.download_button(
    "Exportar extrato categorizado (CSV)",
    df.drop(columns=["mes"]).to_csv(index=False).encode("utf-8"),
    file_name="extrato_categorizado.csv",
    mime="text/csv",
)
