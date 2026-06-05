# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
"""Nạp output parquet của GraphRAG vào Neo4j để xem trực quan.

Cách dùng:
    uv run python scripts/import_to_neo4j.py --output ./output

Biến môi trường (có default cho Neo4j chạy local bằng docker bên dưới):
    NEO4J_URI       (mặc định bolt://localhost:7687)
    NEO4J_USER      (mặc định neo4j)
    NEO4J_PASSWORD  (mặc định 123456)
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd
from neo4j import GraphDatabase


def _read(output: Path, name: str) -> pd.DataFrame | None:
    f = output / f"{name}.parquet"
    if not f.exists():
        print(f"  ! bỏ qua {name}.parquet (không tồn tại)")
        return None
    df = pd.read_parquet(f)
    print(f"  + {name}: {len(df)} dòng")
    return df


def import_graph(output: Path, uri: str, user: str, password: str) -> None:
    entities = _read(output, "entities")
    relationships = _read(output, "relationships")
    communities = _read(output, "communities")
    reports = _read(output, "community_reports")

    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as s:
        # Ràng buộc + index để MERGE nhanh và không trùng
        s.run("CREATE CONSTRAINT entity_title IF NOT EXISTS "
              "FOR (e:__Entity__) REQUIRE e.title IS UNIQUE")
        s.run("CREATE CONSTRAINT community_id IF NOT EXISTS "
              "FOR (c:__Community__) REQUIRE c.community IS UNIQUE")

        # --- Entities -> node :__Entity__ ---
        if entities is not None:
            rows = entities[["id", "title", "type", "description"]].fillna("").to_dict("records")
            s.run(
                """
                UNWIND $rows AS r
                MERGE (e:__Entity__ {title: r.title})
                SET e.id = r.id, e.type = r.type, e.description = r.description
                """,
                rows=rows,
            )
            print("  -> đã tạo node Entity")

        # --- Relationships -> edge :RELATED ---
        if relationships is not None:
            cols = ["source", "target", "description"]
            if "weight" in relationships.columns:
                cols.append("weight")
            rows = relationships[cols].fillna("").to_dict("records")
            s.run(
                """
                UNWIND $rows AS r
                MERGE (a:__Entity__ {title: r.source})
                MERGE (b:__Entity__ {title: r.target})
                MERGE (a)-[rel:RELATED]->(b)
                SET rel.description = r.description, rel.weight = r.weight
                """,
                rows=rows,
            )
            print("  -> đã tạo quan hệ RELATED")

        # --- Communities -> node :__Community__ + IN_COMMUNITY ---
        if communities is not None:
            comm = communities[["community", "level", "title", "entity_ids"]].copy()
            comm["community"] = comm["community"].astype(str)
            comm["entity_ids"] = comm["entity_ids"].apply(
                lambda x: list(x) if x is not None else []
            )
            rows = comm.to_dict("records")
            s.run(
                """
                UNWIND $rows AS r
                MERGE (c:__Community__ {community: toString(r.community)})
                SET c.level = r.level, c.title = r.title
                WITH c, r
                UNWIND coalesce(r.entity_ids, []) AS eid
                MATCH (e:__Entity__) WHERE e.id = eid OR e.title = eid
                MERGE (e)-[:IN_COMMUNITY]->(c)
                """,
                rows=rows,
            )
            print("  -> đã tạo node Community + IN_COMMUNITY")

        # --- Community reports -> gắn summary vào node Community ---
        if reports is not None:
            rows = reports[["community", "title", "summary", "rank"]].fillna("").to_dict("records")
            s.run(
                """
                UNWIND $rows AS r
                MERGE (c:__Community__ {community: toString(r.community)})
                SET c.report_title = r.title, c.summary = r.summary, c.rank = r.rank
                """,
                rows=rows,
            )
            print("  -> đã gắn community reports")

    driver.close()
    print("\nXong! Mở http://localhost:7474 và chạy:  MATCH (n) RETURN n LIMIT 200")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--output", default="./output", type=Path)
    p.add_argument("--uri", default=os.getenv("NEO4J_URI", "bolt://localhost:7687"))
    p.add_argument("--user", default=os.getenv("NEO4J_USER", "neo4j"))
    p.add_argument("--password", default=os.getenv("NEO4J_PASSWORD", "123456"))
    a = p.parse_args()
    print(f"Đọc parquet từ: {a.output.resolve()}")
    import_graph(a.output, a.uri, a.user, a.password)
