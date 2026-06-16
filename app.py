from __future__ import annotations

from datetime import date
from io import BytesIO
from pathlib import Path

import fitz
import streamlit as st
from PIL import Image
from reportlab.lib.colors import black
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


def draw_compact_info_block(cnv: canvas.Canvas, x: float, top_y: float, width: float, data: dict[str, str]) -> float:
    top_row_h = 8 * mm
    bottom_row_h = 8 * mm
    bottom_cell_w = width / 4
    bottom_widths = [bottom_cell_w, bottom_cell_w, bottom_cell_w, bottom_cell_w]

    top_labels = [
        f"ULSAV DE: {data['ulsav_de']}".strip(),
        f"REGIONAL: {data['regional']}".strip(),
    ]
    bottom_labels = [
        f"PLACA DO VEICULO: {data['placa_veiculo']}".strip(),
        f"HOD. INICIAL: {data['hod_inicial']}".strip(),
        f"HOD. FINAL: {data['hod_final']}".strip(),
        f"DIST. DA ULSAV (km): {data['dist_ulsav_km']}".strip(),
    ]

    cnv.saveState()
    cnv.setLineWidth(0.5)
    cnv.setFont(FONT_REGULAR, 5)

    cnv.rect(x, top_y - top_row_h, width, top_row_h, stroke=1, fill=0)
    cnv.line(x + width / 2, top_y, x + width / 2, top_y - top_row_h)
    cnv.drawString(x + 2, top_y - 6, top_labels[0])
    cnv.drawString(x + width / 2 + 2, top_y - 6, top_labels[1])

    bottom_top_y = top_y - top_row_h
    cnv.rect(x, bottom_top_y - bottom_row_h, width, bottom_row_h, stroke=1, fill=0)

    current_x = x
    for cell_width in bottom_widths[:-1]:
        current_x += cell_width
        cnv.line(current_x, bottom_top_y, current_x, bottom_top_y - bottom_row_h)

    current_x = x
    for cell_width, label in zip(bottom_widths, bottom_labels):
        cnv.drawString(current_x + 2, bottom_top_y - 6, label)
        current_x += cell_width

    cnv.restoreState()
    return top_row_h + bottom_row_h


def draw_property_block(cnv: canvas.Canvas, x: float, top_y: float, width: float, data: dict[str, str]) -> float:
    row_h = 8 * mm
    code_col_w = 42 * mm
    municipio_label_w = 18 * mm
    area_label_w = 38 * mm
    soja_label_w = 33 * mm
    sisveg_label_w = 28 * mm
    sisveg_value_w = 24 * mm
    cpf_label_w = 10 * mm
    cpf_value_w = 30 * mm
    fone_label_w = 12 * mm
    fone_value_w = 35 * mm
    coord_label_w = 48 * mm

    cnv.saveState()
    cnv.setLineWidth(0.5)
    cnv.setFont(FONT_REGULAR, 5)

    cnv.rect(x, top_y - row_h, width, row_h, stroke=1, fill=0)
    cnv.line(x + width - code_col_w, top_y, x + width - code_col_w, top_y - row_h)
    cnv.drawString(x + 2, top_y - 6, f"NOME DA PROPRIEDADE: {data['propriedade']}".strip())
    cnv.drawString(x + width - code_col_w + 2, top_y - 6, f"COD. PROPRIEDADE: {data['cod_propriedade']}".strip())

    second_top_y = top_y - row_h
    cnv.rect(x, second_top_y - row_h, width, row_h, stroke=1, fill=0)
    cnv.drawString(
        x + 2,
        second_top_y - 6,
        f"LOGRA DOURO (Setor/Lh/Lt...): {data['logradouro']}".strip(),
    )

    third_top_y = second_top_y - row_h
    cnv.rect(x, third_top_y - row_h, width, row_h, stroke=1, fill=0)
    cnv.line(x + municipio_label_w, third_top_y, x + municipio_label_w, third_top_y - row_h)
    cnv.line(x + width - area_label_w, third_top_y, x + width - area_label_w, third_top_y - row_h)
    cnv.line(x + width - 19 * mm, third_top_y, x + width - 19 * mm, third_top_y - row_h)
    cnv.drawString(x + 2, third_top_y - 6, "MUNICIPIO:")
    cnv.drawString(x + municipio_label_w + 2, third_top_y - 6, data["municipio"])
    cnv.drawString(x + width - area_label_w + 2, third_top_y - 6, "Area da propriedade (ha):")
    cnv.drawString(x + width - 19 * mm + 2, third_top_y - 6, data["area_propriedade"])

    fourth_top_y = third_top_y - row_h
    cnv.rect(x, fourth_top_y - row_h, width, row_h, stroke=1, fill=0)
    cnv.line(x + soja_label_w, fourth_top_y, x + soja_label_w, fourth_top_y - row_h)
    cnv.line(x + width - sisveg_label_w - sisveg_value_w, fourth_top_y, x + width - sisveg_label_w - sisveg_value_w, fourth_top_y - row_h)
    cnv.line(x + width - sisveg_value_w, fourth_top_y, x + width - sisveg_value_w, fourth_top_y - row_h)
    cnv.drawString(x + 2, fourth_top_y - 6, "Area de soja cadastrada (ha):")
    cnv.drawString(x + soja_label_w + 2, fourth_top_y - 6, data["area_soja_cadastrada"])
    cnv.drawString(x + width - sisveg_label_w - sisveg_value_w + 2, fourth_top_y - 6, "COD. SISVEGETAL:")
    cnv.drawString(x + width - sisveg_value_w + 2, fourth_top_y - 6, data["cod_sisvegetal"])

    fifth_top_y = fourth_top_y - row_h
    cnv.rect(x, fifth_top_y - row_h, width, row_h, stroke=1, fill=0)
    cnv.line(x + width - cpf_label_w - cpf_value_w, fifth_top_y, x + width - cpf_label_w - cpf_value_w, fifth_top_y - row_h)
    cnv.line(x + width - cpf_value_w, fifth_top_y, x + width - cpf_value_w, fifth_top_y - row_h)
    cnv.drawString(x + 2, fifth_top_y - 6, f"SOJICULTOR: {data['sojicultor']}".strip())
    cnv.drawString(x + width - cpf_label_w - cpf_value_w + 2, fifth_top_y - 6, "CPF:")
    cnv.drawString(x + width - cpf_value_w + 2, fifth_top_y - 6, data["cpf"])

    sixth_top_y = fifth_top_y - row_h
    cnv.rect(x, sixth_top_y - row_h, width, row_h, stroke=1, fill=0)
    cnv.line(x + width - fone_label_w - fone_value_w, sixth_top_y, x + width - fone_label_w - fone_value_w, sixth_top_y - row_h)
    cnv.line(x + width - fone_value_w, sixth_top_y, x + width - fone_value_w, sixth_top_y - row_h)
    cnv.drawString(x + 2, sixth_top_y - 6, f"e-mail: {data['email']}".strip())
    cnv.drawString(x + width - fone_label_w - fone_value_w + 2, sixth_top_y - 6, "Fone:")
    cnv.drawString(x + width - fone_value_w + 2, sixth_top_y - 6, data["fone"])

    seventh_top_y = sixth_top_y - row_h
    coord_half_w = (width - coord_label_w) / 2
    cnv.rect(x, seventh_top_y - row_h, width, row_h, stroke=1, fill=0)
    cnv.line(x + coord_label_w, seventh_top_y, x + coord_label_w, seventh_top_y - row_h)
    cnv.line(x + coord_label_w + coord_half_w, seventh_top_y, x + coord_label_w + coord_half_w, seventh_top_y - row_h)
    cnv.drawString(x + 2, seventh_top_y - 6, "COORDENADA DA VISITA:")
    cnv.drawString(x + coord_label_w + 2, seventh_top_y - 6, f"S {data['coord_s']}".strip())
    cnv.drawString(x + coord_label_w + coord_half_w + 2, seventh_top_y - 6, f"W {data['coord_w']}".strip())

    cnv.restoreState()
    return row_h * 7


def draw_image_scaled(cnv: canvas.Canvas, image_path: Path, x: float, top_y: float, target_w: float) -> None:
    if not image_path.exists():
        return

    with Image.open(image_path) as img:
        img_w, img_h = img.size

    if img_w <= 0 or img_h <= 0:
        return

    target_h = target_w * (img_h / img_w)
    cnv.drawImage(
        str(image_path),
        x,
        top_y - target_h,
        width=target_w,
        height=target_h,
        preserveAspectRatio=True,
        mask="auto",
    )


def render_pdf_preview(pdf_bytes: bytes) -> bytes:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc.load_page(0)
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
    return pix.tobytes("png")


def build_pdf(data: dict[str, str]) -> bytes:
    buffer = BytesIO()
    cnv = canvas.Canvas(buffer, pagesize=A4)
    cnv.setTitle("FAI Vegetal")

    y = PAGE_HEIGHT - TOP_MARGIN

    idaron_logo = Path("logo idaron.png")
    estado_logo = Path("assets/logo-cropped.png")

    if idaron_logo.exists():
        draw_image_scaled(cnv, idaron_logo, LEFT_MARGIN, y - 1 * mm, 24 * mm)

    if estado_logo.exists():
        center_w = 22 * mm
        center_x = LEFT_MARGIN + (CONTENT_WIDTH - center_w) / 2
        draw_image_scaled(cnv, estado_logo, center_x, y, center_w)

    y -= 19 * mm
    cnv.setStrokeColor(black)
    cnv.line(LEFT_MARGIN, y, PAGE_WIDTH - RIGHT_MARGIN, y)

    title_size = 11.5
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

    y -= title_row_h + 3 * mm
    compact_block_h = draw_compact_info_block(cnv, LEFT_MARGIN, y, CONTENT_WIDTH, data)
    y -= compact_block_h + 1 * mm
    property_block_h = draw_property_block(cnv, LEFT_MARGIN, y, CONTENT_WIDTH, data)
    y -= property_block_h + 5 * mm
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
    cod_propriedade = st.text_input("Cod. propriedade", value="")
    logradouro = st.text_input("Logra douro (Setor/Lh/Lt...)", value="")
    municipio = st.text_input("Municipio", value="")
    area_propriedade = st.text_input("Area da propriedade (ha)", value="")
    area_soja_cadastrada = st.text_input("Area de soja cadastrada (ha)", value="")
    cod_sisvegetal = st.text_input("Cod. SISVEGETAL", value="")
    sojicultor = st.text_input("Sojicultor", value="")
    cpf = st.text_input("CPF", value="")
    email = st.text_input("e-mail", value="")
    fone = st.text_input("Fone", value="")
    coord_s = st.text_input("Coordenada S", value="")
    coord_w = st.text_input("Coordenada W", value="")
    uf = st.text_input("UF", value="")

    st.divider()
    st.subheader("Deslocamento")
    ulsav_de = st.text_input("ULSAV de", value="")
    regional = st.text_input("Regional", value="")
    placa_veiculo = st.text_input("Placa do veiculo", value="")
    hod_inicial = st.text_input("HOD. inicial", value="")
    hod_final = st.text_input("HOD. final", value="")
    dist_ulsav_km = st.text_input("Dist. da ULSAV (km)", value="")

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
    "cod_propriedade": cod_propriedade.strip(),
    "logradouro": logradouro.strip(),
    "municipio": municipio.strip(),
    "area_propriedade": area_propriedade.strip(),
    "area_soja_cadastrada": area_soja_cadastrada.strip(),
    "cod_sisvegetal": cod_sisvegetal.strip(),
    "sojicultor": sojicultor.strip(),
    "cpf": cpf.strip(),
    "email": email.strip(),
    "fone": fone.strip(),
    "coord_s": coord_s.strip(),
    "coord_w": coord_w.strip(),
    "uf": uf.strip(),
    "ulsav_de": ulsav_de.strip(),
    "regional": regional.strip(),
    "placa_veiculo": placa_veiculo.strip(),
    "hod_inicial": hod_inicial.strip(),
    "hod_final": hod_final.strip(),
    "dist_ulsav_km": dist_ulsav_km.strip(),
    "cultura": cultura.strip(),
    "area": area.strip(),
    "talhao": talhao.strip(),
    "titulo": titulo.strip() or "FISCALIZACAO DO VAZIO SANITARIO DA SOJA",
    "subtitulo": subtitulo.strip() or "ESTABELECIDA PELA INSTRUCAO NORMATIVA",
    "observacoes": observacoes.strip(),
}

pdf_bytes = build_pdf(document_data)
left_col, right_col = st.columns([1, 1])
with left_col:
    st.download_button(
        "Baixar PDF",
        data=pdf_bytes,
        file_name="fai-vegetal.pdf",
        mime="application/pdf",
        width="stretch",
    )

with right_col:
    st.write(f"Data do documento: `{document_data['data_emissao']}`")
    st.write(f"Fonte do titulo: `{FONT_BOLD}` em `11.5pt`")

preview_png = render_pdf_preview(pdf_bytes)
st.image(preview_png, width="stretch")
