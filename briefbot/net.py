"""Shared HTTP helper: one User-Agent, one place to tune timeouts and retries."""
import time

import requests

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (compatible; BriefBot/1.0)")

ATTEMPTS = 3        # 1 try + 2 retries for transient failures
BACKOFF_SECONDS = 10  # linear backoff between attempts: 10s, 20s


class HttpError(RuntimeError):
    """HTTP status error (URL-free); keeps the code for retry decisions."""

    def __init__(self, status_code, reason):
        super().__init__(f"HTTP {status_code} {reason or ''}".strip())
        self.status_code = status_code


def http_get(url, timeout=30, attempts=ATTEMPTS, backoff=BACKOFF_SECONDS):
    """GET with retries for transient failures.

    Retried: network errors (read timeouts, resets) and HTTP 429/5xx —
    a feed server that hangs at its daily peak hour is often fine 10s
    later, so one cheap retry beats losing the source for the whole day.
    Not retried: other 4xx — the server deliberately refused the request.
    Errors never echo the URL: source URLs may carry query tokens.
    """
    last_error = None
    for attempt in range(1, max(1, attempts) + 1):
        try:
            resp = requests.get(url, timeout=timeout, headers={"User-Agent": UA})
            raise_clean(resp)  # URL-free error: source URLs may carry query tokens
            return resp
        except HttpError as exc:
            if exc.status_code != 429 and not 500 <= exc.status_code <= 599:
                raise  # deliberate refusal — retrying will not help
            last_error = exc
        except requests.RequestException as exc:
            # URL-free network error (requests embeds the URL in its messages).
            last_error = RuntimeError(f"network error ({type(exc).__name__})")
        if attempt < attempts and backoff:
            time.sleep(backoff * attempt)
    # attempt == actual tries made (max(1, attempts) guard included).
    raise RuntimeError(f"failed after {attempt} attempts: {last_error}") from None


def post_clean(url, **kwargs):
    """POST whose failures never echo the URL through exception messages.

    Several push APIs put the secret in the URL path (Telegram bot token,
    ServerChan send key, Feishu webhook id). requests embeds the full URL in
    its exceptions, so a failed send could otherwise print the key into logs.
    """
    try:
        return requests.post(url, **kwargs)
    except requests.RequestException as exc:
        raise RuntimeError(f"network error ({type(exc).__name__})") from None


def raise_clean(resp):
    """Like resp.raise_for_status(), but the error text omits the URL."""
    try:
        resp.raise_for_status()
    except requests.HTTPError:
        raise HttpError(resp.status_code, resp.reason) from None
