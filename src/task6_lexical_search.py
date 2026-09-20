"""
Task 6 — Lexical search bằng BM25.

Dùng cùng corpus chunks với Task 5. BM25 phù hợp với từ khóa chính xác, mã tài
liệu và tên riêng. Output phải theo SearchResult và sort score giảm dần.
"""


CORPUS: list[dict] = []


def get_corpus() -> list[dict]:
    """Lấy corpus chunks từ Task 4 nếu CORPUS chưa có."""
    global CORPUS
    if not CORPUS:
        try:
            from .task4_chunking_indexing import chunk_documents, load_documents
            CORPUS = chunk_documents(load_documents())
        except Exception:
            CORPUS = []
    return CORPUS


def build_bm25_index(corpus: list[dict]):
    """Tạo BM25 index từ cùng corpus chunks của Task 4."""
    try:
        from rank_bm25 import BM25Okapi
        tokenized = [item["content"].lower().split() for item in corpus]
        return BM25Okapi(tokenized)
    except ImportError:
        # Pure Python BM25 fallback
        import math
        from collections import Counter

        class PureBM25:
            def __init__(self, corpus_docs):
                self.docs = [doc["content"].lower().split() for doc in corpus_docs]
                self.N = len(self.docs)
                self.avgdl = sum(len(d) for d in self.docs) / (self.N or 1)
                self.doc_freqs = Counter()
                for d in self.docs:
                    for word in set(d):
                        self.doc_freqs[word] += 1

            def get_scores(self, query_tokens):
                scores = []
                k1, b = 1.5, 0.75
                for d in self.docs:
                    score = 0.0
                    doc_len = len(d)
                    counts = Counter(d)
                    for q in query_tokens:
                        if q in counts:
                            df = self.doc_freqs[q]
                            idf = math.log(1 + (self.N - df + 0.5) / (df + 0.5))
                            tf = counts[q]
                            num = tf * (k1 + 1)
                            den = tf + k1 * (1 - b + b * (doc_len / (self.avgdl or 1)))
                            score += idf * (num / den)
                    scores.append(score)
                return scores

        return PureBM25(corpus)


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """Trả về BM25 SearchResult theo score giảm dần."""
    active_corpus = CORPUS if CORPUS else get_corpus()
    if not active_corpus:
        return []

    bm25 = build_bm25_index(active_corpus)
    scores = bm25.get_scores(query.lower().split())

    scored_items = [
        (float(score), item)
        for score, item in zip(scores, active_corpus)
    ]
    # Sắp xếp giảm dần theo điểm
    scored_items.sort(key=lambda x: x[0], reverse=True)

    results = []
    seen_ids = set()
    for score, item in scored_items:
        if item["id"] in seen_ids:
            continue
        seen_ids.add(item["id"])
        results.append({
            "id": item["id"],
            "content": item["content"],
            "score": score,
            "metadata": item["metadata"],
            "retrieval_method": "bm25",
        })
        if len(results) >= top_k:
            break

    return results



if __name__ == "__main__":
    for result in lexical_search("test query", top_k=3):
        print(result)
