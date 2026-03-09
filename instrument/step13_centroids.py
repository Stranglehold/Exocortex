#!/usr/bin/env python3
"""
step13_centroids.py — Domain centroid computation from activation geometry.

Reads data/domain_calibration.json, runs each prompt through read_activations
(last-token pooling at target layers), computes per-domain centroids, and
reports separability metrics to identify the optimal classification layer.

Separability score = mean inter-centroid cosine distance / mean intra-domain
cosine distance. Higher = domains are more geometrically distinct.

Usage:
    python3 step13_centroids.py
    python3 step13_centroids.py --layers 9,12,14,18
    python3 step13_centroids.py --save centroids.json
"""

import sys
import json
import argparse
import numpy as np
from pathlib import Path
from collections import defaultdict

CALIBRATION_PATH = Path(__file__).parent / 'data' / 'domain_calibration.json'

# read_activations.py handles UTF-8 stdout/stderr wrapping at import time
sys.path.insert(0, str(Path(__file__).parent))
from read_activations import read_activations, cosine_sim


def cosine_dist(a: np.ndarray, b: np.ndarray) -> float:
    return 1.0 - cosine_sim(a, b)


def centroid(vecs: list) -> np.ndarray:
    return np.mean(vecs, axis=0)


def mean_intra_dist(vecs: list, c: np.ndarray) -> float:
    """Mean cosine distance from centroid within domain."""
    if len(vecs) < 2:
        return 0.0
    return float(np.mean([cosine_dist(v, c) for v in vecs]))


def main():
    parser = argparse.ArgumentParser(description='Domain centroid computation from activation geometry')
    parser.add_argument('--layers', default='9,12,14,18',
                        help='Comma-separated layer indices (default: 9,12,14,18)')
    parser.add_argument('--pool', default='last', choices=['last', 'mean'],
                        help='Token pooling strategy (default: last)')
    parser.add_argument('--save', default=None, metavar='FILE',
                        help='Save centroids + metadata to data/<FILE>.json')
    args = parser.parse_args()

    layers = [int(x.strip()) for x in args.layers.split(',')]

    if not CALIBRATION_PATH.exists():
        print(f'ERROR: Calibration dataset not found: {CALIBRATION_PATH}', file=sys.stderr)
        sys.exit(1)

    with open(CALIBRATION_PATH, 'r', encoding='utf-8') as f:
        calibration = json.load(f)

    domains = sorted(set(e['domain'] for e in calibration))
    counts = {d: sum(1 for e in calibration if e['domain'] == d) for d in domains}

    print('=' * 72)
    print('Step 13: Domain Centroid Computation — Activation Geometry')
    print('=' * 72)
    print(f'Prompts: {len(calibration)}  Domains: {domains}')
    for d in domains:
        print(f'  {d:15s}: {counts[d]} prompts')
    print(f'Layers: {layers}  Pool: {args.pool}')
    print()

    # ── Forward passes ─────────────────────────────────────────────────────────
    # domain → list of result dicts ({layer_idx: np.ndarray})
    domain_activations: dict[str, list] = defaultdict(list)
    failed = 0

    for i, entry in enumerate(calibration):
        label = f'[{i+1:2d}/{len(calibration)}] {entry["domain"]:15s}'
        preview = entry['text'][:50]
        print(f'  {label} {preview!r}', flush=True)

        result = read_activations(entry['text'], target_layers=layers, pool=args.pool)
        if not result:
            print(f'    [WARN] no activations captured', file=sys.stderr)
            failed += 1
        else:
            domain_activations[entry['domain']].append(result)

    if failed:
        print(f'\n  [warn] {failed}/{len(calibration)} prompts produced no activations',
              file=sys.stderr)

    # ── Per-layer centroid analysis ────────────────────────────────────────────
    print()
    print('=' * 72)
    print('LAYER ANALYSIS')
    print('=' * 72)

    all_centroids: dict[int, dict[str, np.ndarray]] = {}
    separability: dict[int, float] = {}

    for layer in layers:
        print(f'\n  Layer {layer}:')

        # Collect vectors (need ≥2 per domain for meaningful centroid)
        domain_vecs: dict[str, list] = {}
        for d in domains:
            vecs = [a[layer] for a in domain_activations[d] if layer in a]
            if len(vecs) >= 2:
                domain_vecs[d] = vecs
            elif vecs:
                print(f'    [skip] {d}: only {len(vecs)} vector, need ≥2')

        if len(domain_vecs) < 2:
            print(f'    [skip] fewer than 2 domains at layer {layer}')
            continue

        # Centroids
        c = {d: centroid(vecs) for d, vecs in domain_vecs.items()}
        all_centroids[layer] = c

        # Intra-domain mean cosine distance
        intra = {d: mean_intra_dist(domain_vecs[d], c[d]) for d in c}
        print(f'    Intra-domain mean cosine distance (lower = tighter cluster):')
        for d in sorted(intra):
            bar = '█' * max(1, int(intra[d] * 80))
            print(f'      {d:15s}: {intra[d]:.4f}  {bar}')

        # Inter-centroid distance matrix
        domain_list = sorted(c.keys())
        cw = 12
        print(f'\n    Inter-centroid cosine distance:')
        print('    ' + ' ' * 15 + ''.join(f'{d[:10]:>{cw}}' for d in domain_list))
        inter_vals = []
        for d1 in domain_list:
            row = f'    {d1[:15]:15s}'
            for d2 in domain_list:
                if d1 == d2:
                    row += f'{"—":>{cw}}'
                else:
                    dist = cosine_dist(c[d1], c[d2])
                    inter_vals.append(dist)
                    row += f'{dist:>{cw}.4f}'
            print(row)

        mean_inter = float(np.mean(inter_vals)) if inter_vals else 0.0
        mean_intra = float(np.mean(list(intra.values())))
        sep = mean_inter / (mean_intra + 1e-9)
        separability[layer] = sep

        print(f'\n    mean_inter={mean_inter:.4f}  mean_intra={mean_intra:.4f}  '
              f'separability={sep:.4f}')

    # ── Optimal layer recommendation ───────────────────────────────────────────
    if not separability:
        print('\nNo separability data — cannot determine optimal layer')
        return

    best_layer = max(separability, key=lambda l: separability[l])

    print()
    print('=' * 72)
    print('OPTIMAL LAYER SELECTION')
    print('=' * 72)
    print(f'  {"Layer":>8}  {"Separability":>14}')
    print(f'  {"-" * 30}')
    for layer in sorted(separability):
        marker = '  ← OPTIMAL' if layer == best_layer else ''
        print(f'  layer {layer:>2}:  {separability[layer]:>14.4f}{marker}')
    print()
    print(f'  Recommendation: read activations at layer {best_layer} for domain classification')
    print(f'  (highest inter/intra ratio = domains most separable relative to internal spread)')

    # ── Janus point analysis ───────────────────────────────────────────────────
    # For 'mixed' domain prompts, show nearest clear-domain centroid
    mixed_entries = [e for e in calibration if e['domain'] == 'mixed']
    mixed_results = domain_activations.get('mixed', [])
    clean_domains = [d for d in sorted(all_centroids.get(best_layer, {})) if d != 'mixed']

    if mixed_entries and mixed_results and clean_domains and best_layer in all_centroids:
        print()
        print('=' * 72)
        print('JANUS POINT ANALYSIS (mixed prompts — nearest domain centroid)')
        print('=' * 72)
        c_best = all_centroids[best_layer]
        for entry, result in zip(mixed_entries, mixed_results):
            if best_layer not in result:
                print(f'  [missing layer {best_layer}]: {entry["text"]!r}')
                continue
            vec = result[best_layer]
            distances = {d: cosine_dist(vec, c_best[d])
                         for d in clean_domains if d in c_best}
            if not distances:
                continue
            nearest = min(distances, key=distances.get)
            print(f'\n  {entry["text"]!r}')
            for d in sorted(distances):
                marker = '  ← nearest' if d == nearest else ''
                print(f'    {d:15s}: {distances[d]:.4f}{marker}')

    # ── Save centroids ─────────────────────────────────────────────────────────
    if args.save:
        save_name = args.save if args.save.endswith('.json') else args.save + '.json'
        save_path = Path(__file__).parent / 'data' / save_name
        save_path.parent.mkdir(parents=True, exist_ok=True)
        save_data = {
            'metadata': {
                'layers': layers,
                'pool': args.pool,
                'domains': domains,
                'n_prompts': len(calibration),
                'optimal_layer': best_layer,
            },
            'separability': {str(l): v for l, v in separability.items()},
            'centroids': {
                str(layer): {d: c.tolist() for d, c in cts.items()}
                for layer, cts in all_centroids.items()
            },
        }
        with open(save_path, 'w') as f:
            json.dump(save_data, f, indent=2)
        print(f'\nCentroids saved: {save_path}')
        print(f'  {len(all_centroids)} layers × {len(domains)} domains')

    print()


if __name__ == '__main__':
    main()
