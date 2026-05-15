"""
mtime_cache — skip rescan when target files unchanged.
Provides cached(key, paths, fn) that returns (result, cache_hit_bool).
"""
import hashlib
import json
import os

_CACHE_DIR = "/tmp/exocortex_cache"
os.makedirs(_CACHE_DIR, exist_ok=True)


def _hash_paths(paths):
    h = hashlib.sha256()
    for p in sorted(paths):
        try:
            st = os.stat(p)
            h.update(f"{p}:{st.st_mtime_ns}:{st.st_size}".encode())
        except FileNotFoundError:
            h.update(f"{p}:MISSING".encode())
    return h.hexdigest()


def cached(key, paths, fn):
    """Return (data, cache_hit_bool). Rebuilds only if file mtimes change.

    Args:
        key:   Cache key string (unique per call site).
        paths: List of file paths to watch for changes.
        fn:    Zero-argument callable that produces the data when cache is cold.
    """
    idx_path  = os.path.join(_CACHE_DIR, f"tr_{key}.json")
    data_path = os.path.join(_CACHE_DIR, f"tr_{key}.txt")
    try:
        with open(idx_path) as fh:
            old_hash = json.load(fh)["hash"]
    except Exception:
        old_hash = None
    new_hash = _hash_paths(paths)
    if old_hash == new_hash and os.path.exists(data_path):
        with open(data_path) as fh:
            return (fh.read(), True)
    data = fn()
    with open(idx_path, "w") as fh:
        json.dump({"hash": new_hash}, fh)
    if data is not None:
        with open(data_path, "w") as fh:
            json.dump(data, fh)
    return (data, False)
