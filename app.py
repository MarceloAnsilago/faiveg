from datetime import date
import base64
import html as html_lib
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


st.set_page_config(
    page_title="FAI Vegetal | Impressao",
    layout="wide",
)


st.markdown(
    """
    <style>
    :root {
        --ink: #1f2933;
        --muted: #5d6875;
        --line: #d6dde5;
        --panel: #f7f9fb;
        --accent: #276749;
    }

    .block-container {
        padding-top: 1.5rem;
        max-width: 1480px;
    }

    [data-testid="stSidebar"] {
        background: #f6f8fa;
    }

    .screen-header {
        display: flex;
        align-items: end;
        justify-content: space-between;
        gap: 1rem;
        margin-bottom: 1rem;
    }

    .screen-header h1 {
        color: var(--ink);
        font-size: 1.6rem;
        line-height: 1.15;
        margin: 0;
        letter-spacing: 0;
    }

    .screen-header p {
        color: var(--muted);
        margin: 0.25rem 0 0;
    }

    .print-area {
        background: #eef2f5;
        border: 1px solid #d9e0e7;
        padding: 24px;
        overflow-x: auto;
    }

    .print-sheet {
        width: 210mm;
        min-height: 297mm;
        margin: 0 auto;
        padding: 6mm 14mm 14mm;
        background: white;
        color: var(--ink);
        box-shadow: 0 12px 28px rgba(18, 38, 63, 0.16);
        font-family: Arial, Helvetica, sans-serif;
    }

    .doc-top {
        border-bottom: 2px solid #111;
        margin-bottom: 8px;
    }

    .logo-row {
        display: grid;
        grid-template-columns: 1fr 1fr 1fr;
        align-items: center;
        min-height: 22mm;
    }

    .logo-left {
        display: flex;
        justify-content: flex-start;
        align-items: center;
    }

    .logo-center {
        display: flex;
        justify-content: center;
        align-items: center;
    }

    .page-logo {
        width: 22mm;
        height: auto;
        display: block;
    }

    .idaron-logo {
        width: 24mm;
        height: auto;
        display: block;
    }

    .doc-heading {
        border-top: 1px solid #777;
        text-align: center;
        padding-top: 1px;
    }

    .doc-heading h2 {
        color: #111;
        font-family: Verdana, Geneva, sans-serif;
        font-size: 28pt;
        line-height: 1;
        margin: 0;
        letter-spacing: 0;
        font-weight: 800;
        text-transform: uppercase;
    }

    .doc-heading span {
        color: #111;
        display: block;
        font-family: Verdana, Geneva, sans-serif;
        font-size: 6pt;
        line-height: 1;
        font-weight: 700;
        text-transform: uppercase;
    }

    .doc-meta span,
    .field span {
        color: var(--muted);
        font-size: 11px;
        text-transform: uppercase;
    }

    .doc-meta {
        text-align: right;
        font-size: 13px;
    }

    .doc-title {
        background: var(--panel);
        border: 1px solid var(--line);
        padding: 10px 12px;
        margin-bottom: 14px;
    }

    .doc-title h3 {
        margin: 0;
        font-size: 18px;
        letter-spacing: 0;
    }

    .grid-2 {
        display: grid;.doc-heading h2 {
        grid-template-columns: 1fr 1fr;
        gap: 10px;
        margin-bottom: 10px;
    }

    .grid-3 {
        display: grid;
        grid-template-columns: 1fr 1fr 1fr;
        gap: 10px;
        margin-bottom: 10px;
    }

    .field {
        border: 1px solid var(--line);
        padding: 8px 9px;
        min-height: 46px;
    }

    .field strong {
        display: block;
        font-size: 13px;
        margin-top: 3px;
        word-break: break-word;
    }

    .section-title {
        margin: 18px 0 8px;
        font-size: 13px;
        color: var(--accent);
        text-transform: uppercase;
        border-bottom: 1px solid var(--line);
        padding-bottom: 4px;
    }

    .obs-box {
        border: 1px solid var(--line);
        min-height: 120px;
        padding: 10px;
        white-space: pre-wrap;
        font-size: 13px;
    }

    .signature-row {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 28px;
        margin-top: 52px;
    }

    .signature {
        border-top: 1px solid var(--ink);
        text-align: center;
        padding-top: 7px;
        font-size: 12px;
    }

    .print-button iframe {
        height: 46px;
    }

    @media print {
        @page {
            size: A4;
            margin: 0;
        }

        html, body, .stApp {
            background: white !important;
        }

        footer,
        [data-testid="stHeader"],
        [data-testid="stSidebar"],
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        .screen-header,
        .print-button,
        .stAlert {
            display: none !important;
        }

        .block-container {
            padding: 0 !important;
            max-width: none !important;
        }

        .print-area {
            padding: 0 !important;
            border: 0 !important;
            background: white !important;
            overflow: visible !important;
        }

        .print-sheet {
            width: 210mm;
            min-height: 297mm;
            margin: 0;
            padding: 6mm 14mm 14mm;
            box-shadow: none !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def clean(value: object, fallback: str = "-") -> str:
    text = str(value).strip()
    return html_lib.escape(text if text else fallback)


def image_data_uri(path: Path) -> str:
    if not path.exists():
        return ""
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


logo_uri = image_data_uri(Path("assets/logo-cropped.png"))
idaron_logo_uri = image_data_uri(Path("logo idaron.png"))


with st.sidebar:
    st.header("Dados da impressao")

    numero = st.text_input("Numero", value="FAI-0001")
    data_emissao = st.date_input("Data", value=date.today(), format="DD/MM/YYYY")
    responsavel = st.text_input("Responsavel", value="")

    st.divider()
    st.subheader("Identificacao")
    produtor = st.text_input("Produtor / Cliente", value="")
    propriedade = st.text_input("Propriedade", value="")
    municipio = st.text_input("Municipio", value="")
    uf = st.text_input("UF", value="")

    st.divider()
    st.subheader("Area e cultura")
    cultura = st.text_input("Cultura", value="")
    area = st.text_input("Area", value="")
    talhao = st.text_input("Talhao", value="")

    st.divider()
    st.subheader("Conteudo")
    titulo = st.text_input("Titulo do documento", value="Fiscalização do Vazio Sanitário da Soja")
    subtitulo = st.text_input(
        "Subtitulo",
        value="Estabelecida pela Instrução Normativa nº 04/2026/IDARON-PROCFAS",
    )
    observacoes = st.text_area(
        "Observacoes",
        value="",
        height=180,
        placeholder="Digite aqui o conteudo que deve sair na impressao.",
    )


st.markdown(
    """
    <div class="screen-header">
        <div>
            <h1>Pagina de Impressao</h1>
            <p>Preencha os campos na lateral e imprima o documento gerado.</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.container():
    st.markdown('<div class="print-button">', unsafe_allow_html=True)
    components.html(
        """
        <button
            onclick="window.parent.print()"
            style="
                height: 40px;
                padding: 0 16px;
                border: 1px solid #276749;
                background: #276749;
                color: white;
                border-radius: 6px;
                font: 600 14px Arial, sans-serif;
                cursor: pointer;
            "
        >
            Imprimir documento
        </button>
        """,
        height=48,
    )
    st.markdown("</div>", unsafe_allow_html=True)


html = f"""
<div class="print-area">
    <main class="print-sheet">
        <header class="doc-top">
            <div class="logo-row">
                <div class="logo-left">
                    <img class="idaron-logo" src="{idaron_logo_uri}" alt="IDARON">
                </div>
                <div class="logo-center">
                    <img class="page-logo" src="{logo_uri}" alt="Rondonia">
                </div>
                <div></div>
            </div>
            <div class="doc-heading">
                <h2>{clean(titulo)}</h2>
                <span>{clean(subtitulo, "")}</span>
            </div>
        </header>

        <section class="grid-2">
            <div class="field">
                <span>Produtor / Cliente</span>
                <strong>{clean(produtor)}</strong>
            </div>
            <div class="field">
                <span>Propriedade</span>
                <strong>{clean(propriedade)}</strong>
            </div>
        </section>

        <section class="grid-3">
            <div class="field">
                <span>Municipio</span>
                <strong>{clean(municipio)}</strong>
            </div>
            <div class="field">
                <span>UF</span>
                <strong>{clean(uf)}</strong>
            </div>
            <div class="field">
                <span>Responsavel</span>
                <strong>{clean(responsavel)}</strong>
            </div>
        </section>

        <h4 class="section-title">Area e cultura</h4>
        <section class="grid-3">
            <div class="field">
                <span>Cultura</span>
                <strong>{clean(cultura)}</strong>
            </div>
            <div class="field">
                <span>Area</span>
                <strong>{clean(area)}</strong>
            </div>
            <div class="field">
                <span>Talhao</span>
                <strong>{clean(talhao)}</strong>
            </div>
        </section>

        <h4 class="section-title">Observacoes</h4>
        <section class="obs-box">{clean(observacoes, "")}</section>

        <section class="signature-row">
            <div class="signature">Responsavel tecnico</div>
            <div class="signature">Produtor / Representante</div>
        </section>
    </main>
</div>
"""

st.markdown(html, unsafe_allow_html=True)
