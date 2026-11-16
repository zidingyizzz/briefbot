"""audit#7 回归测试：static_json 字段模板解析失败不得产生假变更告警。

场景（2026-11-07 audit #7）：API 改字段名（price→amount）后，
旧代码 KeyError→""→watch_changes 天天报 `1200 -> ` 假变更。
修复后：部分失败标记 <missing:key>；全失败行跳过；uid 兜底不漂移。
"""
import json
import os
import tempfile
import unittest

from briefbot.sources.static_json import StaticJsonSource


def _write(rows):
    fh = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    json.dump(rows, fh)
    fh.close()
    return fh.name


class TestStaticJsonMissingFields(unittest.TestCase):
    _files: list = []

    def tearDown(self):
        for f in self._files:
            try:
                os.unlink(f)
            except FileNotFoundError:
                pass
        type(self)._files = []

    def _src(self, rows, fields):
        p = _write(rows)
        self._files.append(p)
        return StaticJsonSource(
            {"id": "t", "url": p, "uid_key": "sku", "fields": fields})

    def test_partial_missing_marks_field(self):
        # API 改名：price 键消失 → 保留条目且显式标记，不是空串
        items = self._src(
            [{"sku": "A1", "name": "Widget", "amount": 1200}],
            {"title": "{name}", "price": "{price}"}).collect()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["fields"]["title"], "Widget")
        self.assertEqual(items[0]["fields"]["price"], "<missing:price>")

    def test_all_missing_row_skipped(self):
        # 全部模板字段解析失败 → 整行跳过，不产生假条目
        items = self._src(
            [{"sku": "A1", "name": "W"}, {"sku": "A2", "name": "X"}],
            {"x": "{nope1}", "y": "{nope2}"}).collect()
        self.assertEqual(items, [])

    def test_empty_fields_spec_keeps_raw_rows(self):
        # 无 fields_spec → dict(row) 兜底，不因 missing==len==0 误跳
        items = self._src(
            [{"sku": "A1", "name": "W"}], {}).collect()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["fields"], {"sku": "A1", "name": "W"})

    def test_uid_fallback_stable_across_skipped_rows(self):
        # 全失败行被跳过后，无 uid_key 行的兜底 uid 用行索引，不随 items 漂移
        items = self._src(
            [{"name": "bad"}, {"name": "ok"}],
            {"x": "{nope}", "y": "{name}"}).collect()
        # 第一行 nope+name：name 可渲染 → 部分失败保留；构造全失败+正常行混合
        items2 = self._src(
            [{"sku": "B0"}, {"name": "row2"}, {"sku": "B2"}],
            {"k": "{name}"}).collect()
        # B0 行全失败跳过；row2 行渲染成功；B2 行全失败跳过
        self.assertEqual(len(items2), 1)
        self.assertEqual(items2[0]["uid"], "t:row1")


if __name__ == "__main__":
    unittest.main()
