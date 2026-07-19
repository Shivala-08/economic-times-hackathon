#!/usr/bin/env python3
"""Run the full 18-question benchmark and report results."""
import json, time, sys
import numpy as np
from src.pipeline.query_engine import retrieve_context, generate_answer
from src.pipeline.llm import get_llm
from src.storage.chroma_store import VectorStore
from src.pipeline.embedder import TextEmbedder
from src.config import settings
from collections import defaultdict

qa_file = "data/benchmarks/qa_pairs.json"
with open(qa_file) as f:
    qa_pairs = json.load(f)

store = VectorStore()
if store.count() == 0:
    print("ERROR: Vector store empty. Run ingest first.")
    sys.exit(1)

llm = get_llm()
from src.pipeline.query_engine import get_embedder
embedder = get_embedder()
print(f"Vector store: {store.count()} chunks")
print(f"LLM: {type(llm).__name__} | model={llm.model} | available={llm.available}")
print(f"Running {len(qa_pairs)} questions...\n")

results = []
correct = 0
total_ms = 0

for i, qa in enumerate(qa_pairs, 1):
    t0 = time.time()
    question = qa["question"]
    expected = qa["answer"].lower()
    expected_source_docs = set(qa.get("source_docs", []))

    context = retrieve_context(question, top_k=50)
    llm_result = generate_answer(question, context)

    answer_text = llm_result.get("answer", "")
    sources_list = llm_result.get("sources", [])
    retrieved_source_docs = {s.get("citation", s.get("doc_id", "")) for s in sources_list}

    elapsed_ms = int((time.time() - t0) * 1000)
    total_ms += elapsed_ms

    # 1. Keyword overlap scoring
    expected_keywords = set(expected.split())
    answer_lower = answer_text.lower()
    matches = sum(1 for kw in expected_keywords if len(kw) > 4 and kw in answer_lower)
    hit_text_keyword = matches >= max(1, len(expected_keywords) // 4)

    # 2. Embedding similarity scoring
    emb_expected = embedder.embed_query(qa["answer"])
    emb_got = embedder.embed_query(answer_text)
    val_dot = np.dot(emb_expected, emb_got)
    val_norm = (np.linalg.norm(emb_expected) * np.linalg.norm(emb_got))
    similarity = val_dot / val_norm if val_norm > 0 else 0.0
    hit_text_semantic = similarity >= settings.similarity_threshold

    # Use semantic similarity as the new text pass criterion
    hit_text = hit_text_semantic

    hit_source = True
    if expected_source_docs:
        hit_source = any(
            any(es.lower() in rs.lower() for rs in retrieved_source_docs)
            for es in expected_source_docs
        )

    hit = hit_text and hit_source
    if hit:
        correct += 1

    status = "PASS" if hit else "FAIL"
    reason = []
    if not hit_text:
        reason.append(f"semantic similarity too low ({similarity:.3f} < {settings.similarity_threshold})")
    if expected_source_docs and not hit_source:
        reason.append("wrong source")
    conf = llm_result.get("confidence", "?")
    if conf == "Low" or conf == 0.25:
        reason.append("low confidence")
    reason_str = ", ".join(reason) if reason else ""

    # Print with detail on both similarity and keyword status
    kw_str = "kw=PASS" if hit_text_keyword else "kw=FAIL"
    print(f"[{i:02d}/18] {status} {qa['id']} | {elapsed_ms:5d}ms | conf={conf} | sim={similarity:.3f} ({kw_str}) | {question[:50]}...")
    if reason_str:
        print(f"        -> {reason_str}")
        print(f"        Expected: {qa['answer']}")
        print(f"        Got:      {answer_text}")

    results.append({"id": qa["id"], "passed": hit, "latency_ms": elapsed_ms, "category": qa.get("category", "")})

accuracy = round(correct / len(qa_pairs) * 100, 1) if qa_pairs else 0
avg_ms = round(total_ms / len(qa_pairs)) if qa_pairs else 0

print("\n" + "=" * 70)
print(f"RESULTS: {correct}/{len(qa_pairs)} correct ({accuracy}%)")
print(f"AVG LATENCY: {avg_ms} ms per question")
print(f"TOTAL TIME: {round(total_ms / 1000, 1)}s")
print(f"MODEL: {llm.model}")
print("=" * 70)

# Category breakdown
cat_stats = defaultdict(lambda: {"pass": 0, "fail": 0})
for r in results:
    cat = r.get("category", "other")
    if r["passed"]:
        cat_stats[cat]["pass"] += 1
    else:
        cat_stats[cat]["fail"] += 1

print("\nCATEGORY BREAKDOWN:")
for cat, s in sorted(cat_stats.items()):
    total_cat = s["pass"] + s["fail"]
    pct = round(s["pass"] / total_cat * 100) if total_cat > 0 else 0
    bar = "#" * s["pass"] + "-" * s["fail"]
    print(f"  {cat:<25s} {s['pass']}/{total_cat} ({pct:3d}%) {bar}")
