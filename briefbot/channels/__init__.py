"""Channel registry — `type:` in job config maps to a class here."""
from .base import Channel
from .bark import BarkChannel
from .email_smtp import EmailChannel
from .feishu import FeishuChannel
from .file import FileChannel
from .serverchan import ServerChanChannel
from .stdout import StdoutChannel
from .telegram import TelegramChannel

CHANNELS = {
    cls.type: cls
    for cls in (TelegramChannel, EmailChannel, FeishuChannel, ServerChanChannel,
                BarkChannel, StdoutChannel, FileChannel)
}


def build_channel(spec, ctx):
    ctype = spec.get("type")
    if ctype not in CHANNELS:
        raise ValueError(
            f"unknown channel type {ctype!r} (available: {', '.join(sorted(CHANNELS))})"
        )
    return CHANNELS[ctype](spec, ctx)
