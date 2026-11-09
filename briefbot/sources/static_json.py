"""JSON API / local JSON file source with simple field templates.

Example spec:
  - type: static_json
    url: https://api.example.com/items        # or a local path
    list_path: data.items                     # optional dotted path to the array
    uid_key: sku
    fields: {title: "{name}", price: "{price}"}
"""
import json

from ..net import http_get
from .base import Source


class StaticJsonSource(Source):
    type = "static_json"

    def collect(self):
        target = self.spec["url"]
        if target.startswith("http://") or target.startswith("https://"):
            resp = http_get(target)
            data = resp.json()
        else:
            with open(target, "r", encoding="utf-8") as fh:
                data = json.load(fh)

        list_path = self.spec.get("list_path")
        if list_path:
            for part in list_path.split("."):
                data = data[part]
        if isinstance(data, dict):
            data = [data]  # single-object APIs work too (watched as one row)
        if not isinstance(data, list):
            raise RuntimeError(f"static_json {self.id}: expected a JSON array")

        fields_spec = self.spec.get("fields") or {}
        uid_key = self.spec.get("uid_key") or "id"
        limit = int(self.spec.get("limit", 50))
        items = []
        for row in data[:limit]:
            if not isinstance(row, dict):
                row = {"value": str(row)}
            fields = {k: _render(v, row) for k, v in fields_spec.items()} or dict(row)
            uid = str(row.get(uid_key, "")) or str(len(items))
            items.append({
                "uid": f"{self.id}:{uid}",
                "title": fields.get("title", uid),
                "url": fields.get("url", ""),
                "text": "; ".join(f"{k}={v}" for k, v in fields.items())[:1500],
                "fields": fields,
            })
        return items


def _render(template, row):
    try:
        return template.format(**row)
    except (KeyError, IndexError):
        return ""
