"""Channel interface: send(subject, body)."""


class Channel:
    type = "base"

    def __init__(self, spec, ctx):
        self.spec = spec
        self.ctx = ctx  # full config, for shared settings like `smtp:`

    def send(self, subject, body):
        raise NotImplementedError
