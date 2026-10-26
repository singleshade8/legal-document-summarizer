"""Optional translation layer (summary -> another language).

Built to survive free-service rate limits ("429 / TooManyRequests") during busy periods:

1. Built-in + disk cache - the sample judgments ship pre-translated (translation_cache.json) and every
                           new translation is saved, so nothing is requested twice.
2. Batching              - all uncached sentences go in ONE request per service (not one per sentence).
3. Throttling            - calls to the same host are spaced >= 0.7 s apart (no bursts).
4. Retry + back-off      - short, bounded retries (the whole attempt is capped at ~25 s).
5. Provider chain        - Argos (offline, if installed) -> Google "gtx" -> Google via deep-translator (if
                           installed) -> Lingva mirrors -> MyMemory. Different services = different rate pools.
                           All HTTP providers use only the Python standard library.
6. Graceful result       - if everything fails the caller still shows the original-language summary.
"""
import json
import os
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

_LOCK = threading.Lock()
_HTTP_LOCK = threading.Lock()
_last_call = {}
MIN_GAP = 0.7            # seconds between two calls to the same host
TOTAL_BUDGET = 25.0      # stop trying further providers after this many seconds

_CACHE_PATH = os.environ.get(
    "TRANSLATION_CACHE", os.path.join(os.path.dirname(os.path.abspath(__file__)), "translation_cache.json"))
_cache = None

LINGVA_HOSTS = ("lingva.ml", "lingva.garudalinux.org", "lingva.lunar.icu")


class RateLimited(Exception):
    pass


# ----------------------------------------------------------------------------- cache
def _load_cache():
    global _cache
    if _cache is None:
        try:
            with open(_CACHE_PATH, encoding="utf-8") as fh:
                _cache = json.load(fh)
        except (OSError, ValueError):
            _cache = {}
    return _cache


def _save_cache():
    try:
        with open(_CACHE_PATH, "w", encoding="utf-8") as fh:
            json.dump(_cache, fh, ensure_ascii=False)
    except OSError:
        pass  # read-only deployment: cache just lives in memory


def _key(src, tgt, text):
    return f"{src}>{tgt}|{text}"


# ----------------------------------------------------------------------------- HTTP helper
def _http_json(url, timeout=15):
    """GET a JSON document politely (per-host spacing). 429/403/503 -> RateLimited."""
    host = urllib.parse.urlparse(url).netloc
    with _HTTP_LOCK:
        wait = MIN_GAP - (time.time() - _last_call.get(host, 0))
        if wait > 0:
            time.sleep(wait)
        _last_call[host] = time.time()
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (NyayaSaar legal summarizer)"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code in (429, 403, 503):
            raise RateLimited(f"HTTP {exc.code}")
        raise


def _is_rate_limit(exc: Exception) -> bool:
    if isinstance(exc, RateLimited):
        return True
    msg = f"{type(exc).__name__} {exc}".lower()
    return any(m in msg for m in ("429", "too many", "toomanyrequests", "rate limit", "quota"))


# ----------------------------------------------------------------------------- providers
def _gtx(text, src, tgt):
    q = urllib.parse.urlencode({"client": "gtx", "sl": src, "tl": tgt, "dt": "t", "q": text})
    data = _http_json("https://translate.googleapis.com/translate_a/single?" + q)
    return "".join(seg[0] for seg in data[0] if seg and seg[0])


def _lingva(host):
    def fn(text, src, tgt):
        url = f"https://{host}/api/v1/{src}/{tgt}/" + urllib.parse.quote(text, safe="")
        return _http_json(url)["translation"]
    fn.__name__ = "lingva"
    return fn


def _mymemory(text, src, tgt):
    q = urllib.parse.urlencode({"q": text, "langpair": f"{src}|{tgt}"})
    data = _http_json("https://api.mymemory.translated.net/get?" + q)
    if str(data.get("responseStatus")) == "429":
        raise RateLimited("MyMemory 429")
    out = (data.get("responseData") or {}).get("translatedText", "")
    if "MYMEMORY WARNING" in out.upper() or "QUERY LENGTH LIMIT" in out.upper():
        raise RateLimited("MyMemory daily quota")
    return out


def _deep_google(text, src, tgt):
    from deep_translator import GoogleTranslator
    return GoogleTranslator(source=src, target=tgt).translate(text)


def _argos(text, src, tgt):
    import argostranslate.translate as at
    return at.translate(text, src, tgt)


def _argos_ready(src, tgt) -> bool:
    try:
        import argostranslate.translate as at
        langs = {l.code: l for l in at.get_installed_languages()}
        return src in langs and tgt in langs and langs[src].get_translation(langs[tgt]) is not None
    except Exception:
        return False


def _has_deep_translator() -> bool:
    try:
        import deep_translator  # noqa: F401
        return True
    except Exception:
        return False


def translation_available() -> bool:
    return True  # built-in cache + standard-library HTTP providers always exist


def _enc_size(s):  # URL-encoded size of a sentence (+ the %0A joiner)
    return len(urllib.parse.quote(s, safe="")) + 3


def _providers(src, tgt):
    """[(name, function, size_budget, batch, size_function)] in order of preference."""
    chain = []
    if _argos_ready(src, tgt):
        chain.append(("argos", _argos, 20000, True, len))
    chain.append(("google-gtx", _gtx, 4000, True, _enc_size))
    if _has_deep_translator():
        chain.append(("google", _deep_google, 4500, True, len))
    for host in LINGVA_HOSTS:
        chain.append((f"lingva:{host}", _lingva(host), 1800, True, _enc_size))
    chain.append(("mymemory", _mymemory, 450, False, len))  # tiny per-request limit -> one sentence at a time
    return chain


# ----------------------------------------------------------------------------- engine
def _retry(fn):
    """Bounded retry. Rate limit: 1 retry after 2 s. Other errors: up to 3 tries (1 s, 2 s)."""
    last = None
    for i in range(3):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 - libraries raise many types
            last = exc
            limited = _is_rate_limit(exc)
            if i >= (1 if limited else 2):
                break
            time.sleep(2 if limited else (i + 1))
    if _is_rate_limit(last):
        raise RateLimited(str(last))
    raise last


def _chunks(items, limit, size=len):
    cur, total = [], 0
    for it in items:
        sz = size(it)
        if cur and total + sz > limit:
            yield cur
            cur, total = [], 0
        cur.append(it)
        total += sz
    if cur:
        yield cur


def _split_bytes(sentence, max_bytes=440):
    """Split a long sentence on word boundaries so each piece fits a small per-request byte limit."""
    pieces, cur = [], ""
    for w in sentence.split():
        if cur and len((cur + " " + w).encode("utf-8")) > max_bytes:
            pieces.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        pieces.append(cur)
    return pieces or [sentence]


def _run_provider(fn, limit, batch, sentences, src, tgt, size=len):
    out = []
    if batch:
        for chunk in _chunks(sentences, limit, size):
            res = _retry(lambda c=chunk: fn("\n".join(c), src, tgt))
            parts = [p.strip() for p in (res or "").split("\n") if p.strip()]
            if len(parts) != len(chunk):  # service merged/split lines -> do this chunk one by one
                parts = [_retry(lambda s=s: fn(s, src, tgt)) for s in chunk]
            out.extend(parts)
    else:
        for s in sentences:
            pieces = [_retry(lambda p=p: fn(p, src, tgt)) for p in _split_bytes(s)]
            out.append(" ".join(x for x in pieces if x))
    return out


def translate_sentences(sentences, source: str, target: str):
    """Translate a list of sentences.

    Returns (translated_list | None, error_message | None, provider_name | None).
    """
    if not sentences or source == target:
        return list(sentences), None, None

    with _LOCK:
        cache = _load_cache()
        missing = [s for s in dict.fromkeys(sentences) if _key(source, target, s) not in cache]

    provider_used = "cache" if not missing else None
    rate_limited = False
    last_error = None

    if missing:
        started = time.time()
        for entry in _providers(source, target):
            name, fn, limit, batch, *rest = entry
            size = rest[0] if rest else len
            if time.time() - started > TOTAL_BUDGET:
                last_error = "time budget used up"
                break
            try:
                got = _run_provider(fn, limit, batch, missing, source, target, size)
                if len(got) != len(missing):
                    raise ValueError("provider returned an unexpected number of lines")
                with _LOCK:
                    for s, t in zip(missing, got):
                        cache[_key(source, target, s)] = t
                    _save_cache()
                provider_used = name
                break
            except RateLimited:
                rate_limited = True
                last_error = f"{name} is rate-limiting requests"
            except Exception as exc:  # noqa: BLE001
                last_error = f"{name}: {type(exc).__name__}"
        if provider_used is None:
            if rate_limited:
                msg = ("The free translation services are busy (too many requests). Wait about a minute and "
                       "press Summarise again - successful translations are saved, so retrying is cheap. "
                       "Showing the original-language summary.")
            else:
                msg = (f"Translation service unavailable ({last_error}). Check your internet connection. "
                       "Showing the original-language summary.")
            return None, msg, None

    with _LOCK:
        return [cache[_key(source, target, s)] for s in sentences], None, provider_used
