"""Neo4j access. Neo4j is the graph database of record; every graph is also cached as JSON
(graph_store) so the app still answers questions if Neo4j is temporarily down."""
import logging

from ..config import settings

log = logging.getLogger(__name__)
LABELS = {"Repository", "File", "Class", "Function", "Method", "Variable", "Module"}
REL_TYPES = {"CONTAINS", "IMPORTS", "CALLS", "USES", "EXTENDS", "IMPLEMENTS", "DEPENDS_ON", "DEFINED_IN"}


class Neo4jClient:
    def __init__(self) -> None:
        self._driver = None

    def _get_driver(self):
        if self._driver is None:
            from neo4j import GraphDatabase  # optional dependency (requirements-neo4j.txt)

            self._driver = GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password),
                                                connection_timeout=3, max_transaction_retry_time=3)
        return self._driver

    def available(self) -> bool:
        try:
            self._get_driver().verify_connectivity()
            return True
        except Exception as exc:
            log.warning("Neo4j unavailable: %s", exc)
            return False

    def write_graph(self, repo_id: str, graph: dict) -> None:
        """Replace the stored graph of a repository. Labels/types are whitelisted (no injection)."""
        with self._get_driver().session() as session:
            session.run("MATCH (n {repo_id: $r}) DETACH DELETE n", r=repo_id)
            by_label: dict[str, list[dict]] = {}
            for n in graph["nodes"]:
                if n["label"] in LABELS:
                    by_label.setdefault(n["label"], []).append({**n, "repo_id": repo_id})
            for label, rows in by_label.items():
                session.run(f"UNWIND $rows AS r MERGE (n:{label} {{id: r.id}}) SET n += r", rows=rows)
            by_type: dict[str, list[dict]] = {}
            for e in graph["edges"]:
                if e["type"] in REL_TYPES:
                    by_type.setdefault(e["type"], []).append(e)
            for typ, rows in by_type.items():
                session.run(f"UNWIND $rows AS r MATCH (a {{id: r.source}}), (b {{id: r.target}}) MERGE (a)-[:{typ}]->(b)", rows=rows)

    def neighbors(self, node_id: str, limit: int = 25) -> list[dict]:
        with self._get_driver().session() as session:
            res = session.run("MATCH (a {id: $id})-[r]-(b) RETURN a.name AS a, type(r) AS t, b.name AS b, "
                              "startNode(r).id = $id AS outgoing LIMIT $l", id=node_id, l=limit)
            return [dict(r) for r in res]

    def close(self) -> None:
        if self._driver:
            self._driver.close()


neo4j_client = Neo4jClient()
