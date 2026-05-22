#!/usr/bin/env python3
"""Streamlit viewer for the shortest-path dataset results.

This app shows one row per sample with:
- initial object previews (2D cube net + 3D reconstruction)
- target object previews
- the predefined sequence used to create the sample target
- all shortest paths found by the solver, if any
- distractor and solvability metadata
"""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
from matplotlib.patches import Rectangle
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


HERE = Path(__file__).parent
DATASET_PATH = HERE / "test_objects_qor" / "shortest_path_dataset" / "dataset.json"
DISTRACTOR_PATH = HERE / "test_objects_qor" / "shortest_path_dataset" / "distractors.json"


OBJECT_LABEL_COLORS = {
    "front": "#E53935",
    "right": "#1E88E5",
    "up": "#FDD835",
    "back": "#43A047",
    "left": "#FB8C00",
    "down": "#8E24AA",
}

DEPTH_ALPHA = {
    "a": 1.0,
    "b": 0.72,
    "c": 0.44,
    "d": 0.24,
    "e": 0.10,
}

FACE_ORDER = ["front", "back", "left", "right", "up", "down"]
FACE_POSITIONS = {
    "up": (0, 1),
    "left": (1, 0),
    "front": (1, 1),
    "right": (1, 2),
    "down": (2, 1),
    "back": (2, 2),
}


def natural_sort_key(name):
    match = re.search(r"(\d+)$", name)
    if match:
        return name[: match.start()], int(match.group(1))
    return name, 0


def load_dataset():
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_distractors():
    if not DISTRACTOR_PATH.exists():
        return {"summary": {"count": 0}, "distractors": []}
    with open(DISTRACTOR_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def face_color(face_name):
    return OBJECT_LABEL_COLORS.get(face_name, "#9E9E9E")


def cell_color(face_name, value, transparent=True):
    if value == "*":
        return mcolors.to_rgba("#C8C8C8", 1.0)
    alpha = DEPTH_ALPHA.get(value, 0.35) if transparent else 1.0
    return mcolors.to_rgba(face_color(face_name), alpha)


def map_face_to_xyz(face_name, r, c, layer):
    if face_name == "front":
        return c, r, layer
    if face_name == "back":
        return 2 - c, r, 2 - layer
    if face_name == "left":
        return layer, r, 2 - c
    if face_name == "right":
        return 2 - layer, r, c
    if face_name == "up":
        return c, layer, 2 - r
    if face_name == "down":
        return c, 2 - layer, r
    return -1, -1, -1


def reconstruct_voxels_from_faces(faces, size=3):
    occ = np.zeros((size, size, size), dtype=bool)
    colors = np.zeros((size, size, size, 4), dtype=float)

    for face_name in FACE_ORDER:
        mat = faces.get(face_name)
        if mat is None:
            continue

        for r in range(len(mat)):
            for c in range(len(mat[r])):
                value = mat[r][c]
                if value == "*":
                    continue

                layer = {"a": 0, "b": 1, "c": 2, "d": 2, "e": 2}.get(value, 2)
                x, y, z = map_face_to_xyz(face_name, r, c, layer)

                if 0 <= x < size and 0 <= y < size and 0 <= z < size and not occ[x, y, z]:
                    occ[x, y, z] = True
                    colors[x, y, z] = cell_color(face_name, value, transparent=False)

    return occ, colors


def apply_axis_ops(occ, colors, perm=(2, 0, 1), flips=(1, 0, 1)):
    occ_t = np.transpose(occ, perm)
    colors_t = np.transpose(colors, perm + (3,))

    for axis, do_flip in enumerate(flips):
        if do_flip:
            occ_t = np.flip(occ_t, axis=axis)
            colors_t = np.flip(colors_t, axis=axis)

    return occ_t, colors_t


def face_tile_vertices(face_name, row, col, cell_size=1.0, cube_size=3.0, offset=0.0):
    x0 = col * cell_size
    x1 = x0 + cell_size
    y0 = row * cell_size
    y1 = y0 + cell_size

    if face_name == "front":
        z = cube_size + offset
        return [[x0, y0, z], [x1, y0, z], [x1, y1, z], [x0, y1, z]]
    if face_name == "back":
        z = 0.0 - offset
        return [[x1, y0, z], [x0, y0, z], [x0, y1, z], [x1, y1, z]]
    if face_name == "right":
        x = cube_size + offset
        return [[x, y0, x0], [x, y0, x1], [x, y1, x1], [x, y1, x0]]
    if face_name == "left":
        x = 0.0 - offset
        return [[x, y0, x1], [x, y0, x0], [x, y1, x0], [x, y1, x1]]
    if face_name == "up":
        y = 0.0 - offset
        return [[x0, y, x1], [x1, y, x1], [x1, y, x0], [x0, y, x0]]
    if face_name == "down":
        y = cube_size + offset
        return [[x0, y, x0], [x1, y, x0], [x1, y, x1], [x0, y, x1]]
    return []


def draw_cube_grid_compact(faces, title=None, face_palette=None, figsize=(3.0, 3.0)):
    fig, axes = plt.subplots(3, 3, figsize=figsize)

    if title:
        fig.suptitle(title, fontsize=9, fontweight="bold")

    for row in axes:
        for ax in row:
            ax.set_visible(False)

    for face_name, (row, col) in FACE_POSITIONS.items():
        matrix = faces.get(face_name)
        if matrix is None:
            continue

        ax = axes[row, col]
        ax.set_visible(True)
        rows = len(matrix)
        cols = len(matrix[0]) if matrix else 0

        ax.set_xlim(-0.5, cols - 0.5)
        ax.set_ylim(-0.5, rows - 0.5)
        ax.set_aspect("equal")
        ax.invert_yaxis()
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(face_name.upper(), fontsize=6, fontweight="bold", pad=1)

        for r, row_data in enumerate(matrix):
            for c, value in enumerate(row_data):
                rect = Rectangle(
                    (c - 0.4, r - 0.4),
                    0.8,
                    0.8,
                    facecolor=cell_color(face_name, value, transparent=True),
                    edgecolor="black",
                    linewidth=0.6,
                )
                ax.add_patch(rect)
                ax.text(c, r, value, ha="center", va="center", fontsize=6, fontweight="bold")

    plt.tight_layout(pad=0.2)
    return fig


def voxel_face_vertices(x, y, z, face_name, epsilon=0.01):
    x0, x1 = x, x + 1
    y0, y1 = y, y + 1
    z0, z1 = z, z + 1

    if face_name == "front":
        z1 += epsilon
        return [[x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]]
    if face_name == "back":
        z0 -= epsilon
        return [[x1, y0, z0], [x0, y0, z0], [x0, y1, z0], [x1, y1, z0]]
    if face_name == "left":
        x0 -= epsilon
        return [[x0, y0, z1], [x0, y0, z0], [x0, y1, z0], [x0, y1, z1]]
    if face_name == "right":
        x1 += epsilon
        return [[x1, y0, z0], [x1, y0, z1], [x1, y1, z1], [x1, y1, z0]]
    if face_name == "up":
        y0 -= epsilon
        return [[x0, y0, z1], [x1, y0, z1], [x1, y0, z0], [x0, y0, z0]]
    if face_name == "down":
        y1 += epsilon
        return [[x0, y1, z0], [x1, y1, z0], [x1, y1, z1], [x0, y1, z1]]
    return []


def _compute_orig_normal_to_face():
    mapping = {}
    for face_name in ["front", "right", "back", "left", "up", "down"]:
        row, col, layer = 1, 1, 0
        x0, y0, z0 = map_face_to_xyz(face_name, row, col, layer)
        x1, y1, z1 = map_face_to_xyz(face_name, row, col, 1)
        vector = (x1 - x0, y1 - y0, z1 - z0)
        outward = (-int(np.sign(vector[0])), -int(np.sign(vector[1])), -int(np.sign(vector[2])))
        mapping[outward] = face_name
    return mapping


_ORIG_NORMAL_TO_FACE = _compute_orig_normal_to_face()


def _unapply_axis_ops_to_coords(coord_t):
    perm = (2, 0, 1)
    flips = (1, 0, 1)

    coord_after_unflip = [0, 0, 0]
    for axis in range(3):
        value = coord_t[axis]
        if flips[axis]:
            value = 2 - value
        coord_after_unflip[axis] = value

    inv_perm = [0, 0, 0]
    for transformed_axis, original_axis in enumerate(perm):
        inv_perm[original_axis] = transformed_axis

    coord_orig = [0, 0, 0]
    for original_axis in range(3):
        coord_orig[original_axis] = coord_after_unflip[inv_perm[original_axis]]
    return tuple(coord_orig)


def _transform_vector_to_original(vec_t):
    perm = (2, 0, 1)
    flips = (1, 0, 1)

    inv_perm = [0, 0, 0]
    for transformed_axis, original_axis in enumerate(perm):
        inv_perm[original_axis] = transformed_axis

    vec_orig = [0, 0, 0]
    for original_axis in range(3):
        component = vec_t[inv_perm[original_axis]]
        if flips[inv_perm[original_axis]]:
            component = -component
        vec_orig[original_axis] = component
    return tuple(vec_orig)


def _voxel_face_vertices_transformed(x, y, z, direction, offset=0.02):
    x0, x1 = x, x + 1
    y0, y1 = y, y + 1
    z0, z1 = z, z + 1

    if direction == "+x":
        x1 += offset
        return [[x1, y0, z0], [x1, y1, z0], [x1, y1, z1], [x1, y0, z1]]
    if direction == "-x":
        x0 -= offset
        return [[x0, y0, z1], [x0, y1, z1], [x0, y1, z0], [x0, y0, z0]]
    if direction == "+y":
        y1 += offset
        return [[x0, y1, z0], [x1, y1, z0], [x1, y1, z1], [x0, y1, z1]]
    if direction == "-y":
        y0 -= offset
        return [[x0, y0, z1], [x1, y0, z1], [x1, y0, z0], [x0, y0, z0]]
    if direction == "+z":
        z1 += offset
        return [[x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]]
    if direction == "-z":
        z0 -= offset
        return [[x0, y1, z0], [x1, y1, z0], [x1, y0, z0], [x0, y0, z0]]

    return []


def draw_voxel_compact(faces, title=None, elev=30, azim=45, figsize=(3.0, 3.0)):
    occ, _ = reconstruct_voxels_from_faces(faces, size=3)
    occ_t, _ = apply_axis_ops(occ, np.zeros(occ.shape + (4,), dtype=float))

    proj_map = {}
    for face_name in FACE_ORDER:
        matrix = faces.get(face_name)
        if matrix is None:
            continue

        for r, row in enumerate(matrix):
            for c, value in enumerate(row):
                if value == "*":
                    continue

                layer = {"a": 0, "b": 1, "c": 2, "d": 2, "e": 2}.get(value, 2)
                x_o, y_o, z_o = map_face_to_xyz(face_name, r, c, layer)
                if 0 <= x_o < 3 and 0 <= y_o < 3 and 0 <= z_o < 3:
                    proj_map[(x_o, y_o, z_o, face_name)] = value

    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(111, projection="3d")

    facecolors = np.empty(occ_t.shape + (4,), dtype=float)
    facecolors[...] = mcolors.to_rgba("#D8D8D8", 1.0)
    facecolors[~occ_t] = (0, 0, 0, 0)

    ax.voxels(occ_t, facecolors=facecolors, edgecolor="k", linewidth=0.5)

    neighbors = [
        ((1, 0, 0), "+x"),
        ((-1, 0, 0), "-x"),
        ((0, 1, 0), "+y"),
        ((0, -1, 0), "-y"),
        ((0, 0, 1), "+z"),
        ((0, 0, -1), "-z"),
    ]

    size = occ_t.shape[0]
    for x in range(size):
        for y in range(size):
            for z in range(size):
                if not occ_t[x, y, z]:
                    continue

                for (dx, dy, dz), direction in neighbors:
                    nx, ny, nz = x + dx, y + dy, z + dz
                    exposed = not (0 <= nx < size and 0 <= ny < size and 0 <= nz < size and occ_t[nx, ny, nz])
                    if not exposed:
                        continue

                    orig_coord = _unapply_axis_ops_to_coords((x, y, z))
                    face_name = _ORIG_NORMAL_TO_FACE.get(_transform_vector_to_original((dx, dy, dz)))

                    color = None
                    if face_name is not None:
                        value = proj_map.get((orig_coord[0], orig_coord[1], orig_coord[2], face_name))
                        if value is not None:
                            color = cell_color(face_name, value, transparent=False)

                    if color is None:
                        color = mcolors.to_rgba("#C8C8C8", 1.0)

                    verts = _voxel_face_vertices_transformed(x, y, z, direction)
                    if not verts:
                        continue

                    poly = Poly3DCollection([verts], facecolor=color, edgecolor="#202020", linewidth=0.25)
                    ax.add_collection3d(poly)

    ax.set_xlim(0, 3)
    ax.set_ylim(0, 3)
    ax.set_zlim(0, 3)
    ax.set_box_aspect((1, 1, 1))
    ax.set_axis_off()
    ax.view_init(elev=elev, azim=azim)

    if title:
        ax.set_title(title, fontsize=9, fontweight="bold")

    plt.tight_layout(pad=0.1)
    return fig


@st.cache_data(show_spinner=False)
def load_dataset():
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(show_spinner=False)
def load_distractors():
    if not DISTRACTOR_PATH.exists():
        return {"summary": {"count": 0}, "distractors": []}
    with open(DISTRACTOR_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def short_sequence(sequence):
    if not sequence:
        return "original / no rotation"
    return " → ".join(sequence)


def dataset_summary_table(dataset):
    return {
        "objects": ", ".join(dataset["summary"]["objects"]),
        "samples": dataset["summary"]["sample_count"],
        "distractors": dataset["summary"]["distractor_count"],
        "solvable": dataset["summary"]["solvable_count"],
        "unsolved": dataset["summary"]["unsolved_count"],
        "max_sequence_len": dataset["summary"]["max_sequence_len"],
        "graph_depth": dataset["summary"]["graph_depth"],
    }


def make_sample_label(sample):
    return f"{sample['sample_id']} | {sample['initial_object']} | {sample['target_mode']}"


def render_row(sample, row_index):
    initial_faces = sample["initial_faces"]
    target_faces = sample["target_faces"]
    sequence = sample["sequence"]
    shortest_paths = sample.get("all_shortest_paths", [])

    st.markdown(f"### {row_index + 1}. {sample['sample_id']}")

    c1, c2, c3 = st.columns([1.15, 1.25, 1.15])

    with c1:
        st.markdown("**Initial 2D**")
        fig = draw_cube_grid_compact(initial_faces, title=sample["initial_object"])
        st.pyplot(fig, use_container_width=False)
        plt.close(fig)

        st.markdown("**Initial 3D**")
        fig = draw_voxel_compact(initial_faces, title=sample["initial_object"])
        st.pyplot(fig, use_container_width=False)
        plt.close(fig)

    with c2:
        st.markdown("**Sequence / Solver**")
        st.write({
            "generated_sequence": short_sequence(sequence),
            "sequence_length": sample["sequence_length"],
            "target_mode": sample["target_mode"],
            "target_is_distractor": sample["target_is_distractor"],
            "solvable": sample["solvable"],
            "shortest_path_count": sample.get("shortest_path_count", 0),
            "shortest_path_length": sample.get("shortest_path_length"),
        })

        if shortest_paths:
            with st.expander("All shortest paths", expanded=False):
                for idx, path in enumerate(shortest_paths, start=1):
                    st.write(f"{idx}. {short_sequence(path)}")
        else:
            st.caption("No path found from the initial object to this target.")

        if sample.get("erased_voxels"):
            st.caption(f"Erased voxels: {sample['erased_voxels']}")

    with c3:
        st.markdown("**Target 2D / 3D**")
        st.caption(sample["target_mode"])
        fig = draw_cube_grid_compact(target_faces, title=sample["target_mode"])
        st.pyplot(fig, use_container_width=False)
        plt.close(fig)

        fig = draw_voxel_compact(target_faces, title=f"Target: {sample['target_mode']}")
        st.pyplot(fig, use_container_width=False)
        plt.close(fig)


def main():
    st.set_page_config(page_title="Shortest Path Dataset Results", layout="wide")
    st.title("Shortest Path Dataset Results")
    st.write("Rows show the initial object, its matrix + 3D preview, the generated sequence, and the target object.")

    dataset = load_dataset()
    distractors = load_distractors()

    summary = dataset_summary_table(dataset)
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Samples", summary["samples"])
    s2.metric("Distractors", summary["distractors"])
    s3.metric("Solvable", summary["solvable"])
    s4.metric("Unsolved", summary["unsolved"])

    with st.expander("Dataset summary", expanded=False):
        st.write(summary)
        st.write({"distractor_file_count": distractors.get("summary", {}).get("count", 0)})

    samples = dataset["samples"]

    col_a, col_b, col_c, col_d, col_e = st.columns(5)
    with col_a:
        object_filter = st.multiselect("Initial object", dataset["summary"]["objects"], default=dataset["summary"]["objects"])
    with col_b:
        mode_filter = st.multiselect("Target mode", sorted({sample["target_mode"] for sample in samples}), default=sorted({sample["target_mode"] for sample in samples}))
    with col_c:
        distractor_only = st.checkbox("Distractor targets only", value=False)
    with col_d:
        solvable_only = st.checkbox("Solved only", value=False)
    with col_e:
        page_size = st.number_input("Rows per page", min_value=1, max_value=50, value=12, step=1)

    filtered = [
        sample for sample in samples
        if sample["initial_object"] in object_filter
        and sample["target_mode"] in mode_filter
        and (not distractor_only or sample["target_is_distractor"])
        and (not solvable_only or sample["solvable"])
    ]

    st.caption(f"Showing {len(filtered)} of {len(samples)} samples")

    if not filtered:
        st.warning("No samples match the filters.")
        return

    page_count = max(1, (len(filtered) + page_size - 1) // page_size)
    page = st.slider("Page", min_value=1, max_value=page_count, value=1)
    start = (page - 1) * page_size
    end = min(len(filtered), start + page_size)

    for row_index, sample in enumerate(filtered[start:end], start=start):
        with st.container():
            render_row(sample, row_index)


if __name__ == "__main__":
    main()