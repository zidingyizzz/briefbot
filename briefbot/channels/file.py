"""Append each brief to a dated markdown report file (archive channel)."""
import datetime
import os

from .base import Channel


class FileChannel(Channel):
    type = "file"

    def send(self, subject, body):
        path = self.spec["path"]  # a directory (daily file) or an explicit file
        now = datetime.datetime.now()
        if path.endswith("/"):
            path = os.path.join(path, now.strftime("%Y-%m-%d") + ".md")
        lines = [
            f"# {subject}",
            "",
            f"_run at {now.strftime('%Y-%m-%d %H:%M:%S')}_",
            "",
            body,
            "",
        ]
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write("\n".join(lines))
