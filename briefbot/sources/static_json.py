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

        # "." (root array) or stray empty segments must not be traversed:
        # ".".split(".") == ["", ""] would crash on data[""].
        parts = [p for p in (self.spec.get("list_path") or "").split(".") if p]
        for part in parts:
            data = data[part]
        if isinstance(data, dict):
            data = [data]  # single-object APIs work too (watched as one row)
        if not isinstance(data, list):
            raise RuntimeError(f"static_json {self.id}: expected a JSON array")

        fields_spec = self.spec.get("fields") or {}
        uid_key = self.spec.get("uid_key") or "id"
        limit = int(self.spec.get("limit", 50))
        items = []
        for row_idx, row in enumerate(data[:limit]):
            if not isinstance(row, dict):
                row = {"value": str(row)}
            # audit#7（2026-11-12 修）：字段模板解析失败（API 改名/行结构不同）
            # 不得返回空串——空串会触发 watch_changes 的假变更告警（`1200 -> `）。
            # 渲染失败的字段标记 "<missing:key>"，watch 层按值变化如实呈现，
            # 且 fields 全失败的行跳过（比静默空值更可诊断）。
            missing = []

            def guarded_render(name, template, r=row):
                try:
                    return template.format(**r)
                except (KeyError, IndexError) as exc:
                    missing.append(name)
                    return f"<missing:{name}>"

            fields = {k: guarded_render(k, v) for k, v in fields_spec.items()} or dict(row)
            # uid 兜底用行索引（非 len(items)）：全失败行被跳过后 items 长度会漂移
            uid = str(row.get(uid_key, "")) or f"row{row_idx}"
            if missing and len(missing) == len(fields_spec):
                continue  # 该行所有模板字段都解析失败：结构性缺失，跳过不产生假条目
            items.append({
                "uid": f"{self.id}:{uid}",
                "title": fields.get("title", uid),
                "url": fields.get("url", ""),
                "text": "; ".join(f"{k}={v}" for k, v in fields.items())[:1500],
                "fields": fields,
            })
        return items
