# Architecture and viva notes

## Pipeline
1. **Ingestion** - ZIP / GitHub / sample -> safe extraction (`services/repository_service.py`).
2. **Parsing** - `parsers/` (Python `ast`; regex + brace matching for Java, JS, TS, C, C++) -> classes, functions, imports, calls.
3. **Knowledge graph** - `graph/graph_builder.py` creates nodes (Repository, File, Class, Function, Method, Module) and edges (CONTAINS, IMPORTS, CALLS, USES, EXTENDS, IMPLEMENTS, DEPENDS_ON, DEFINED_IN). NetworkX answers dependency/impact queries; Neo4j is optional.
4. **Vector index** - `services/indexing_service.py` chunks code per function/class/file; `vector/` embeds locally (sentence-transformers) into ChromaDB with file/class/function/line metadata.
5. **Agent** - `agents/graph_agent.py` (LangGraph): plan -> retrieve -> context -> answer.
6. **Hybrid retrieval** - `retrieval/hybrid_retriever.py`: runs the chosen tools, expands vector hits through the call graph, removes duplicates, boosts results found by several tools, ranks, builds the context.
7. **Answer** - local Ollama model, grounded by a strict system prompt (no invented files, say "not found").

## Agent tools
`vector_search`, `graph_search`, `file_search`, `dependency_analysis`, `code_context`, `repository_summary`.

## Why GraphRAG instead of plain RAG
Vector search finds similar text; the graph adds structure (who calls whom, who imports whom), so questions like "what breaks if I change X?" are answered from relationships, not guesses.

## Likely viva questions
- Why local models? Free, private, no API dependency.
- How is impact analysis computed? Reverse reachability over DEPENDS_ON edges (`networkx.ancestors`).
- How do you avoid hallucination? Context-only prompt, source list with line numbers, explicit "not found".
- Limitations? Regex parsers for non-Python languages, name-based call resolution, small-model answer quality.
