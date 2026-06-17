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

st.markdown(
    """
    <style>
    .stApp .block-container {
        max-width: 1100px;
        margin-left: auto;
        margin-right: auto;
        padding-top: 1.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
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
    font_size = 9
    line_height = 11
    bullet_size = 2.4 * mm
    bullet_gap = 1.5 * mm
    cnv.setFont(FONT_REGULAR, font_size)

    cursor_y = top_y - 14
    paragraphs = str(text or "").splitlines() or [""]
    bottom_limit = top_y - height + 10

    for paragraph in paragraphs:
        raw = " ".join(paragraph.split())
        if not raw:
            cursor_y -= line_height
            continue

        has_square_bullet = raw.startswith("• ") or raw.startswith("- ")
        content = raw[2:].strip() if has_square_bullet else raw
        text_start_x = x + 5 + (bullet_size + bullet_gap if has_square_bullet else 0)
        available_width = width - 10 - (bullet_size + bullet_gap if has_square_bullet else 0)

        for line_index, line in enumerate(wrap_text(content, FONT_REGULAR, font_size, available_width)):
            if cursor_y < bottom_limit:
                return
            if has_square_bullet and line_index == 0:
                bullet_y = cursor_y - (bullet_size / 2) + (1 * mm)
                cnv.rect(x + 5, bullet_y, bullet_size, bullet_size, stroke=1, fill=0)
            cnv.drawString(text_start_x, cursor_y, line)
            cursor_y -= line_height


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
        f"PLACA DO VEÍCULO: {data['placa_veiculo']}".strip(),
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
    property_name_label_w = 18 * mm
    logradouro_label_w = 22 * mm
    municipio_label_w = 18 * mm
    area_label_w = 38 * mm
    soja_label_w = 33 * mm
    sisveg_label_w = 28 * mm
    sisveg_value_w = 24 * mm
    sojicultor_label_w = 20 * mm
    cpf_label_w = 10 * mm
    cpf_value_w = 30 * mm
    email_label_w = 14 * mm
    fone_label_w = 12 * mm
    fone_value_w = 35 * mm
    coord_label_w = 48 * mm
    cnv.saveState()
    cnv.setLineWidth(0.5)
    cnv.setFont(FONT_REGULAR, 5)

    cnv.rect(x, top_y - row_h, width, row_h, stroke=1, fill=0)
    cnv.line(x + property_name_label_w, top_y, x + property_name_label_w, top_y - row_h)
    cnv.line(x + width - code_col_w, top_y, x + width - code_col_w, top_y - row_h)
    cnv.drawString(x + 2, top_y - 5 - (2 * mm), "NOME DA")
    cnv.drawString(x + 2, top_y - 11 - (2 * mm), "PROPRIEDADE:")
    cnv.drawString(x + property_name_label_w + 2, top_y - 6, data["propriedade"])
    cnv.drawString(x + width - code_col_w + 2, top_y - 6, f"COD. PROPRIEDADE: {data['cod_propriedade']}".strip())

    second_top_y = top_y - row_h
    cnv.rect(x, second_top_y - row_h, width, row_h, stroke=1, fill=0)
    cnv.line(x + logradouro_label_w, second_top_y, x + logradouro_label_w, second_top_y - row_h)
    cnv.drawString(x + 2, second_top_y - 5 - (2 * mm), "LOGRADOURO")
    cnv.drawString(x + 2, second_top_y - 11 - (2 * mm), "(Setor/Lh/Lt...):")
    cnv.drawString(x + logradouro_label_w + 2, second_top_y - 6 - (2 * mm), data["logradouro"])

    third_top_y = second_top_y - row_h
    cnv.rect(x, third_top_y - row_h, width, row_h, stroke=1, fill=0)
    cnv.line(x + municipio_label_w, third_top_y, x + municipio_label_w, third_top_y - row_h)
    cnv.line(x + width - area_label_w, third_top_y, x + width - area_label_w, third_top_y - row_h)
    cnv.line(x + width - 19 * mm, third_top_y, x + width - 19 * mm, third_top_y - row_h)
    cnv.drawString(x + 2, third_top_y - 6 - (2 * mm), "MUNICÍPIO:")
    cnv.drawString(x + municipio_label_w + 2, third_top_y - 6 - (2 * mm), data["municipio"])
    cnv.drawString(x + width - area_label_w + 2, third_top_y - 6 - (2 * mm), "Área da propriedade (ha):")
    cnv.drawString(x + width - 19 * mm + 2, third_top_y - 6 - (2 * mm), data["area_propriedade"])

    fourth_top_y = third_top_y - row_h
    cnv.rect(x, fourth_top_y - row_h, width, row_h, stroke=1, fill=0)
    cnv.line(x + soja_label_w, fourth_top_y, x + soja_label_w, fourth_top_y - row_h)
    cnv.line(x + width - sisveg_label_w - sisveg_value_w, fourth_top_y, x + width - sisveg_label_w - sisveg_value_w, fourth_top_y - row_h)
    cnv.line(x + width - sisveg_value_w, fourth_top_y, x + width - sisveg_value_w, fourth_top_y - row_h)
    cnv.drawString(x + 2, fourth_top_y - 6 - (2 * mm), "Área de soja cadastrada (ha):")
    cnv.drawString(x + soja_label_w + 2, fourth_top_y - 6 - (2 * mm), data["area_soja_cadastrada"])
    cnv.drawString(x + width - sisveg_label_w - sisveg_value_w + 2, fourth_top_y - 6 - (2 * mm), "COD. SISVEGETAL:")
    cnv.drawString(x + width - sisveg_value_w + 2, fourth_top_y - 6 - (2 * mm), data["cod_sisvegetal"])

    fifth_top_y = fourth_top_y - row_h
    cnv.rect(x, fifth_top_y - row_h, width, row_h, stroke=1, fill=0)
    cnv.line(x + sojicultor_label_w, fifth_top_y, x + sojicultor_label_w, fifth_top_y - row_h)
    cnv.line(x + width - cpf_label_w - cpf_value_w, fifth_top_y, x + width - cpf_label_w - cpf_value_w, fifth_top_y - row_h)
    cnv.line(x + width - cpf_value_w, fifth_top_y, x + width - cpf_value_w, fifth_top_y - row_h)
    cnv.drawString(x + 2, fifth_top_y - 6 - (2 * mm), "SOJICULTOR:")
    cnv.drawString(x + sojicultor_label_w + 2, fifth_top_y - 6 - (2 * mm), data["sojicultor"])
    cnv.drawString(x + width - cpf_label_w - cpf_value_w + 2, fifth_top_y - 6 - (2 * mm), "CPF:")
    cnv.drawString(x + width - cpf_value_w + 2, fifth_top_y - 6 - (2 * mm), data["cpf"])

    sixth_top_y = fifth_top_y - row_h
    cnv.rect(x, sixth_top_y - row_h, width, row_h, stroke=1, fill=0)
    cnv.line(x + email_label_w, sixth_top_y, x + email_label_w, sixth_top_y - row_h)
    cnv.line(x + width - fone_label_w - fone_value_w, sixth_top_y, x + width - fone_label_w - fone_value_w, sixth_top_y - row_h)
    cnv.line(x + width - fone_value_w, sixth_top_y, x + width - fone_value_w, sixth_top_y - row_h)
    cnv.drawString(x + 2, sixth_top_y - 6 - (2 * mm), "e-mail:")
    cnv.drawString(x + email_label_w + 2, sixth_top_y - 6 - (2 * mm), data["email"])
    cnv.drawString(x + width - fone_label_w - fone_value_w + 2, sixth_top_y - 6 - (2 * mm), "Fone:")
    cnv.drawString(x + width - fone_value_w + 2, sixth_top_y - 6 - (2 * mm), data["fone"])

    seventh_top_y = sixth_top_y - row_h
    coord_half_w = (width - coord_label_w) / 2
    cnv.rect(x, seventh_top_y - row_h, width, row_h, stroke=1, fill=0)
    cnv.line(x + coord_label_w, seventh_top_y, x + coord_label_w, seventh_top_y - row_h)
    cnv.line(x + coord_label_w + coord_half_w, seventh_top_y, x + coord_label_w + coord_half_w, seventh_top_y - row_h)
    cnv.drawString(x + 2, seventh_top_y - 6, "COORDENADA DA VISITA:")
    cnv.drawString(x + coord_label_w + 2, seventh_top_y - 6, f"S {data['coord_s']}".strip())
    cnv.drawString(x + coord_label_w + coord_half_w + 2, seventh_top_y - 6, f"W {data['coord_w']}".strip())

    eighth_top_y = seventh_top_y - row_h
    confirm_start_x = x + coord_label_w + coord_half_w
    confirm_cell_w = (width - (coord_label_w + coord_half_w)) / 4
    sim_mark = "X" if data["coord_confere"] == "SIM" else ""
    nao_mark = "X" if data["coord_confere"] == "NÃO" else ""

    cnv.rect(x, eighth_top_y - row_h, width, row_h, stroke=1, fill=0)
    cnv.line(confirm_start_x, eighth_top_y, confirm_start_x, eighth_top_y - row_h)
    cnv.line(confirm_start_x + confirm_cell_w, eighth_top_y, confirm_start_x + confirm_cell_w, eighth_top_y - row_h)
    cnv.line(confirm_start_x + (confirm_cell_w * 2), eighth_top_y, confirm_start_x + (confirm_cell_w * 2), eighth_top_y - row_h)
    cnv.line(confirm_start_x + (confirm_cell_w * 3), eighth_top_y, confirm_start_x + (confirm_cell_w * 3), eighth_top_y - row_h)
    cnv.drawString(x + 2, eighth_top_y - 6, "COORDENADA DA PROPRIEDADE CONFERE COM A INFORMADA NO SISTEMA?")
    cnv.drawString(confirm_start_x + 2, eighth_top_y - 6, "SIM")
    cnv.drawString(confirm_start_x + confirm_cell_w + 2, eighth_top_y - 6, sim_mark)
    cnv.drawString(confirm_start_x + (confirm_cell_w * 2) + 2, eighth_top_y - 6, "NÃO")
    cnv.drawString(confirm_start_x + (confirm_cell_w * 3) + 2, eighth_top_y - 6, nao_mark)

    cnv.restoreState()
    return row_h * 8


def draw_standard_text_row(cnv: canvas.Canvas, x: float, top_y: float, width: float, text: str, checked: bool = False) -> float:
    font_size = 7
    line_height = 8
    square_size = 2.4 * mm
    label_gap = 1.2 * mm
    text_x = x + 3 + square_size + label_gap
    text_width = width - (text_x - x) - 3
    wrapped_lines = wrap_text(text, FONT_REGULAR, font_size, text_width)
    text_block_h = line_height * len(wrapped_lines)
    row_h = max(8 * mm, text_block_h + 6)
    top_padding = 8
    square_y = top_y - top_padding - square_size + (1 * mm)

    cnv.saveState()
    cnv.setLineWidth(0.5)
    cnv.rect(x, top_y - row_h, width, row_h, stroke=1, fill=0)
    draw_marked_square(cnv, x + 3, square_y, square_size, checked)
    cnv.setFont(FONT_REGULAR, font_size)
    cursor_y = top_y - top_padding
    for line in wrapped_lines:
        cnv.drawString(text_x, cursor_y, line)
        cursor_y -= line_height
    cnv.restoreState()
    return row_h


def draw_standard_empty_row(cnv: canvas.Canvas, x: float, top_y: float, width: float) -> float:
    row_h = 8 * mm
    cnv.saveState()
    cnv.setLineWidth(0.5)
    cnv.rect(x, top_y - row_h, width, row_h, stroke=1, fill=0)
    cnv.restoreState()
    return row_h


def draw_small_text_block(cnv: canvas.Canvas, x: float, top_y: float, width: float, text: str) -> float:
    row_h = 5.2 * mm
    font_size = fit_text(cnv, text, FONT_BOLD, 7, 5, width - 6)
    cnv.saveState()
    cnv.setLineWidth(0.5)
    cnv.rect(x, top_y - row_h, width, row_h, stroke=1, fill=0)
    cnv.setFont(FONT_BOLD, font_size)
    cnv.drawString(x + 3, top_y - 8, text)
    cnv.restoreState()
    return row_h


def draw_split_standard_rows(cnv: canvas.Canvas, x: float, top_y: float, width: float, num_rows: int = 4) -> float:
    row_h = 8 * mm
    total_h = row_h * max(num_rows, 1)
    cnv.saveState()
    cnv.setLineWidth(0.5)
    cnv.rect(x, top_y - total_h, width, total_h, stroke=1, fill=0)

    mid_x = x + (width / 2)
    cnv.line(mid_x, top_y, mid_x, top_y - total_h)

    for index in range(1, num_rows):
        row_y = top_y - (index * row_h)
        cnv.line(x, row_y, x + width, row_y)

    cnv.restoreState()
    return total_h


def draw_marked_square(cnv: canvas.Canvas, x: float, y: float, size: float, marked: bool) -> None:
    cnv.rect(x, y, size, size, stroke=1, fill=0)
    if marked:
        cnv.setFont(FONT_BOLD, 6)
        cnv.drawString(x + 0.6 * mm, y + 0.1 * mm, "X")


def draw_yes_no_option_cell(
    cnv: canvas.Canvas,
    x: float,
    top_y: float,
    height: float,
    base_text: str,
    selected: str = "",
) -> None:
    font_size = 7
    square_size = 2.4 * mm
    label_gap = 1.2 * mm
    option_gap = 4 * mm
    text_y = top_y - 13
    square_y = top_y - height + ((height - square_size) / 2) + (1 * mm) - 2

    cnv.setFont(FONT_REGULAR, font_size)
    cnv.drawString(x + 3, text_y, base_text)

    base_text_w = pdfmetrics.stringWidth(base_text, FONT_REGULAR, font_size)
    sim_x = x + 3 + base_text_w + (2 * mm)
    draw_marked_square(cnv, sim_x, square_y, square_size, selected == "SIM")
    cnv.drawString(sim_x + square_size + label_gap, text_y, "SIM")

    sim_label_w = pdfmetrics.stringWidth("SIM", FONT_REGULAR, font_size)
    nao_x = sim_x + square_size + label_gap + sim_label_w + option_gap
    draw_marked_square(cnv, nao_x, square_y, square_size, selected == "NÃO")
    cnv.drawString(nao_x + square_size + label_gap, text_y, "NÃO")


def draw_monitoring_option_cell(
    cnv: canvas.Canvas, x: float, top_y: float, width: float, height: float, selected: str = ""
) -> None:
    draw_yes_no_option_cell(cnv, x, top_y, height, "Realiza monitoramento da ferrugem:", selected)


def draw_safrinha_option_cell(
    cnv: canvas.Canvas, x: float, top_y: float, width: float, height: float, selected: str = ""
) -> None:
    draw_yes_no_option_cell(cnv, x, top_y, height, "Cultiva soja em safrinha:", selected)


def draw_occurrence_option_cell(
    cnv: canvas.Canvas, x: float, top_y: float, width: float, height: float, selected: str = ""
) -> None:
    draw_yes_no_option_cell(cnv, x, top_y, height, "Ocorrência de ferrugem:", selected)


def draw_safrinha_register_option_cell(
    cnv: canvas.Canvas, x: float, top_y: float, width: float, height: float, selected: str = ""
) -> None:
    draw_yes_no_option_cell(cnv, x, top_y, height, "Realizou Cadastro da safrinha:", selected)


def draw_lab_confirmation_option_cell(
    cnv: canvas.Canvas, x: float, top_y: float, width: float, height: float, selected: str = ""
) -> None:
    draw_yes_no_option_cell(cnv, x, top_y, height, "Ocorrência confirmada por laboratório:", selected)


def draw_plain_label_cell(cnv: canvas.Canvas, x: float, top_y: float, text: str) -> None:
    cnv.setFont(FONT_REGULAR, 7)
    cnv.drawString(x + 3, top_y - 13, text)


def draw_seed_origin_row(cnv: canvas.Canvas, x: float, top_y: float, width: float, data: dict[str, str | bool]) -> float:
    row_h = 8 * mm
    left_w = 62 * mm
    square_size = 2.4 * mm
    label_gap = 1.2 * mm
    option_gap = 5 * mm
    text_y = top_y - 13
    square_y = top_y - row_h + ((row_h - square_size) / 2) + (1 * mm) - 2
    right_x = x + left_w

    cnv.saveState()
    cnv.setLineWidth(0.5)
    cnv.rect(x, top_y - row_h, width, row_h, stroke=1, fill=0)
    cnv.line(right_x, top_y, right_x, top_y - row_h)

    cnv.setFont(FONT_REGULAR, 7)
    cnv.drawString(x + 3, text_y, "Estimativa de perda (%):")
    cnv.drawString(right_x + 3, text_y, "Origem das sementes safra/safrinha:")

    propria_x = right_x + 48 * mm
    draw_marked_square(cnv, propria_x, square_y, square_size, bool(data.get("origem_propria")))
    cnv.drawString(propria_x + square_size + label_gap, text_y, "Própria")

    empresa_x = propria_x + square_size + label_gap + pdfmetrics.stringWidth("Própria", FONT_REGULAR, 7) + option_gap
    draw_marked_square(cnv, empresa_x, square_y, square_size, bool(data.get("origem_empresa")))
    cnv.drawString(empresa_x + square_size + label_gap, text_y, "Empresa")

    outra_x = empresa_x + square_size + label_gap + pdfmetrics.stringWidth("Empresa", FONT_REGULAR, 7) + option_gap
    draw_marked_square(cnv, outra_x, square_y, square_size, bool(data.get("origem_outra")))
    cnv.drawString(outra_x + square_size + label_gap, text_y, "Outra")

    cnv.restoreState()
    return row_h


def draw_other_observations_box(cnv: canvas.Canvas, x: float, top_y: float, width: float) -> float:
    row_h = 8 * mm
    box_h = row_h * 3

    cnv.saveState()
    cnv.setLineWidth(0.5)
    cnv.rect(x, top_y - box_h, width, box_h, stroke=1, fill=0)
    cnv.setFont(FONT_BOLD, 7)
    cnv.drawString(x + 3, top_y - 10, "Outras observações:")
    cnv.restoreState()
    return box_h


def draw_schedule_signature_block(cnv: canvas.Canvas, x: float, top_y: float, width: float) -> float:
    row_h = 8 * mm
    total_h = row_h * 5
    left_w = width * 0.53
    right_w = width - left_w
    left_mid_x = x + (left_w * 0.55)
    split_x = x + left_w

    cnv.saveState()
    cnv.setLineWidth(0.5)
    cnv.rect(x, top_y - total_h, width, total_h, stroke=1, fill=0)
    cnv.line(split_x, top_y, split_x, top_y - total_h)

    current_y = top_y - row_h
    for _ in range(4):
        cnv.line(x, current_y, x + width, current_y)
        current_y -= row_h

    cnv.line(left_mid_x, top_y, left_mid_x, top_y - row_h)
    cnv.setFont(FONT_REGULAR, 7)
    cnv.drawString(x + 3, top_y - 13, "Horário:")
    cnv.drawString(left_mid_x + 3, top_y - 13, "Data:")
    cnv.drawString(split_x + 3, top_y - 13, "Local:")

    owner_header_y = top_y - row_h
    cnv.drawString(x + 3, owner_header_y - 13, "Proprietário, Produtor ou Responsável pelas Informações:")
    cnv.drawString(split_x + 3, owner_header_y - 13, "Carimbo e assinatura do servidor IDARON:")

    cnv.drawString(x + 3, owner_header_y - row_h - 13, "Nome:")
    cnv.drawString(x + 3, owner_header_y - (2 * row_h) - 13, "CPF:")
    cnv.drawString(x + 3, owner_header_y - (3 * row_h) - 13, "Assinatura:")

    cnv.restoreState()
    return total_h


def draw_block_header(cnv: canvas.Canvas, x: float, top_y: float, width: float, label: str) -> float:
    row_h = 5.5 * mm
    cnv.saveState()
    cnv.setLineWidth(0.5)
    cnv.rect(x, top_y - row_h, width, row_h, stroke=1, fill=0)
    cnv.setFont(FONT_BOLD, 8.5)
    cnv.drawString(x + 3, top_y - 8, label)
    cnv.restoreState()
    return row_h


def draw_verification_block(
    cnv: canvas.Canvas,
    x: float,
    top_y: float,
    width: float,
    items: list[dict[str, str | bool | list[str]]],
    left_option: str = "SIM",
    right_option: str = "NÃO",
) -> float:
    row_h = 5.5 * mm
    option_font_size = 6
    square_size = 2.4 * mm
    label_gap = 1.2 * mm
    option_gap = 5 * mm
    option_text_gap = 1.5 * mm
    right_padding = 3
    text_x = x + 3
    total_h = row_h * max(len(items), 1)
    option_ascent = pdfmetrics.getAscent(FONT_REGULAR, option_font_size) / 1000 * option_font_size
    option_descent = abs(pdfmetrics.getDescent(FONT_REGULAR, option_font_size) / 1000 * option_font_size)
    option_text_h = option_ascent + option_descent

    left_label_w = pdfmetrics.stringWidth(left_option, FONT_REGULAR, option_font_size)
    right_label_w = pdfmetrics.stringWidth(right_option, FONT_REGULAR, option_font_size)
    options_width = (square_size + label_gap + left_label_w + option_gap + square_size + label_gap + right_label_w)
    max_options_start_x = x + width - right_padding - options_width

    cnv.saveState()
    cnv.setLineWidth(0.5)
    cnv.rect(x, top_y - total_h, width, total_h, stroke=1, fill=0)

    for index, item in enumerate(items):
        text = str(item["text"])
        checkbox_only = bool(item.get("checkbox_only", False))
        bold_terms = [str(term) for term in item.get("bold_terms", [])] if item.get("bold_terms") else []
        current_top_y = top_y - (index * row_h)
        row_center_y = current_top_y - (row_h / 2)
        square_y = row_center_y - (square_size / 2) + (1 * mm)
        text_max_width = max(max_options_start_x - text_x - option_text_gap, 40)
        font_size = fit_text(cnv, text, FONT_REGULAR, 7, 5, text_max_width)

        cnv.setFont(FONT_REGULAR, font_size)
        if checkbox_only:
            draw_marked_square(cnv, text_x, square_y, square_size, bool(item.get("checked", False)))
            text_obj = cnv.beginText()
            text_obj.setTextOrigin(text_x + square_size + label_gap, current_top_y - 8)
            text_obj.setFont(FONT_REGULAR, font_size)

            cursor = 0
            while cursor < len(text):
                next_match = None
                next_term = None
                for term in bold_terms:
                    match_index = text.find(term, cursor)
                    if match_index != -1 and (next_match is None or match_index < next_match):
                        next_match = match_index
                        next_term = term

                if next_match is None or next_term is None:
                    text_obj.setFont(FONT_REGULAR, font_size)
                    text_obj.textOut(text[cursor:])
                    break

                if next_match > cursor:
                    text_obj.setFont(FONT_REGULAR, font_size)
                    text_obj.textOut(text[cursor:next_match])

                text_obj.setFont(FONT_BOLD, font_size)
                text_obj.textOut(next_term)
                cursor = next_match + len(next_term)

            cnv.drawText(text_obj)
            continue

        text_width = pdfmetrics.stringWidth(text, FONT_REGULAR, font_size)
        options_start_x = min(text_x + text_width + option_text_gap, max_options_start_x)
        option_text_y = row_center_y - (option_text_h / 2) + option_descent

        cnv.drawString(text_x, current_top_y - 8, text)
        cnv.setFont(FONT_REGULAR, option_font_size)
        selected = str(item.get("marked_option", ""))
        draw_marked_square(cnv, options_start_x, square_y, square_size, selected == left_option)
        cnv.drawString(options_start_x + square_size + label_gap, option_text_y, left_option)

        right_square_x = options_start_x + square_size + label_gap + left_label_w + option_gap
        draw_marked_square(cnv, right_square_x, square_y, square_size, selected == right_option)
        cnv.drawString(right_square_x + square_size + label_gap, option_text_y, right_option)

    cnv.restoreState()
    return total_h


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
    pix = page.get_pixmap(matrix=fitz.Matrix(3, 3), alpha=False)
    return pix.tobytes("png")


def build_pdf(data: dict[str, str]) -> bytes:
    buffer = BytesIO()
    cnv = canvas.Canvas(buffer, pagesize=A4)
    cnv.setTitle("FAI Vegetal")

    y = PAGE_HEIGHT - TOP_MARGIN

    idaron_logo = Path("assets/logo idaron")
    estado_logo = Path("assets/logo-cropped.png")

    if idaron_logo.exists():
        draw_image_scaled(cnv, idaron_logo, LEFT_MARGIN, y - 17 * mm, 24 * mm)

    if estado_logo.exists():
        center_w = 22 * mm
        center_x = LEFT_MARGIN + (CONTENT_WIDTH - center_w) / 2
        draw_image_scaled(cnv, estado_logo, center_x, y, center_w)

    y -= 19 * mm

    title_size = 11.5
    cnv.setFont(FONT_BOLD, title_size)
    title_width = pdfmetrics.stringWidth(data["titulo"], FONT_BOLD, title_size)
    cnv.drawString((PAGE_WIDTH - title_width) / 2, y - 12, data["titulo"])

    subtitle_size = fit_text(cnv, data["subtitulo"], FONT_BOLD, 5, 4, CONTENT_WIDTH - 8)
    cnv.setFont(FONT_BOLD, subtitle_size)
    subtitle_width = pdfmetrics.stringWidth(data["subtitulo"], FONT_BOLD, subtitle_size)
    cnv.drawString((PAGE_WIDTH - subtitle_width) / 2, y - 20, data["subtitulo"])

    y -= 29
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
    y -= property_block_h + 1 * mm
    verification_header_h = draw_block_header(cnv, LEFT_MARGIN, y, CONTENT_WIDTH, "SITUA\u00c7\u00d5ES VERIFICADAS:")
    y -= verification_header_h
    verification_line_h = draw_verification_block(
        cnv,
        LEFT_MARGIN,
        y,
        CONTENT_WIDTH,
        [
            {
                "text": "\u2022 A \u00e1rea fiscalizada possui cadastro no sistema da Ag\u00eancia IDARON:",
                "marked_option": data["cadastro_idaron_status"],
            },
            {
                "text": "\u2022 O cadastro foi realizado dentro do prazo Oficial:",
                "marked_option": data["cadastro_prazo_status"],
            },
            {
                "text": "Fica o produtor notificado, conforme Art. 10\u00b0 e par\u00e1grafos da Instru\u00e7\u00e3o Normativa n\u00ba 10/2024 a realizar o DESVITALIZAR em um prazo de 10 dias.",
                "checkbox_only": True,
                "checked": bool(data["notificacao_produtor_checked"]),
                "bold_terms": ["produtor notificado", "DESVITALIZAR"],
            },
        ],
    )
    y -= verification_line_h + 1 * mm
    empty_row_h = draw_standard_text_row(
        cnv,
        LEFT_MARGIN,
        y,
        CONTENT_WIDTH,
        "A(s) notifica\u00e7\u00e3o(\u00f5es) n\u00e3o foi(ram) atendida(s) dentro do prazo, caracterizando irregularidade(s) e o descumprimento da Instru\u00e7\u00e3o Normativa n\u00b0 10/2024-IDARON, tendo sido lavrado Auto de Infra\u00e7\u00e3o N\u00b0 ______ em __/___/20__",
        checked=bool(data["irregularidade_checked"]),
    )
    y -= empty_row_h + 1 * mm
    additional_obs_h = draw_small_text_block(
        cnv,
        LEFT_MARGIN,
        y,
        CONTENT_WIDTH,
        "OBSERVA\u00c7\u00d5ES ADICIONAIS, conforme a Instru\u00e7\u00e3o Normativa n\u00ba 10/2024/IDARON-PROCFAS:",
    )
    y -= additional_obs_h
    additional_rows_h = draw_split_standard_rows(cnv, LEFT_MARGIN, y, CONTENT_WIDTH, num_rows=4)
    draw_monitoring_option_cell(cnv, LEFT_MARGIN, y, CONTENT_WIDTH / 2, 8 * mm, data["monitoramento_ferrugem_status"])
    draw_safrinha_option_cell(cnv, LEFT_MARGIN + (CONTENT_WIDTH / 2), y, CONTENT_WIDTH / 2, 8 * mm, data["cultiva_soja_safrinha_status"])
    draw_occurrence_option_cell(cnv, LEFT_MARGIN, y - (8 * mm), CONTENT_WIDTH / 2, 8 * mm, data["ocorrencia_ferrugem_status"])
    draw_safrinha_register_option_cell(cnv, LEFT_MARGIN + (CONTENT_WIDTH / 2), y - (8 * mm), CONTENT_WIDTH / 2, 8 * mm, data["cadastro_safrinha_status"])
    draw_lab_confirmation_option_cell(cnv, LEFT_MARGIN, y - (16 * mm), CONTENT_WIDTH / 2, 8 * mm, data["ocorrencia_laboratorio_status"])
    draw_plain_label_cell(cnv, LEFT_MARGIN + (CONTENT_WIDTH / 2), y - (16 * mm), "Data de plantio:")
    draw_plain_label_cell(cnv, LEFT_MARGIN, y - (24 * mm), "Laboratório:")
    draw_plain_label_cell(cnv, LEFT_MARGIN + (CONTENT_WIDTH / 2), y - (24 * mm), "Outra(s) cultivos(s) safrinha:")
    y -= additional_rows_h
    blank_row_h = draw_standard_empty_row(cnv, LEFT_MARGIN, y, CONTENT_WIDTH)
    y -= blank_row_h
    seed_origin_h = draw_seed_origin_row(cnv, LEFT_MARGIN, y, CONTENT_WIDTH, data)
    y -= seed_origin_h
    other_obs_h = draw_other_observations_box(cnv, LEFT_MARGIN, y, CONTENT_WIDTH)
    y -= other_obs_h + 1 * mm
    schedule_signature_h = draw_schedule_signature_block(cnv, LEFT_MARGIN, y, CONTENT_WIDTH)

    cnv.showPage()
    cnv.save()
    return buffer.getvalue()


register_fonts()

yes_no_options = ["", "SIM", "NÃO"]

st.header("Formulário do PDF")
with st.form("fai_pdf_form"):
    top_cols = st.columns(3)
    with top_cols[0]:
        numero = st.text_input("Número", value="")
    with top_cols[1]:
        data_emissao = st.date_input("Data", value=date.today(), format="DD/MM/YYYY")
    with top_cols[2]:
        responsavel = st.text_input("Responsável", value="")

    with st.expander("Identificação", expanded=True):
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            produtor = st.text_input("Produtor / Cliente", value="")
            propriedade = st.text_input("Propriedade", value="")
            cod_propriedade = st.text_input("Cod. propriedade", value="")
            municipio = st.text_input("Município", value="")
            sojicultor = st.text_input("Sojicultor", value="")
        with col_b:
            logradouro = st.text_input("Logradouro (Setor/Lh/Lt...)", value="")
            area_propriedade = st.text_input("Área da propriedade (ha)", value="")
            area_soja_cadastrada = st.text_input("Área de soja cadastrada (ha)", value="")
            cod_sisvegetal = st.text_input("Cod. SISVEGETAL", value="")
            cpf = st.text_input("CPF", value="")
        with col_c:
            email = st.text_input("e-mail", value="")
            fone = st.text_input("Fone", value="")
            coord_s = st.text_input("Coordenada S", value="")
            coord_w = st.text_input("Coordenada W", value="")
            coord_confere = st.selectbox("Coordenada confere no sistema", yes_no_options, index=0)
            uf = st.text_input("UF", value="")

    with st.expander("Deslocamento", expanded=False):
        col_a, col_b = st.columns(2)
        with col_a:
            ulsav_de = st.text_input("ULSAV de", value="")
            placa_veiculo = st.text_input("Placa do veículo", value="")
            hod_inicial = st.text_input("HOD. inicial", value="")
        with col_b:
            regional = st.text_input("Regional", value="")
            hod_final = st.text_input("HOD. final", value="")
            dist_ulsav_km = st.text_input("Dist. da ULSAV (km)", value="")

    with st.expander("Cabeçalho e conteúdo", expanded=False):
        titulo = st.text_input("Título", value="FISCALIZAÇÃO DO VAZIO SANITÁRIO DA SOJA")
        subtitulo = st.text_input(
            "Subtítulo",
            value="ESTABELECIDA PELA INSTRUÇÃO NORMATIVA N° 04/2026/IDARON-PROCFAS",
        )
        observacoes = st.text_area(
            "Observações",
            value="",
            height=180,
            placeholder="Digite aqui o conteúdo que deve sair no PDF.",
        )

    with st.expander("Quadradinhos do PDF", expanded=True):
        ver_a, ver_b = st.columns(2)
        with ver_a:
            cadastro_idaron_status = st.selectbox("Área possui cadastro na Agência IDARON", yes_no_options, index=0)
            cadastro_prazo_status = st.selectbox("Cadastro realizado dentro do prazo oficial", yes_no_options, index=0)
            notificacao_produtor_checked = st.checkbox("Marcar notificação do produtor", value=False)
            irregularidade_checked = st.checkbox("Marcar irregularidade / auto de infração", value=False)
        with ver_b:
            monitoramento_ferrugem_status = st.selectbox("Realiza monitoramento da ferrugem", yes_no_options, index=0)
            cultiva_soja_safrinha_status = st.selectbox("Cultiva soja em safrinha", yes_no_options, index=0)
            ocorrencia_ferrugem_status = st.selectbox("Ocorrência de ferrugem", yes_no_options, index=0)
            cadastro_safrinha_status = st.selectbox("Realizou cadastro da safrinha", yes_no_options, index=0)
            ocorrencia_laboratorio_status = st.selectbox("Ocorrência confirmada por laboratório", yes_no_options, index=0)

        origem_cols = st.columns(3)
        with origem_cols[0]:
            origem_propria = st.checkbox("Origem da semente: Própria", value=False)
        with origem_cols[1]:
            origem_empresa = st.checkbox("Origem da semente: Empresa", value=False)
        with origem_cols[2]:
            origem_outra = st.checkbox("Origem da semente: Outra", value=False)

    st.form_submit_button("Atualizar PDF", width="stretch")

st.title("FAI Vegetal")
st.caption("Base simplificada: o documento agora é gerado como PDF, sem depender da impressão HTML do navegador.")

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
    "coord_confere": coord_confere.strip(),
    "uf": uf.strip(),
    "ulsav_de": ulsav_de.strip(),
    "regional": regional.strip(),
    "placa_veiculo": placa_veiculo.strip(),
    "hod_inicial": hod_inicial.strip(),
    "hod_final": hod_final.strip(),
    "dist_ulsav_km": dist_ulsav_km.strip(),
    "cultura": "",
    "area": "",
    "talhao": "",
    "titulo": titulo.strip() or "FISCALIZAÇÃO DO VAZIO SANITÁRIO DA SOJA",
    "subtitulo": subtitulo.strip() or "ESTABELECIDA PELA INSTRUÇÃO NORMATIVA",
    "observacoes": observacoes.strip(),
    "cadastro_idaron_status": cadastro_idaron_status.strip(),
    "cadastro_prazo_status": cadastro_prazo_status.strip(),
    "notificacao_produtor_checked": notificacao_produtor_checked,
    "irregularidade_checked": irregularidade_checked,
    "monitoramento_ferrugem_status": monitoramento_ferrugem_status.strip(),
    "cultiva_soja_safrinha_status": cultiva_soja_safrinha_status.strip(),
    "ocorrencia_ferrugem_status": ocorrencia_ferrugem_status.strip(),
    "cadastro_safrinha_status": cadastro_safrinha_status.strip(),
    "ocorrencia_laboratorio_status": ocorrencia_laboratorio_status.strip(),
    "origem_propria": origem_propria,
    "origem_empresa": origem_empresa,
    "origem_outra": origem_outra,
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
