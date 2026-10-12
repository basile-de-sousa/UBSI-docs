"""Bounded, offline preview preparation. Never called in a web request."""
import base64
import csv
from datetime import date, datetime, time
from html.parser import HTMLParser
import io
import json
import math
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote
import zipfile
import zlib

from defusedxml import ElementTree as ET
from openpyxl.reader.excel import ExcelReader
from openpyxl.cell.read_only import ReadOnlyCell
from openpyxl.utils.cell import coordinate_to_tuple
from openpyxl.styles.numbers import is_date_format
from openpyxl.utils.datetime import from_excel
from PIL import Image, ImageOps
from pypdf import PdfReader, PdfWriter
import cairosvg


class PreparationError(Exception):
    def __init__(self, code, detail=""):
        self.code, self.detail = code, detail


def fail(code="invalid", detail=""):
    raise PreparationError(code, detail)


def bound(value, maximum, label):
    if value > maximum:
        fail("limit", f"{label} : {value:,} observés ; limite {maximum:,}.".replace(",", " "))


def xml(raw, limit):
    bound(len(raw), limit, "Octets XML décompressés")
    return ET.fromstring(raw)


DERIVED_BYTES = 0
DERIVED_LIMIT = 200 * 1024**2


def write_bytes(path, raw):
    global DERIVED_BYTES
    bound(DERIVED_BYTES + len(raw), DERIVED_LIMIT, "Octets des aperçus dérivés")
    path.write_bytes(raw)
    DERIVED_BYTES += len(raw)


def write_json(path, data):
    write_bytes(path, json.dumps(data, ensure_ascii=False, allow_nan=False).encode("utf-8"))


def check_pixels(width, height, limits):
    if width <= 0 or height <= 0: fail()
    bound(width * height, limits["pixels"], "Pixels de l’image")
    bound(max(width, height), limits["side"], "Pixels du plus grand côté")


def raster(raw, out, limits, expected=None):
    Image.MAX_IMAGE_PIXELS = None
    with Image.open(io.BytesIO(raw)) as image:
        if image.format not in {"PNG", "JPEG"} or (expected and image.format != expected):
            fail()
        check_pixels(*image.size, limits)
        image.load()
        image = ImageOps.exif_transpose(image)
        encoded = io.BytesIO()
        image.convert("RGBA" if image.mode in {"RGBA", "LA", "P"} else "RGB").save(encoded, format="PNG")
        write_bytes(out, encoded.getvalue())
    return {"asset": out.name, "mime": "image/png"}


def svg(raw, out, limits):
    root = xml(raw, limits["source_bytes"])
    allowed = {"svg", "g", "rect", "circle", "ellipse", "line", "path", "polyline", "polygon", "text", "tspan", "defs", "marker", "title", "desc", "linearGradient", "radialGradient", "stop", "clipPath"}
    if root.tag.split("}")[-1] != "svg":
        fail()
    for node in root.iter():
        if node.tag.split("}")[-1] not in allowed:
            fail("unsafe")
        for key, value in node.attrib.items():
            key = key.split("}")[-1]
            if key.lower().startswith("on") or key in {"href", "src", "style"} or re.search(r"(?:https?:|file:|javascript:|data:|@import)", value, re.I):
                fail("unsafe")
            if "url(" in value.lower() and not re.fullmatch(r"url\(#[A-Za-z0-9_-]+\)", value):
                fail("unsafe")
    # Derive a safe output size before Cairo allocates a surface.
    box = root.get("viewBox", "").replace(",", " ").split()
    def dimension(value, fallback):
        if value is None:
            return fallback
        match = re.fullmatch(r"([0-9.]+)(?:px)?", value)
        if not match:
            fail("invalid")
        return float(match[1])
    width = dimension(root.get("width"), float(box[2]) if len(box) == 4 else 1000)
    height = dimension(root.get("height"), float(box[3]) if len(box) == 4 else 700)
    if not math.isfinite(width) or not math.isfinite(height):
        fail()
    check_pixels(math.ceil(width), math.ceil(height), limits)
    png = cairosvg.svg2png(bytestring=ET.tostring(root), output_width=math.ceil(width), output_height=math.ceil(height), unsafe=False)
    return raster(png, out, limits, "PNG")


class LabelSanitizer(HTMLParser):
    """Reject active/remote HTML rather than silently render a different diagram."""
    def handle_starttag(self, tag, attrs):
        if tag.lower() not in {"div", "span", "p", "br", "b", "strong", "i", "em", "u", "s", "font", "table", "tbody", "tr", "td", "th", "ul", "ol", "li", "sub", "sup", "img"}:
            fail("unsafe")
        for key, value in attrs:
            if key.lower().startswith("on") or key.lower() in {"href", "srcset", "formaction"}:
                fail("unsafe")
            if value and re.search(r"https?:|file:|javascript:|expression\s*\(|url\s*\(|@import", value, re.I):
                fail("unsafe")
            if key.lower() == "src":
                self.images.append(value)
    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.images = []


def inline_image(value, limits):
    # draw.io commonly uses data:image/png,BASE64 without the ;base64 marker.
    match = re.fullmatch(r"data:image/(png|jpeg)(?:;base64)?,([A-Za-z0-9+/=\s]+)", value, re.I)
    if not match:
        fail("unsafe")
    raw = base64.b64decode(match[2], validate=False)
    with Image.open(io.BytesIO(raw)) as image:
        if image.format not in {"PNG", "JPEG"}:
            fail("unsafe")
        check_pixels(*image.size, limits)
        image.verify()


def drawio(raw, out, limits, vendor):
    root = xml(raw, limits["source_bytes"])
    pages = list(root) if root.tag == "mxfile" else [root] if root.tag == "mxGraphModel" else []
    if not pages or len(pages) > limits["pages"] or any(page.tag not in {"diagram", "mxGraphModel"} for page in pages):
        fail("limit" if len(pages) > limits["pages"] else "invalid")
    stencils = json.loads((vendor / "drawio-shapes.json").read_text())
    available = set(stencils["names"])
    supported_shapes = set(stencils["builtins"])
    manifest, total = [], 0
    for index, page in enumerate(pages):
        model = page.find("mxGraphModel") if page.tag == "diagram" else page
        if model is None:
            decoder = zlib.decompressobj(-15)
            packed = base64.b64decode((page.text or "").strip(), validate=True)
            decoded = decoder.decompress(packed, limits["drawio_page_bytes"] * 3 + 1)
            if len(decoded) > limits["drawio_page_bytes"] * 3 or not decoder.eof or decoder.unused_data:
                fail("limit")
            model = xml(unquote(decoded.decode("utf-8"), errors="strict").encode(), limits["drawio_page_bytes"])
        encoded = ET.tostring(model, encoding="unicode")
        size = len(encoded.encode())
        total += size
        if model.tag != "mxGraphModel" or size > limits["drawio_page_bytes"] or total > limits["expanded_bytes"]:
            fail("limit")
        if model.get("math") == "1": fail("renderer")
        cells = list(model.iter("mxCell"))
        parents = {child: parent for parent in model.iter() for child in parent}
        ids = [cell.get("id") or parents.get(cell, model).get("id") for cell in cells]
        if len(cells) > limits["cells"] or not cells or len(set(ids)) != len(ids) or None in ids:
            fail("limit" if len(cells) > limits["cells"] else "invalid")
        cell_by_id = dict(zip(ids, cells))
        checked = set()
        for identifier, cell in cell_by_id.items():
            for endpoint in [cell.get("source"), cell.get("target")]:
                if endpoint is not None and endpoint not in cell_by_id: fail()
            cursor, chain = identifier, set()
            while cursor is not None and cursor not in checked:
                if cursor in chain or cursor not in cell_by_id: fail()
                chain.add(cursor)
                cursor = cell_by_id[cursor].get("parent")
            checked.update(chain)
        allowed_tags = {"mxGraphModel", "root", "mxCell", "mxGeometry", "mxPoint", "Array", "mxRectangle", "object", "UserObject"}
        for node in model.iter():
            if node.tag not in allowed_tags:
                fail("unsafe")
            for key, value in node.attrib.items():
                if key.lower().startswith("on") or key.lower() in {"href", "link", "src"} or re.search(r"https?://|file:|javascript:|<script|<iframe|@import|expression\s*\(", value, re.I):
                    fail("unsafe")
                if "<" in value:
                    sanitizer = LabelSanitizer(); sanitizer.feed(value); sanitizer.close()
                    for image in sanitizer.images:
                        inline_image(image, limits)
                if key == "style":
                    shape = re.search(r"(?:^|;)shape=([^;]+)", value)
                    if shape and shape[1].startswith("stencil("):
                        packed = shape[1][8:-1] if shape[1].endswith(")") else ""
                        decoder = zlib.decompressobj(-15)
                        decoded = decoder.decompress(base64.b64decode(packed, validate=True), limits["drawio_page_bytes"] * 3 + 1)
                        if not decoder.eof or decoder.unused_data or len(decoded) > limits["drawio_page_bytes"] * 3: fail("limit")
                        stencil = xml(unquote(decoded.decode(), errors="strict").encode(), limits["drawio_page_bytes"])
                        allowed_commands = {"shape", "connections", "constraint", "background", "foreground", "save", "restore", "path", "move", "line", "quad", "curve", "arc", "rect", "roundrect", "ellipse", "close", "fill", "stroke", "fillstroke", "fillcolor", "strokecolor", "strokewidth", "dashed", "dashpattern", "alpha", "fillalpha", "strokealpha", "fontcolor", "fontfamily", "fontsize", "fontstyle", "text"}
                        if stencil.tag != "shape": fail()
                        for command in stencil.iter():
                            if command.tag not in allowed_commands or (command.text or "").strip(): fail("unsafe")
                            for attribute, parameter in command.attrib.items():
                                if attribute.lower().startswith("on") or re.search(r"https?:|file:|data:|javascript:|function|<|>", parameter, re.I): fail("unsafe")
                    elif shape and shape[1] not in available and shape[1] not in supported_shapes:
                        fail("renderer")
                    for image in re.findall(r"(?:^|;)(?:image|backgroundImage)=([^;]*(?:;base64,[^;]*)?)", value):
                        inline_image(image, limits)
                    if re.search(r"(?:^|;)(?:stencil|imageBackground|imageBorder)=", value):
                        fail("unsafe")
                    if "data:" in value and not re.search(r"(?:^|;)image=data:image/(?:png|jpeg)", value):
                        fail("unsafe")
            # Geometry must stay finite and bounded to avoid browser allocation abuse.
            for key in {"x", "y", "width", "height"} & node.attrib.keys():
                number = float(node.get(key))
                if not math.isfinite(number) or abs(number) > 100000:
                    fail("limit")
        name = f"page-{index}.json"
        write_json(out / name, {"xml": encoded})
        manifest.append({"name": page.get("name", f"Page {index + 1}"), "asset": name, "mime": "application/json"})
    return {"kind": "drawio", "pages": manifest, "notes": ["Consultation seule : les liens, ressources externes, bibliothèques personnalisées et actions d’édition ne sont pas pris en charge."]}


def cell_display(value, number_format):
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y %H:%M" if value.time() != time() else "%d/%m/%Y")
    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")
    if isinstance(value, time):
        return value.strftime("%H:%M:%S")
    if isinstance(value, bool):
        return "VRAI" if value else "FAUX"
    if isinstance(value, (float, int)) and not isinstance(value, bool):
        if not math.isfinite(value):
            fail()
        pattern = number_format.split(";")[0]
        decimals = re.search(r"\.([0#]+)", pattern)
        precision = min(len(decimals[1]), 10) if decimals else 0
        if "%" in pattern:
            return f"{value * 100:.{precision}f}".replace(".", ",") + " %"
        if re.search(r"[0#]", pattern) and pattern != "General":
            result = f"{value:,.{precision}f}" if "," in pattern.split(".")[0] else f"{value:.{precision}f}"
            return result.replace(",", " ").replace(".", ",")
    return str(value)


def sheet_assets(out, index, name, hidden, cells, rows, columns, notes=None):
    pages = max(1, math.ceil(rows / 100))
    for page in range(pages):
        subset = {str(row): cells.get(row, {}) for row in range(page * 100 + 1, min(rows, (page + 1) * 100) + 1)}
        write_json(out / f"sheet-{index}-{page}.json", subset)
    return {"name": name, "hidden": hidden, "rows": rows, "columns": columns, "pages": pages, "notes": notes or []}


def xlsx(path, out, limits):
    ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        bound(sum(i.file_size for i in infos), limits["expanded_bytes"], "Octets du classeur décompressé")
        bound(len(infos), 10000, "Entrées du classeur")
        names = [i.filename for i in infos]
        if len(set(names)) != len(names) or "[Content_Types].xml" not in names or "xl/workbook.xml" not in names:
            fail()
        if any(i.flag_bits & 1 or (i.compress_size and i.file_size > max(1048576, i.compress_size * 1000)) for i in infos):
            fail("limit")
        if any("vbaproject" in n.lower() or n.startswith(("xl/embeddings/", "xl/activeX/")) for n in names):
            fail("unsafe")
        types = xml(archive.read("[Content_Types].xml"), limits["expanded_bytes"])
        if not any(n.get("ContentType") == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml" for n in types):
            fail()
        # Never pass a package with external relationships to the workbook parser.
        # Hyperlinks/external formula caches are retained as inert values only.
        reader = ExcelReader(io.BytesIO(path.read_bytes()), read_only=True, data_only=True, keep_links=False)
        reader.read()
        workbook = reader.wb
        try:
            if workbook.chartsheets or not workbook.worksheets:
                fail("renderer")
            bound(len(workbook.worksheets), limits["sheets"], "Feuilles")
            total, sheets = 0, []
            for index, sheet in enumerate(workbook.worksheets):
                cells, max_row, max_column, merged = {}, 0, 0, False
                with archive.open(sheet._worksheet_path) as source:
                    for _, node in ET.iterparse(source, events=("end",)):
                        if node.tag == ns + "mergeCell":
                            merged = True
                        if node.tag != ns + "c":
                            if node.tag == ns + "row": node.clear()
                            continue
                        value_node, formula_node = node.find(ns + "v"), node.find(ns + "f")
                        inline = node.find(ns + "is")
                        value = value_node.text if value_node is not None else None
                        kind = node.get("t", "n")
                        populated = formula_node is not None or value is not None or inline is not None
                        if populated:
                            row, column = coordinate_to_tuple(node.get("r", ""))
                            if row < 1 or column < 1 or str(column) in cells.get(row, {}): fail()
                            total += 1
                            bound(row, limits["rows"], "Ligne renseignée")
                            bound(column, limits["columns"], "Colonne renseignée")
                            bound(total, limits["cells"], "Cellules renseignées")
                            formula = "".join(formula_node.itertext()) if formula_node is not None else None
                            missing = formula_node is not None and (value_node is None or (not value and kind != "str"))
                            if kind == "s" and value is not None:
                                value = reader.shared_strings[int(value)]
                            elif kind == "inlineStr":
                                value = "".join(n.text or "" for n in inline.iter(ns + "t")) if inline is not None else ""
                            elif kind == "b" and value is not None:
                                value = bool(int(value))
                            elif kind == "n" and value is not None:
                                value = float(value) if "." in value or "e" in value.lower() else int(value)
                            elif kind == "d" and value:
                                value = datetime.fromisoformat(value.replace("Z", "+00:00"))
                            styled = ReadOnlyCell(sheet, row, column, value, data_type="n", style_id=int(node.get("s", "0")))
                            if isinstance(value, (int, float)) and kind != "b" and is_date_format(styled.number_format):
                                value = from_excel(value, workbook.epoch)
                            display = "Résultat non disponible" if missing else cell_display(value, styled.number_format)
                            cells.setdefault(row, {})[str(column)] = {"value": display, "bold": bool(styled.font.bold), "missing": missing, "formula": formula}
                            max_row, max_column = max(max_row, row), max(max_column, column)
                        node.clear()
                sheets.append(sheet_assets(out, index, sheet.title, sheet.sheet_state != "visible", cells, max_row, max_column, ["Cellules fusionnées simplifiées : valeur en haut à gauche."] if merged else []))
            return {"kind": "table", "sheets": sheets, "notes": ["Valeurs enregistrées, sans recalcul. Résultat non disponible : recalculez et enregistrez le classeur avant réimport.", "Mise en forme simplifiée : nombres, dates, pourcentages, gras et retours à la ligne. Graphiques et mise en forme conditionnelle ne sont pas reproduits."]}
        finally:
            workbook.close()


def csv_preview(raw, out, limits, options):
    text = raw.decode("utf-8-sig")
    if "\x00" in text:
        fail()
    csv.field_size_limit(limits["source_bytes"])
    candidates, limit_errors = [], []
    chosen = options.get("delimiter", "auto")
    for separator in ([chosen] if chosen != "auto" else [",", ";", "\t"]):
        cells, width, rows, total, valid = {}, None, 0, 0, True
        try:
            for row in csv.reader(io.StringIO(text, newline=""), delimiter=separator, strict=True):
                rows += 1
                if width is None: width = len(row)
                if len(row) != width or not width:
                    valid = False; break
                total += sum(value != "" for value in row)
                bound(rows, limits["rows"], "Lignes CSV")
                bound(width, limits["columns"], "Colonnes CSV")
                bound(total, limits["cells"], "Cellules CSV renseignées")
                cells[rows] = {str(i + 1): {"value": value, "bold": False} for i, value in enumerate(row) if value != ""}
        except PreparationError as error:
            limit_errors.append(error)
            valid = False
        except csv.Error:
            valid = False
        if valid and rows and (width > 1 or chosen != "auto"):
            candidates.append((cells, rows, width, separator))
    if not candidates and limit_errors:
        raise limit_errors[0]
    if len(candidates) != 1:
        fail("csv")
    cells, rows, width, separator = candidates[0]
    return {"kind": "table", "sheets": [sheet_assets(out, 0, "Tableau CSV", False, cells, rows, width)], "delimiter": separator, "notes": ["CSV UTF-8 : texte brut, aucune formule exécutée."]}


def pdf(raw, out, limits):
    if not raw.startswith(b"%PDF-"):
        fail()
    reader = PdfReader(io.BytesIO(raw), strict=True)
    if reader.is_encrypted:
        fail("invalid")
    if not reader.pages: fail()
    bound(len(reader.pages), limits["pages"], "Pages PDF")
    writer = PdfWriter()
    for page in reader.pages:
        for key in ["/AA", "/Annots", "/OpenAction", "/PresSteps", "/Metadata"]:
            if key in page: del page[key]
        writer.add_page(page)
    encoded = io.BytesIO()
    writer.write(encoded)
    write_bytes(out / "preview.pdf", encoded.getvalue())
    return {"kind": "pdf", "pages": [{"name": f"Page {i+1}", "asset": "preview.pdf", "mime": "application/pdf"} for i in range(len(reader.pages))], "notes": ["Aperçu des pages : formulaires, liens, pièces jointes et actions PDF désactivés."]}


def plantuml(raw, out, limits, vendor):
    source = raw.decode("utf-8-sig")
    blocks = re.findall(r"(?ims)^\s*@startuml[^\r\n]*\r?\n.*?^\s*@enduml\s*$", source)
    if not blocks or len(blocks) > limits["pages"]:
        fail("limit" if len(blocks) > limits["pages"] else "invalid")
    remainder = re.sub(r"(?ims)^\s*@startuml[^\r\n]*\r?\n.*?^\s*@enduml\s*$", "", source)
    if remainder.strip():
        fail("invalid")
    if re.search(r"!\s*(?:include|import|theme)|%(?:load|read|file|getenv)|https?://|file:|<img|\[\[|!\s*(?:function|procedure|definelong)", source, re.I):
        fail("unsafe")
    bound(len(blocks) + len(re.findall(r"(?im)^\s*newpage\b", source)), limits["pages"], "Pages PlantUML")
    pages = []
    for i, block in enumerate(blocks):
        # Strip user-controlled output filenames and force the qualified engine.
        block = re.sub(r"(?im)^\s*@startuml[^\r\n]*", "@startuml", block)
        target = out / f"uml-{i}.puml"
        target.write_text(block, encoding="utf-8")
        completed = subprocess.run(["java", "-Djava.awt.headless=true", "-DPLANTUML_SECURITY_PROFILE=SANDBOX", f"-Xmx{limits['plantuml_heap_mb']}m", "-XX:CompressedClassSpaceSize=32m", "-XX:ReservedCodeCacheSize=64m", "-XX:MaxMetaspaceSize=128m", "-XX:+UseSerialGC", "-XX:ActiveProcessorCount=2", "-jar", str(vendor / "plantuml.jar"), "-Playout=smetana", "-tpng", "-failfast2", str(target)], cwd=out, env={"PATH": "/usr/bin:/bin:/opt/homebrew/bin", "PLANTUML_SECURITY_PROFILE": "SANDBOX", "HOME": str(out)}, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=limits["plantuml_seconds"])
        images = sorted(out.glob(f"uml-{i}*.png"))
        target.unlink(missing_ok=True)
        if completed.returncode != 0 or not images:
            fail("renderer")
        for image in images:
            if len(pages) >= limits["pages"]:
                fail("limit")
            raster(image.read_bytes(), image, limits, "PNG")
            pages.append({"name": f"Page {len(pages)+1}", "asset": image.name, "mime": "image/png"})
    return {"kind": "image", "pages": pages, "notes": ["Rendu local PlantUML ; includes et ressources externes refusés."]}


def prepare(path, format, out, limits, options, vendor):
    global DERIVED_BYTES, DERIVED_LIMIT
    DERIVED_BYTES, DERIVED_LIMIT = 0, limits["expanded_bytes"]
    Image.MAX_IMAGE_PIXELS = None
    raw = path.read_bytes()
    bound(len(raw), limits["source_bytes"], "Octets du fichier original")
    if format == "drawio": return drawio(raw, out, limits, vendor)
    if format == "xlsx": return xlsx(path, out, limits)
    if format == "csv": return csv_preview(raw, out, limits, options)
    if format == "pdf": return pdf(raw, out, limits)
    if format == "plantuml": return plantuml(raw, out, limits, vendor)
    if format in {"png", "jpeg", "svg"}:
        page = svg(raw, out / "preview.png", limits) if format == "svg" else raster(raw, out / "preview.png", limits, format.upper())
        return {"kind": "image", "pages": [{"name": "Image", **page}], "notes": []}
    fail()
