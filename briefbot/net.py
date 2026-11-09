"""Shared HTTP helper: one User-Agent, one place to tune timeouts."""
import requests

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (compatible; BriefBot/1.0)")


def http_get(url, timeout=30):
    resp = requests.get(url, timeout=timeout, headers={"User-Agent": UA})
    raise_clean(resp)  # URL-free error: source URLs may carry query tokens
    return resp


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
        raise RuntimeError(f"HTTP {resp.status_code} {resp.reason}") from None
