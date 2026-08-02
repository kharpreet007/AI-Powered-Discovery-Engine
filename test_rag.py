import sys
from server.retriever import retriever
from server.synthesizer import synthesizer

def test_rag(query: str):
    print(f"Testing query: '{query}'\n")
    
    print("1. Retrieving evidence...")
    evidence = retriever.retrieve(query, top_k=5)
    
    print(f"Found {len(evidence)} evidence chunks.")
    for i, e in enumerate(evidence):
        print(f"  [{i+1}] Source: {e.metadata.get('source')} (Score: {e.distance:.4f})")
        print(f"      Snippet: {e.document[:100]}...")
        
    if not evidence:
        print("No evidence found. Exiting.")
        return
        
    print("\n2. Synthesizing answer...")
    answer = synthesizer.synthesize(query, evidence)
    
    print("\n----------------- ANSWER -----------------")
    print(answer)
    print("------------------------------------------\n")

if __name__ == "__main__":
    query = "What are the common frustrations users have with grocery delivery apps?"
    if len(sys.argv) > 1:
        query = sys.argv[1]
    test_rag(query)
