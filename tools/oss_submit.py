"""oss_submit — Log a new claim directly to the OSS intelligence ledger (analyst dictation)."""

import os
import sys

from helpers.tool import Tool, Response

PLUGIN_PATH = os.environ.get("OSS_PLUGIN_PATH", "/a0/usr/plugins/oss")


def _ensure_plugin() -> None:
    for _k in list(sys.modules.keys()):
        if _k == 'src' or _k.startswith('src.'):
            del sys.modules[_k]
    if PLUGIN_PATH in sys.path:
        sys.path.remove(PLUGIN_PATH)
    sys.path.insert(0, PLUGIN_PATH)


def _oss_error(prefix: str, e: Exception) -> Response:
    return Response(message=f"[OSS] {prefix}: {e}", break_loop=False)


class OssSubmit(Tool):
    """
    Log a new claim directly to the OSS intelligence ledger.

    Use when the analyst dictates something worth recording that isn't
    coming through monitored RSS feeds. Claim is embedded, deduplicated,
    and inserted as STAGED with auto-promotion.

    Args:
        claim_text     (str):       The claim to record [required]
        topic_tags     (str|list):  Comma-separated or list of topic tags
        technique_class (str):      presuasion | fracture | emergent | direct | none
    """

    async def execute(self, **kwargs) -> Response:
        claim_text      = (self.args.get("claim_text") or "").strip()
        topic_tags      = self.args.get("topic_tags") or []
        technique_class = (self.args.get("technique_class") or "direct").strip()

        print(f"[OSS] oss_submit: claim={claim_text[:60]!r}", flush=True)

        if not claim_text:
            return Response(message="[OSS] oss_submit requires claim_text.", break_loop=False)

        if isinstance(topic_tags, str):
            topic_tags = [t.strip() for t in topic_tags.split(",") if t.strip()]

        try:
            _ensure_plugin()
            import numpy as np
            import faiss as faiss_lib
            from sentence_transformers import SentenceTransformer
            from src.db import get_conn, init_db, jloads, jdumps

            faiss_path = os.environ.get("OSS_FAISS_PATH", "/a0/usr/oss/claims.index")
            dedup_thr  = float(os.environ.get("OSS_DEDUP_THRESHOLD", "0.95"))
            emb_model  = os.environ.get("OSS_EMBEDDING_MODEL", "all-MiniLM-L6-v2")

            conn = get_conn()
            init_db(conn)
            cur  = conn.cursor()

            cur.execute("SELECT id FROM sources WHERE name='Analyst Manual Entry' LIMIT 1")
            row = cur.fetchone()
            if row:
                source_id = row["id"]
            else:
                cur.execute(
                    "INSERT INTO sources (name, url, source_type, cluster, confidence_score) "
                    "VALUES ('Analyst Manual Entry', 'manual://analyst-entry', 'official', 'official', 1.0)"
                )
                conn.commit()
                source_id = cur.lastrowid

            model = SentenceTransformer(emb_model)
            vec   = model.encode([claim_text], normalize_embeddings=True).astype(np.float32)

            duplicate = False
            if os.path.exists(faiss_path):
                idx = faiss_lib.read_index(faiss_path)
                if idx.ntotal > 0:
                    D, I = idx.search(vec, 1)
                    if D[0][0] >= dedup_thr:
                        duplicate = True

            if duplicate:
                conn.close()
                return Response(
                    message="[OSS] Near-identical claim already in ledger — not added.",
                    break_loop=False,
                )

            now       = __import__("datetime").datetime.utcnow().isoformat()
            tags_json = jdumps(topic_tags)
            cur.execute("""
                INSERT INTO claims
                    (source_id, raw_text, claim_text, article_url, article_title,
                     topic_tags, technique_class, extracted_at, trust_level,
                     staging_confidence)
                VALUES (?,?,?,?,?,?,?,?,'STAGED',1.0)
            """, (
                source_id, claim_text, claim_text,
                "manual://analyst-entry", "Analyst Manual Entry",
                tags_json, technique_class, now,
            ))
            conn.commit()
            claim_id = cur.lastrowid

            try:
                os.makedirs(os.path.dirname(faiss_path), exist_ok=True)
                if os.path.exists(faiss_path):
                    idx = faiss_lib.read_index(faiss_path)
                else:
                    idx = faiss_lib.IndexFlatIP(vec.shape[1])
                faiss_id = idx.ntotal
                idx.add(vec)
                faiss_lib.write_index(idx, faiss_path)
                cur.execute("UPDATE claims SET faiss_id=? WHERE id=?", (faiss_id, claim_id))
                conn.commit()
            except Exception as faiss_err:
                print(f"[OSS] FAISS persist warning: {faiss_err}", flush=True)

            cur.execute("UPDATE claims SET trust_level='PROMOTED' WHERE id=?", (claim_id,))
            conn.commit()

            matched   = []
            unmatched = []
            for tag in topic_tags:
                cur.execute("SELECT tag FROM topics WHERE tag=?", (tag,))
                if cur.fetchone():
                    matched.append(tag)
                else:
                    unmatched.append(tag)
            conn.close()

        except Exception as e:
            return _oss_error("oss_submit failed", e)

        lines = [
            f"[OSS] Claim submitted and promoted — ID {claim_id}",
            f"Topics matched: {matched if matched else '(none)'}",
        ]
        if unmatched:
            lines.append(f"Topics not recognized (not applied): {unmatched}")
        return Response(message="\n".join(lines), break_loop=False)
