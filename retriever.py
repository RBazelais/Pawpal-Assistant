import math
import os
import re
from typing import Any

_KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), "knowledge")


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _build_corpus() -> list[dict[str, Any]]:
    """Walk knowledge/ and load every .md bullet point as a separate chunk."""
    chunks: list[dict[str, Any]] = []
    for root, _, files in os.walk(_KNOWLEDGE_DIR):
        for fname in sorted(files):
            if not fname.endswith(".md"):
                continue
            path = os.path.join(root, fname)
            rel = os.path.relpath(path, _KNOWLEDGE_DIR).replace("\\", "/")
            parts = rel.split("/")
            species = parts[0] if len(parts) >= 2 else "unknown"
            topic = os.path.splitext(parts[-1])[0]

            with open(path, encoding="utf-8") as fh:
                text = fh.read()

            lines = [
                ln.lstrip("- ").strip()
                for ln in text.splitlines()
                if ln.strip().startswith("-")
            ]
            for line in lines:
                chunks.append(
                    {
                        "text": line,
                        "species": species,
                        "topic": topic,
                        "source": rel,
                        "tokens": _tokenize(line),
                    }
                )
    return chunks


_CORPUS: list[dict[str, Any]] = _build_corpus()


def _idf(term: str) -> float:
    df = sum(1 for chunk in _CORPUS if term in chunk["tokens"])
    if df == 0:
        return 0.0
    return math.log((1 + len(_CORPUS)) / (1 + df)) + 1.0


def _tf(term: str, tokens: list[str]) -> float:
    return tokens.count(term) / len(tokens) if tokens else 0.0


def _tfidf_score(query_tokens: list[str], chunk: dict[str, Any]) -> float:
    vocab = set(query_tokens) | set(chunk["tokens"])
    dot = q_norm = c_norm = 0.0
    for term in vocab:
        idf = _idf(term)
        q_val = _tf(term, query_tokens) * idf
        c_val = _tf(term, chunk["tokens"]) * idf
        dot += q_val * c_val
        q_norm += q_val ** 2
        c_norm += c_val ** 2
    denom = math.sqrt(q_norm) * math.sqrt(c_norm)
    return dot / denom if denom > 0 else 0.0


def retrieve(
    query: str,
    species: str = "any",
    top_k: int = 3,
) -> list[dict[str, Any]]:
    """Return top-k knowledge chunks most relevant to query.

    Results include: text, species, topic, source, score (0–1).
    Chunks from the matching species folder receive a 1.3x boost.
    """
    query_tokens = _tokenize(query)
    if not query_tokens:
        return []

    results: list[dict[str, Any]] = []
    for chunk in _CORPUS:
        score = _tfidf_score(query_tokens, chunk)
        if species in ("dog", "cat") and chunk["species"] == species:
            score *= 1.3
        results.append(
            {
                "text": chunk["text"],
                "species": chunk["species"],
                "topic": chunk["topic"],
                "source": chunk["source"],
                "score": min(score, 1.0),
            }
        )

    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:top_k]
