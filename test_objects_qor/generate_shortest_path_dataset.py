#!/usr/bin/env python3
"""Generate a shortest-path dataset with distractor targets.

Each sample contains:
- an initial 3x3x3 object (object1..object6)
- a predefined sequence of rotations
- a target object that is either the exact transformed result or a distractor
- the full set of shortest paths from initial to target, if any

Distractors are generated from the transformed target using:
- mirror transforms
- safe cube erasures that do not leave cubes floating above them

Outputs:
- dataset.json: samples with initial/sequence/target and shortest paths
- distractors.json: unique distractor objects used by the dataset
- README.md: dataset format summary
"""

from __future__ import annotations

import argparse
import copy
import itertools
import json
import sys
from collections import defaultdict, deque
from pathlib import Path
from typing import Dict, List, Sequence, Tuple


HERE = Path(__file__).parent
REPO_ROOT = HERE.parent
for candidate in HERE.resolve().parents:
    if (candidate / "visualize_cubes_qor.py").exists():
        REPO_ROOT = candidate
        break

sys.path.insert(0, str(REPO_ROOT))

import visualize_cubes_qor as vcq
import visualize_object1_3d as v3d


OBJECTS = [f"object{i}" for i in range(1, 7)]
ROTATIONS = [
    "towards_up",
    "towards_down",
    "towards_left",
    "towards_right",
    "1q",
    "-1q",
]
FACE_ORDER = ["front", "back", "left", "right", "up", "down"]
DETERMINISTIC_TARGET_MODES = ["mirror_x", "mirror_z", "erase_top"]


def clone_faces(faces):
    return {face: copy.deepcopy(matrix) for face, matrix in faces.items()}


def serialize_faces(faces):
    parts = []
    for face in FACE_ORDER:
        matrix = faces.get(face)
        if matrix is None:
            parts.append("None")
        else:
            parts.append("|".join("".join(row) for row in matrix))
    return "\n".join(parts)


def apply_sequence(faces, sequence):
    current = clone_faces(faces)

    for rotation in sequence:
        if rotation in {"1q", "-1q"}:
            current = vcq.apply_in_plane_rotation(current, rotation)
        else:
            current = vcq.apply_rotation_via_prolog(current, rotation)

    return current


def all_sequences(max_len):
    sequences = [[]]

    for length in range(1, max_len + 1):
        for seq in itertools.permutations(ROTATIONS, length):
            sequences.append(list(seq))

    return sequences


def occupancy_from_faces(faces):
    occ, _ = v3d.reconstruct_voxels_from_faces(faces, size=3, fusion="priority")
    return occ


def faces_from_occupancy(occ):
    faces = {}

    for face_name in FACE_ORDER:
        matrix = []
        for r in range(3):
            row = []
            for c in range(3):
                value = "*"
                for layer in range(3):
                    x, y, z = v3d._map_face_to_xyz(face_name, r, c, layer)
                    if 0 <= x < 3 and 0 <= y < 3 and 0 <= z < 3 and occ[x, y, z]:
                        value = ["a", "b", "c"][layer]
                        break
                row.append(value)
            matrix.append(row)
        faces[face_name] = matrix

    return faces


def mirror_occupancy(occ, axis):
    return occ[::-1, :, :] if axis == 0 else occ[:, ::-1, :] if axis == 1 else occ[:, :, ::-1]


def removable_voxels(occ):
    candidates = []
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if not occ[x, y, z]:
                    continue

                # Safe to remove if nothing is stacked above it in the same column.
                if not occ[x, y + 1 :, z].any():
                    candidates.append((x, y, z))

    return candidates


def erase_occupancy(occ, count=1):
    new_occ = occ.copy()
    removed = []

    for _ in range(count):
        candidates = removable_voxels(new_occ)
        if not candidates:
            break

        # Deterministic: remove the highest, then lexicographically earliest.
        candidates.sort(key=lambda t: (-t[1], t[0], t[2]))
        voxel = candidates[0]
        new_occ[voxel] = False
        removed.append(voxel)

    return new_occ, removed


def build_distractor_variants(faces):
    occ = occupancy_from_faces(faces)

    variants = {
        "mirror_x": faces_from_occupancy(mirror_occupancy(occ, 0)),
        "mirror_z": faces_from_occupancy(mirror_occupancy(occ, 2)),
    }

    erased_occ, removed = erase_occupancy(occ, count=1)
    variants["erase_top"] = faces_from_occupancy(erased_occ)

    return variants, removed


def build_rotation_graph(start_faces, max_depth=3):
    start_sig = serialize_faces(start_faces)
    states_by_sig = {
        start_sig: {
            "faces": clone_faces(start_faces),
            "sequence_from_start": [],
        }
    }
    graph = defaultdict(list)
    queue = deque([(start_sig, 0)])
    seen_depth = {start_sig: 0}

    while queue:
        current_sig, depth = queue.popleft()
        current_faces = states_by_sig[current_sig]["faces"]

        if depth >= max_depth:
            continue

        for rotation in ROTATIONS:
            next_faces = apply_sequence(current_faces, [rotation])
            next_sig = serialize_faces(next_faces)
            graph[current_sig].append((rotation, next_sig))

            next_depth = depth + 1
            prev_depth = seen_depth.get(next_sig)

            if prev_depth is None or next_depth < prev_depth:
                seen_depth[next_sig] = next_depth
                states_by_sig[next_sig] = {
                    "faces": next_faces,
                    "sequence_from_start": states_by_sig[current_sig]["sequence_from_start"] + [rotation],
                }
                queue.append((next_sig, next_depth))

    return {
        "start_sig": start_sig,
        "states_by_sig": states_by_sig,
        "graph": dict(graph),
    }


def all_shortest_paths(graph_data, target_sig, max_paths=200):
    start_sig = graph_data["start_sig"]
    graph = graph_data["graph"]

    if target_sig not in graph_data["states_by_sig"]:
        return []

    queue = deque([(start_sig, [])])
    seen_depth = {start_sig: 0}
    best_depth = None
    paths = []

    while queue:
        current_sig, sequence = queue.popleft()
        depth = len(sequence)

        if best_depth is not None and depth > best_depth:
            continue

        if current_sig == target_sig:
            if best_depth is None:
                best_depth = depth

            if len(paths) < max_paths:
                paths.append(sequence)

            continue

        for rotation, next_sig in graph.get(current_sig, []):
            next_depth = depth + 1

            if best_depth is not None and next_depth > best_depth:
                continue

            prev_depth = seen_depth.get(next_sig)
            if prev_depth is not None and prev_depth < next_depth:
                continue

            # Allow same-depth revisits so we keep alternative shortest sequences.
            seen_depth[next_sig] = min(prev_depth, next_depth) if prev_depth is not None else next_depth
            queue.append((next_sig, sequence + [rotation]))

    return paths


def make_sample_id(object_name, sequence, target_mode):
    sequence_name = "original" if not sequence else "__".join(sequence)
    return f"{object_name}__{sequence_name}__{target_mode}"


def generate_dataset(max_sequence_len=2, graph_depth=3):
    entries = []
    distractors = []
    distractor_index = {}

    sequences = all_sequences(max_sequence_len)

    for object_name in OBJECTS:
        base_faces = vcq.extract_faces_from_q3d(object_name)
        graph_data = build_rotation_graph(base_faces, max_depth=graph_depth)
        sample_counter = 0

        for sequence in sequences:
            transformed_faces = apply_sequence(base_faces, sequence)
            target_sig_exact = serialize_faces(transformed_faces)

            variant_map, removed = build_distractor_variants(transformed_faces)

            # Create one exact sample and one distractor sample per sequence.
            target_modes = ["exact", DETERMINISTIC_TARGET_MODES[sample_counter % len(DETERMINISTIC_TARGET_MODES)]]
            sample_counter += 1

            for target_mode in target_modes:
                if target_mode == "exact":
                    target_faces = clone_faces(transformed_faces)
                    target_is_distractor = False
                else:
                    target_faces = clone_faces(variant_map[target_mode])
                    target_is_distractor = True

                sample_id = make_sample_id(object_name, sequence, target_mode)
                target_sig = serialize_faces(target_faces)
                paths = all_shortest_paths(graph_data, target_sig)

                distractor_items = []
                for mode, faces in variant_map.items():
                    distractor_id = f"{sample_id}__distractor__{mode}"
                    distractor_sig = serialize_faces(faces)

                    distractor_record = {
                        "distractor_id": distractor_id,
                        "source_sample_id": sample_id,
                        "mode": mode,
                        "faces": faces,
                    }

                    if distractor_id not in distractor_index:
                        distractor_index[distractor_id] = len(distractors)
                        distractors.append(distractor_record)

                    distractor_items.append(distractor_id)

                entries.append({
                    "sample_id": sample_id,
                    "initial_object": object_name,
                    "initial_faces": clone_faces(base_faces),
                    "sequence": sequence,
                    "sequence_length": len(sequence),
                    "transformed_faces": clone_faces(transformed_faces),
                    "target_mode": target_mode,
                    "target_is_distractor": target_is_distractor,
                    "target_faces": target_faces,
                    "distractor_ids": distractor_items,
                    "erased_voxels": removed if target_mode == "erase_top" else [],
                    "all_shortest_paths": paths,
                    "shortest_path_count": len(paths),
                    "shortest_path_length": len(paths[0]) if paths else None,
                    "solvable": bool(paths),
                })

    summary = {
        "objects": OBJECTS,
        "max_sequence_len": max_sequence_len,
        "graph_depth": graph_depth,
        "sample_count": len(entries),
        "distractor_count": len(distractors),
        "solvable_count": sum(1 for entry in entries if entry["solvable"]),
        "unsolved_count": sum(1 for entry in entries if not entry["solvable"]),
    }

    return {
        "summary": summary,
        "entries": entries,
        "distractors": distractors,
    }


def write_json(path, payload):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def write_readme(path, summary):
    text = f"""# Shortest Path Dataset

This dataset was generated from the six 3x3x3 objects in `q3d-ex.pl`.

## Files

- `dataset.json`: samples with initial object, action sequence, target, distractor references, and all shortest paths.
- `distractors.json`: unique distractor objects used by the samples.
- `summary.json`: dataset counts.

## Sample Fields

- `initial_object`: source object name.
- `sequence`: predefined rotation sequence used to derive the base transformed object.
- `target_mode`: `exact`, `mirror_x`, `mirror_z`, or `erase_top`.
- `target_is_distractor`: whether the target was replaced by a distractor variant.
- `all_shortest_paths`: all minimal action sequences from the initial object to the target, if any.

## Summary

- objects: {summary['objects']}
- max_sequence_len: {summary['max_sequence_len']}
- graph_depth: {summary['graph_depth']}
- sample_count: {summary['sample_count']}
- distractor_count: {summary['distractor_count']}
- solvable_count: {summary['solvable_count']}
- unsolved_count: {summary['unsolved_count']}
"""
    path.write_text(text, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Generate shortest-path dataset with distractors.")
    parser.add_argument("--max-sequence-len", type=int, default=2)
    parser.add_argument("--graph-depth", type=int, default=3)
    parser.add_argument("--output-dir", type=str, default=str(HERE / "shortest_path_dataset"))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    dataset = generate_dataset(max_sequence_len=args.max_sequence_len, graph_depth=args.graph_depth)

    write_json(output_dir / "dataset.json", {
        "summary": dataset["summary"],
        "samples": dataset["entries"],
    })

    write_json(output_dir / "distractors.json", {
        "summary": {
            "count": len(dataset["distractors"]),
        },
        "distractors": dataset["distractors"],
    })

    write_json(output_dir / "summary.json", dataset["summary"])
    write_readme(output_dir / "README.md", dataset["summary"])

    print(json.dumps(dataset["summary"], indent=2))
    print(f"Wrote dataset to {output_dir}")


if __name__ == "__main__":
    main()