from __future__ import annotations

import base64
from datetime import date
from io import BytesIO
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from reportlab.lib.colors import black, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


st.set_page_config(
    page_title="FAI Vegetal | PDF",
    layout="wide",
)


PAGE_WIDTH, PAGE_HEIGHT = A4
LEFT_MARGIN = 14 * mm
RIGHT_MARGIN = 14 * mm
TOP_MARGIN = 6 * mm
CONTENT_WIDTH = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN

FONT_REGULAR = "Helvetica"
FONT_BOLD = "Helvetica-Bold"


def register_fonts() -> None:
    global FONT_REGULAR, FONT_BOLD

    verdana = Path(r"C:\Windows\Fonts\verdana.ttf")
    verdana_bold = Path(r"C:\Windows\Fonts\verdanab.ttf")

    if verdana.exists() and verdana_bold.exists():
        pdfmetrics.registerFont(TTFont("VerdanaCustom", str(verdana)))
        pdfmetrics.registerFont(TTFont("VerdanaCustom-Bold", str(verdana_bold)))
        FONT_REGULAR = "VerdanaCustom"
        FONT_BOLD = "VerdanaCustom-Bold"


def fit_text(cnv: canvas.Canvas, text: str, font_name: str, max_size: float, min_size: float, width: float) -> float:
    size = max_size
    while size > min_size and pdfmetrics.stringWidth(text, font_name, size) > width:
        size -= 0.25
    return max(size, min_size)


def wrap_text(text: str, font_name: str, font_size: float, width: float) -> list[str]:
    raw = " ".join(str(text or "").split())
    if not raw:
        return [""]

    words = raw.split(" ")
    lines: list[str] = []
    current = words[0]

    for word in words[1:]:
        candidate = f"{current} {word}"
        if pdfmetrics.stringWidth(candidate, font_name, font_size) <= width:
            current = candidate
        else:
            lines.append(current)
            current = word

    lines.append(current)
    return lines


def draw_field(
    cnv: canvas.Canvas,
    x: float,
    top_y: float,
    width: float,
    height: float,
    label: str,
    value: str,
) -> None:
    cnv.rect(x, top_y - height, width, height, stroke=1, fill=0)
    cnv.setFont(FONT_REGULAR, 7)
    cnv.drawString(x + 5, top_y - 9, label.upper())
    cnv.setFont(FONT_BOLD, 9.5)

    text_y = top_y - 23
    for line in wrap_text(value or "-", FONT_BOLD, 9.5, width - 10)[:2]:
        cnv.drawString(x + 5, text_y, line)
        text_y -= 10


def draw_text_block(
    cnv: canvas.Canvas,
    x: float,
    top_y: float,
    width: float,
    height: float,
    text: str,
) -> None:
    cnv.rect(x, top_y - height, width, height, stroke=1, fill=0)
    cnv.setFont(FONT_REGULAR, 9)

    cursor_y = top_y - 14
    for line in wrap_text(text, FONT_REGULAR, 9, width - 10):
        if cursor_y < top_y - height + 10:
            break
        cnv.drawString(x + 5, cursor_y, line)
        cursor_y -= 11


def draw_signature_line(cnv: canvas.Canvas, x: float, y: float, width: float, label: str) -> None:
    cnv.line(x, y, x + width, y)
    cnv.setFont(FONT_REGULAR, 8.5)
    label_width = pdfmetrics.stringWidth(label, FONT_REGULAR, 8.5)
    cnv.drawString(x + (width - label_width) / 2, y - 11, label)


def build_pdf(data: dict[str, str]) -> bytes:
    buffer = BytesIO()
    cnv = canvas.Canvas(buffer, pagesize=A4)
    cnv.setTitle("FAI Vegetal")

    y = PAGE_HEIGHT - TOP_MARGIN

    idaron_logo = Path("logo idaron.png")
    estado_logo = Path("assets/logo-cropped.png")

    if idaron_logo.exists():
        cnv.drawImage(str(idaron_logo), LEFT_MARGIN, y - 18 * mm, width=24 * mm, preserveAspectRatio=True, mask="auto")

    if estado_logo.exists():
        center_w = 22 * mm
        center_x = LEFT_MARGIN + (CONTENT_WIDTH - center_w) / 2
        cnv.drawImage(str(estado_logo), center_x, y - 17 * mm, width=center_w, preserveAspectRatio=True, mask="auto")

    y -= 19 * mm
    cnv.setStrokeColor(black)
    cnv.line(LEFT_MARGIN, y, PAGE_WIDTH - RIGHT_MARGIN, y)

    title_size = fit_text(cnv, data["titulo"], FONT_BOLD, 11.5, 8, CONTENT_WIDTH - 8)
    cnv.setFont(FONT_BOLD, title_size)
    title_width = pdfmetrics.stringWidth(data["titulo"], FONT_BOLD, title_size)
    cnv.drawString((PAGE_WIDTH - title_width) / 2, y - 12, data["titulo"])

    subtitle_size = fit_text(cnv, data["subtitulo"], FONT_BOLD, 5, 4, CONTENT_WIDTH - 8)
    cnv.setFont(FONT_BOLD, subtitle_size)
    subtitle_width = pdfmetrics.stringWidth(data["subtitulo"], FONT_BOLD, subtitle_size)
    cnv.drawString((PAGE_WIDTH - subtitle_width) / 2, y - 20, data["subtitulo"])

    y -= 25
    title_row_h = 8 * mm
    number_col_w = 38 * mm
    cnv.rect(LEFT_MARGIN, y - title_row_h, CONTENT_WIDTH, title_row_h, stroke=1, fill=0)
    cnv.line(PAGE_WIDTH - RIGHT_MARGIN - number_col_w, y, PAGE_WIDTH - RIGHT_MARGIN - number_col_w, y - title_row_h)

    row_title = "FICHA DE ATENDIMENTO INDIVIDUAL - FAI"
    cnv.setFont(FONT_BOLD, 9.5)
    row_title_width = pdfmetrics.stringWidth(row_title, FONT_BOLD, 9.5)
    left_area_width = CONTENT_WIDTH - number_col_w
    cnv.drawString(LEFT_MARGIN + (left_area_width - row_title_width) / 2, y - 16, row_title)
    cnv.drawString(PAGE_WIDTH - RIGHT_MARGIN - number_col_w + 5, y - 16, f"N°/{data['numero']}")

    y -= title_row_h + 5 * mm
    field_h = 16 * mm
    gap = 3 * mm

    half_w = (CONTENT_WIDTH - gap) / 2
    third_w = (CONTENT_WIDTH - 2 * gap) / 3

    draw_field(cnv, LEFT_MARGIN, y, half_w, field_h, "Produtor / Cliente", data["produtor"])
    draw_field(cnv, LEFT_MARGIN + half_w + gap, y, half_w, field_h, "Propriedade", data["propriedade"])
    y -= field_h + gap

    draw_field(cnv, LEFT_MARGIN, y, third_w, field_h, "Municipio", data["municipio"])
    draw_field(cnv, LEFT_MARGIN + third_w + gap, y, third_w, field_h, "UF", data["uf"])
    draw_field(cnv, LEFT_MARGIN + (third_w + gap) * 2, y, third_w, field_h, "Responsavel", data["responsavel"])
    y -= field_h + 5 * mm

    cnv.setFont(FONT_BOLD, 9.5)
    cnv.drawString(LEFT_MARGIN, y, "AREA E CULTURA")
    y -= 4 * mm

    draw_field(cnv, LEFT_MARGIN, y, third_w, field_h, "Cultura", data["cultura"])
    draw_field(cnv, LEFT_MARGIN + third_w + gap, y, third_w, field_h, "Area", data["area"])
    draw_field(cnv, LEFT_MARGIN + (third_w + gap) * 2, y, third_w, field_h, "Talhao", data["talhao"])
    y -= field_h + 5 * mm

    cnv.setFont(FONT_BOLD, 9.5)
    cnv.drawString(LEFT_MARGIN, y, "OBSERVACOES")
    y -= 4 * mm

    obs_height = 55 * mm
    draw_text_block(cnv, LEFT_MARGIN, y, CONTENT_WIDTH, obs_height, data["observacoes"])
    y -= obs_height + 20 * mm

    sign_w = 70 * mm
    draw_signature_line(cnv, LEFT_MARGIN + 8 * mm, y, sign_w, "Responsavel tecnico")
    draw_signature_line(cnv, PAGE_WIDTH - RIGHT_MARGIN - sign_w - 8 * mm, y, sign_w, "Produtor / Representante")

    cnv.showPage()
    cnv.save()
    return buffer.getvalue()


register_fonts()

with st.sidebar:
    st.header("Dados do PDF")

    numero = st.text_input("Numero", value="")
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
    st.subheader("Cabecalho")
    titulo = st.text_input("Titulo", value="FISCALIZACAO DO VAZIO SANITARIO DA SOJA")
    subtitulo = st.text_input(
        "Subtitulo",
        value="ESTABELECIDA PELA INSTRUCAO NORMATIVA N 04/2026/IDARON-PROCFAS",
    )

    st.divider()
    st.subheader("Conteudo")
    observacoes = st.text_area(
        "Observacoes",
        value="",
        height=220,
        placeholder="Digite aqui o conteudo que deve sair no PDF.",
    )


st.title("FAI Vegetal")
st.caption("Base simplificada: o documento agora e gerado como PDF, sem depender da impressao HTML do navegador.")

document_data = {
    "numero": numero.strip(),
    "data_emissao": data_emissao.strftime("%d/%m/%Y"),
    "responsavel": responsavel.strip(),
    "produtor": produtor.strip(),
    "propriedade": propriedade.strip(),
    "municipio": municipio.strip(),
    "uf": uf.strip(),
    "cultura": cultura.strip(),
    "area": area.strip(),
    "talhao": talhao.strip(),
    "titulo": titulo.strip() or "FISCALIZACAO DO VAZIO SANITARIO DA SOJA",
    "subtitulo": subtitulo.strip() or "ESTABELECIDA PELA INSTRUCAO NORMATIVA",
    "observacoes": observacoes.strip(),
}

pdf_bytes = build_pdf(document_data)
pdf_b64 = base64.b64encode(pdf_bytes).decode("ascii")

left_col, right_col = st.columns([1, 1])
with left_col:
    st.download_button(
        "Baixar PDF",
        data=pdf_bytes,
        file_name="fai-vegetal.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

with right_col:
    st.write(f"Data do documento: `{document_data['data_emissao']}`")

components.html(
    f"""
    <iframe
        src="data:application/pdf;base64,{pdf_b64}"
        width="100%"
        height="1100"
        style="border: 1px solid #d0d7de; border-radius: 6px; background: white;"
    ></iframe>
    """,
    height=1120,
)
