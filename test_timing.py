import time
from src.pipeline.query_engine import retrieve_context, generate_answer, get_embedder, get_vector_store
from src.pipeline.extractor import extract_entities
from src.graph.knowledge_graph import get_knowledge_graph

def run():
    question = "Which equipment requires quarterly inspection?"
    
    t0 = time.time()
    embedder = get_embedder()
    store = get_vector_store("docs")
    q_emb = embedder.embed_query(question)
    t1 = time.time()
    
    res = store.query(q_emb, n_results=5)
    t2 = time.time()
    
    ents = extract_entities(question)
    kg = get_knowledge_graph()
    t3 = time.time()
    
    context = retrieve_context(question, top_k=5)
    t4 = time.time()
    
    ans = generate_answer(question, context)
    t5 = time.time()
    
    print(f"Embedding: {(t1-t0)*1000:.2f} ms")
    print(f"Vector search: {(t2-t1)*1000:.2f} ms")
    print(f"Extract + KG init: {(t3-t2)*1000:.2f} ms")
    print(f"Full retrieve_context: {(t4-t3)*1000:.2f} ms")
    print(f"Generate answer: {(t5-t4)*1000:.2f} ms")
    print(f"Total: {(t5-t0)*1000:.2f} ms")

if __name__ == "__main__":
    run()
