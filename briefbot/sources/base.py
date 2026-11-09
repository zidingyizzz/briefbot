"""Source interface. Every source returns a list of item dicts:
{"uid": str, "title": str, "url": str, "text": str, "fields": dict}
"""


class Source:
    type = "base"

    def __init__(self, spec):
        self.spec = spec
        self.id = spec.get("id") or spec.get("url") or self.type

    def collect(self):
        raise NotImplementedError
