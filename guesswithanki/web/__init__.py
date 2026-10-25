"""The dashboard page: web/dashboard.html with the numbers of core/stats.summary put in."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def page(data, standalone=False):
    html = (HERE / "dashboard.html").read_text(encoding="utf-8")
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    html = html.replace("/*GP_DATA*/null", blob)
    if standalone:
        html = html.replace("<!--GP_HEAD-->", '<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">')
    return html
