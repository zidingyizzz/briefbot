"""Print-to-console channel — great for testing and dry runs."""
from .base import Channel


class StdoutChannel(Channel):
    type = "stdout"

    def send(self, subject, body):
        print("=" * 64)
        print(subject)
        print("=" * 64)
        print(body)
        print()
