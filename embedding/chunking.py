"""
Sliding window text chunking utilities.
"""


def chunk_text(
    text: str,
    chunk_size: int = 800,
    overlap: int = 100,
) -> list[str]:

    if not text:
        return []

    words = text.split()

    if len(words) <= chunk_size:
        return [
            text.strip()
        ]

    chunks = []

    start = 0

    while start < len(words):

        end = start + chunk_size

        chunk = " ".join(
            words[start:end]
        )

        chunks.append(chunk)

        start += chunk_size - overlap

    return chunks

