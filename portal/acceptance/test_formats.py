import io
import json
from pathlib import Path
import zipfile
from xml.etree import ElementTree as ET

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from openpyxl import Workbook
from PIL import Image
from pypdf import PdfWriter

from documents.services import upload
from jobs import worker
from knowledge.models import Kind, Relation

from .helpers import Fixtures


def workbook_bytes():
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["Numeric", "Empty", "Missing"])
    sheet.append(["=1+2", '=IF(1=1,"","x")', "=7*8"])
    workbook.create_sheet("Hidden").sheet_state = "hidden"
    workbook["Hidden"]["A1"] = "Fictional hidden value"
    original, output = io.BytesIO(), io.BytesIO()
    workbook.save(original)
    ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    with zipfile.ZipFile(original) as archive, zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as result:
        for entry in archive.infolist():
            data = archive.read(entry.filename)
            if entry.filename == "xl/worksheets/sheet1.xml":
                root = ET.fromstring(data)
                cells = {cell.attrib["r"]: cell for cell in root.iter(ns+"c")}
                cells["A2"].find(ns+"v").text = "3"
                cells["B2"].set("t", "str")
                cells["C2"].remove(cells["C2"].find(ns+"v"))
                data = ET.tostring(root)
            result.writestr(entry.filename, data)
    return output.getvalue()


class FormatAcceptance(Fixtures, TestCase):
    def prepare(self, extension, data, category="database"):
        app = self.application("APP-"+extension.upper())
        doc = self.draft(Kind.DOCUMENT, {"category": category, "description": "Synthetic acceptance source"}, {Relation.APPLICATION: [app.pk]})
        file = upload(self.admin.pk, doc.pk, doc.edit_version, SimpleUploadedFile("fictional."+extension, data))
        worker.execute(worker.claim())
        file.preview.refresh_from_db()
        self.assertEqual(file.preview.state, "ready", file.preview.error_code)
        doc = self.publish(doc)
        client = self.client_for(self.reader)
        self.assertEqual(client.get(f"/documents/{doc.pk}/preview/").status_code, 200)
        response = client.get(f"/documents/{doc.pk}/download/")
        self.assertEqual(b"".join(response.streaming_content), data)
        self.assertEqual(client.get(f"/admin/documents/{doc.pk}/revisions/1/download/").status_code, 403)
        return file

    def test_ac07_drawio_and_xml_have_two_pages(self):
        page = '<mxGraphModel><root><mxCell id="0"/><mxCell id="1" parent="0"/><mxCell id="2" value="Fictional" vertex="1" parent="1"><mxGeometry x="0" y="0" width="80" height="30" as="geometry"/></mxCell></root></mxGraphModel>'
        raw = ('<mxfile><diagram name="First">'+page+'</diagram><diagram name="Second">'+page+'</diagram></mxfile>').encode()
        for extension in ["drawio", "xml"]:
            with self.subTest(extension=extension):
                file = self.prepare(extension, raw, "flow")
                self.assertEqual(len(file.preview.manifest["pages"]), 2)

    def test_ac08_ac19_workbook_formula_cache_and_sheets(self):
        file = self.prepare("xlsx", workbook_bytes(), "spreadsheet")
        sheets = file.preview.manifest["sheets"]
        self.assertEqual(len(sheets), 2)
        self.assertTrue(sheets[1]["hidden"])
        assets = file.preview.manifest["assets"]
        page_name = next(name for name in assets if name.startswith("sheet-0") and name.endswith(".json"))
        data = json.loads((Path(self.private.name)/file.preview.asset_prefix/page_name).read_text())
        serialized = json.dumps(data, ensure_ascii=False)
        self.assertIn('"value": "3"', serialized)
        self.assertIn('"value": ""', serialized)
        self.assertIn('"missing": true', serialized)
        self.assertIn("Résultat non disponible", serialized)

    def test_ac09_uml_pdf_images_and_csv(self):
        writer, pdf = PdfWriter(), io.BytesIO()
        writer.add_blank_page(200, 200)
        writer.add_blank_page(200, 200)
        writer.write(pdf)
        png, jpeg = io.BytesIO(), io.BytesIO()
        Image.new("RGB", (20, 20), "white").save(png, format="PNG")
        Image.new("RGB", (20, 20), "white").save(jpeg, format="JPEG")
        uml = b"@startuml\nclass Fictional\n@enduml\n"
        cases = [("puml", uml, "database"), ("plantuml", uml, "database"), ("pdf", pdf.getvalue(), "database"), ("png", png.getvalue(), "database"), ("jpg", jpeg.getvalue(), "database"), ("jpeg", jpeg.getvalue(), "database"), ("svg", b'<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20"><rect width="10" height="10"/></svg>', "database"), ("csv", b"a;b\n1;2\n", "spreadsheet")]
        for extension, data, category in cases:
            with self.subTest(extension=extension): self.prepare(extension, data, category)
