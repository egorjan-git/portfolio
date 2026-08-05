import re
import unicodedata

WHITESPACE_RE = re.compile(r"\s+")
TOKEN_RE = re.compile(r"[\w-]+", re.UNICODE)


def normalize_query(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold().strip()
    return WHITESPACE_RE.sub(" ", normalized)


def query_tokens(value: str) -> set[str]:
    return set(TOKEN_RE.findall(value))
