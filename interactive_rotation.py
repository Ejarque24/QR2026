#!/usr/bin/env python3
"""
Interactive FRU rotation inference demo.

This app creates a small interactive dataset for object1 to object6.

For each object:
- fixed object = original object from q3d-ex.pl
- transformed object = movable copy
- inferred rotation = shortest detected sequence from fixed FRU to transformed FRU

Supported moves:
- towards_up
- towards_down
- towards_left
- towards_right
- 1q
- -1q

Requirements:
    pip install streamlit matplotlib numpy pandas

Run:
    streamlit run interactive_inference_demo.py

Assumes these files are in the same folder:
- interactive_inference_demo.py
- visualize_cubes_qor.py
- q3d-ex.pl
- rotation_qor_inspired.pl
"""

from collections import deque, defaultdict
import copy
import re
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.patches import Rectangle
import streamlit as st

import visualize_cubes_qor as vcq

import io
import hashlib
import networkx as nx


# ============================================================================
# CONFIG
# ============================================================================

OBJECT_NAMES = [
    "object1",
    "object2",
    "object3",
    "object4",
    "object5",
    "object6",
]

Q3D_PATH = Path(__file__).parent / "q3d-ex.pl"

FACES = [
    "front",
    "back",
    "left",
    "right",
    "up",
    "down",
]

FRU_FACES = [
    "front",
    "right",
    "up",
]

NORMAL_ROTATIONS = [
    "towards_up",
    "towards_down",
    "towards_left",
    "towards_right",
]

IN_PLANE_ROTATIONS = [
    "1q",
    "-1q",
]

# Display names for in-plane rotations. Keep short forms for graphs only.
IN_PLANE_DISPLAY = {
    "1q": "towards-up-right",
    "-1q": "towards-up-left",
}

def display_rotation(rot, for_graph=False):
    if for_graph:
        return rot
    return IN_PLANE_DISPLAY.get(rot, rot)

def display_sequence(sequence, for_graph=False):
    if not sequence:
        return "original / no rotation"
    return " → ".join(display_rotation(r, for_graph=for_graph) for r in sequence)

ALL_ROTATIONS = NORMAL_ROTATIONS + IN_PLANE_ROTATIONS

DEPTH_TO_LAYER = {
    "a": 0,
    "b": 1,
    "c": 2,
    "d": 2,
    "e": 2,
}

DEFAULT_PERM = (2, 0, 1)
DEFAULT_FLIPS = (1, 0, 1)
DEFAULT_VOXEL_COLOR = "#FFD700"

DEFAULT_FACE_PALETTE = {
    "front": "front",
    "right": "right",
    "up": "up",
    "back": "back",
    "left": "left",
    "down": "down",
}

ROTATION_FACE_TARGETS = {
    "towards_up": {
        "front": "up",
        "up": "back",
        "back": "down",
        "down": "front",
        "left": "left",
        "right": "right",
    },
    "towards_down": {
        "front": "down",
        "down": "back",
        "back": "up",
        "up": "front",
        "left": "left",
        "right": "right",
    },
    "towards_left": {
        "right": "front",
        "front": "left",
        "left": "back",
        "back": "right",
        "up": "up",
        "down": "down",
    },
    "towards_right": {
        "left": "front",
        "front": "right",
        "right": "back",
        "back": "left",
        "up": "up",
        "down": "down",
    },
    "1q": {
        "front": "front",
        "back": "back",
        "up": "right",
        "right": "down",
        "down": "left",
        "left": "up",
    },
    "-1q": {
        "front": "front",
        "back": "back",
        "up": "left",
        "left": "down",
        "down": "right",
        "right": "up",
    },
}


def rotate_face_palette(face_palette, rotation_name):
    mapping = ROTATION_FACE_TARGETS.get(rotation_name)

    if not mapping:
        return copy.deepcopy(face_palette)

    new_palette = {}
    for source_face, target_face in mapping.items():
        new_palette[target_face] = face_palette.get(source_face, source_face)

    for face_name in DEFAULT_FACE_PALETTE:
        new_palette.setdefault(face_name, face_palette.get(face_name, face_name))

    return new_palette


def resolve_face_palette(face_palette, face_name):
    return (face_palette or DEFAULT_FACE_PALETTE).get(face_name, face_name)

FACE_VIEW_COLORS = {
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


def face_view_color(face_name):
    return FACE_VIEW_COLORS.get(face_name, "#9E9E9E")


def face_cell_rgba(face_name, value, transparent=True):
    if value == "*":
        return mcolors.to_rgba("#C8C8C8", 1.0)

    alpha = DEPTH_ALPHA.get(value, 0.35) if transparent else 1.0
    return mcolors.to_rgba(face_view_color(face_name), alpha)


def face_cell_rgb(face_name, value):
    return face_cell_rgba(face_name, value, transparent=False)


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


def add_face_overlays(ax, faces, depth_tinted=False, offset=0.02):
    for face_name in ["front", "back", "left", "right", "up", "down"]:
        matrix = faces.get(face_name)

        if matrix is None:
            continue

        for r, row in enumerate(matrix):
            for c, value in enumerate(row):
                vertices = face_tile_vertices(face_name, r, c, offset=offset)

                if not vertices:
                    continue

                poly = Poly3DCollection(
                    [vertices],
                    facecolor=face_cell_rgba(
                        face_name,
                        value,
                        transparent=depth_tinted,
                    ),
                    edgecolor="#202020",
                    linewidth=0.2,
                )
                ax.add_collection3d(poly)


def build_face_surface_data(face_name, matrix):
    grid = np.linspace(0, 3, 4)

    if face_name == "front":
        x, y = np.meshgrid(grid, grid[::-1])
        z = np.full((4, 4), 3.0)
    elif face_name == "back":
        x, y = np.meshgrid(grid[::-1], grid[::-1])
        z = np.full((4, 4), 0.0)
    elif face_name == "right":
        z, y = np.meshgrid(grid, grid[::-1])
        x = np.full((4, 4), 3.0)
    elif face_name == "left":
        z, y = np.meshgrid(grid[::-1], grid[::-1])
        x = np.full((4, 4), 0.0)
    elif face_name == "up":
        x, z = np.meshgrid(grid, grid[::-1])
        y = np.full((4, 4), 0.0)
    elif face_name == "down":
        x, z = np.meshgrid(grid, grid)
        y = np.full((4, 4), 3.0)
    else:
        return None, None, None

    facecolors = np.empty((3, 3, 4), dtype=float)

    for r, row in enumerate(matrix):
        for c, value in enumerate(row):
            facecolors[r, c] = face_cell_rgb(face_name, value)

    return x, y, z, facecolors


def draw_surface_cube_compact(
    faces,
    title=None,
    figsize=(2.25, 2.25),
    elev=30,
    azim=45,
    depth_tinted=False,
):
    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(111, projection="3d")

    for face_name in ["front", "back", "left", "right", "up", "down"]:
        matrix = faces.get(face_name)

        if matrix is None:
            continue

        x, y, z, facecolors = build_face_surface_data(face_name, matrix)

        if x is None:
            continue

        if depth_tinted:
            depth_facecolors = np.empty_like(facecolors)
            for r, row in enumerate(matrix):
                for c, value in enumerate(row):
                    depth_facecolors[r, c] = face_cell_rgba(
                        face_name,
                        value,
                        transparent=True,
                    )
            facecolors = depth_facecolors

        ax.plot_surface(
            x,
            y,
            z,
            facecolors=facecolors,
            shade=False,
            edgecolor="#202020",
            linewidth=0.3,
            antialiased=False,
        )

    ax.set_xlim(0, 3)
    ax.set_ylim(0, 3)
    ax.set_zlim(0, 3)
    ax.set_box_aspect((1, 1, 1))
    ax.set_axis_off()
    ax.view_init(elev=elev, azim=azim)

    if title:
        ax.set_title(title, fontsize=8, fontweight="bold")

    plt.tight_layout(pad=0.05)
    return fig


def draw_face_tile_cube_compact(
    faces,
    title=None,
    figsize=(2.25, 2.25),
    elev=30,
    azim=45,
    depth_tinted=False,
):
    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(111, projection="3d")

    for face_name in ["front", "back", "left", "right", "up", "down"]:
        matrix = faces.get(face_name)

        if matrix is None:
            continue

        for r, row in enumerate(matrix):
            for c, value in enumerate(row):
                vertices = face_tile_vertices(face_name, r, c)

                if not vertices:
                    continue

                poly = Poly3DCollection(
                    [vertices],
                    facecolor=face_cell_rgba(
                        face_name,
                        value,
                        transparent=depth_tinted,
                    ),
                    edgecolor="#202020",
                    linewidth=0.25,
                )
                ax.add_collection3d(poly)

    wire_color = "#2E2E2E"
    corners = np.array([
        [0, 0, 0],
        [3, 0, 0],
        [3, 3, 0],
        [0, 3, 0],
        [0, 0, 3],
        [3, 0, 3],
        [3, 3, 3],
        [0, 3, 3],
    ])

    edges = [
        (0, 1), (1, 2), (2, 3), (3, 0),
        (4, 5), (5, 6), (6, 7), (7, 4),
        (0, 4), (1, 5), (2, 6), (3, 7),
    ]

    for a, b in edges:
        xs = [corners[a][0], corners[b][0]]
        ys = [corners[a][1], corners[b][1]]
        zs = [corners[a][2], corners[b][2]]
        ax.plot(xs, ys, zs, color=wire_color, linewidth=1.0)

    ax.set_xlim(0, 3)
    ax.set_ylim(0, 3)
    ax.set_zlim(0, 3)
    ax.set_box_aspect((1, 1, 1))
    ax.set_axis_off()
    ax.view_init(elev=elev, azim=azim)

    if title:
        ax.set_title(title, fontsize=8, fontweight="bold")

    plt.tight_layout(pad=0.05)
    return fig


# ============================================================================
# SIGNATURE HELPERS
# ============================================================================

def matrix_signature(matrix):
    return tuple(tuple(row) for row in matrix)


def full_cube_signature(faces):
    return tuple(
        (face, matrix_signature(faces[face]))
        for face in FACES
    )


def fru_signature(faces_or_fru):
    return tuple(
        (face, matrix_signature(faces_or_fru[face]))
        for face in FRU_FACES
    )


def format_sequence(sequence):
    if not sequence:
        return "original / no rotation"

    return " → ".join(sequence)


def short_sequence(sequence, max_chars=80):
    text = format_sequence(sequence)

    if len(text) <= max_chars:
        return text

    return text[:max_chars - 3] + "..."


# ============================================================================
# OBJECT LOADING
# ============================================================================

@st.cache_data(show_spinner=False)
def load_faces_for_object(object_name):
    faces = vcq.extract_faces_from_q3d(object_name)

    required = ["front", "back", "left", "right", "up", "down"]

    if not all(faces.get(face) is not None for face in required):
        raise ValueError(f"{object_name} does not have all six faces.")

    return faces


def initialize_session_state():
    if "fixed_faces" not in st.session_state:
        st.session_state.fixed_faces = {}

    if "transformed_faces" not in st.session_state:
        st.session_state.transformed_faces = {}

    if "actual_history" not in st.session_state:
        st.session_state.actual_history = {}

    if "face_palettes" not in st.session_state:
        st.session_state.face_palettes = {}

    for object_name in OBJECT_NAMES:
        if object_name not in st.session_state.fixed_faces:
            faces = load_faces_for_object(object_name)

            st.session_state.fixed_faces[object_name] = copy.deepcopy(faces)
            st.session_state.transformed_faces[object_name] = copy.deepcopy(faces)
            st.session_state.actual_history[object_name] = []
            st.session_state.face_palettes[object_name] = copy.deepcopy(DEFAULT_FACE_PALETTE)


# ============================================================================
# ROTATION APPLICATION
# ============================================================================

def apply_rotation(faces, rotation):
    if rotation in NORMAL_ROTATIONS:
        return vcq.apply_rotation_via_prolog(faces, rotation)

    if rotation in IN_PLANE_ROTATIONS:
        return vcq.apply_in_plane_rotation(faces, rotation)

    raise ValueError(f"Unknown rotation: {rotation}")


def move_transformed_object(object_name, rotation):
    current = st.session_state.transformed_faces[object_name]
    current_palette = st.session_state.face_palettes.get(
        object_name,
        copy.deepcopy(DEFAULT_FACE_PALETTE),
    )
    rotated = apply_rotation(current, rotation)

    st.session_state.transformed_faces[object_name] = rotated
    st.session_state.face_palettes[object_name] = rotate_face_palette(
        current_palette,
        rotation,
    )
    st.session_state.actual_history[object_name].append(rotation)


def reset_transformed_object(object_name):
    st.session_state.transformed_faces[object_name] = copy.deepcopy(
        st.session_state.fixed_faces[object_name]
    )
    st.session_state.actual_history[object_name] = []
    st.session_state.face_palettes[object_name] = copy.deepcopy(DEFAULT_FACE_PALETTE)


def reset_all_objects():
    for object_name in OBJECT_NAMES:
        reset_transformed_object(object_name)


# ============================================================================
# ROTATION GRAPH / INFERENCE ENGINE
# ============================================================================

@st.cache_data(show_spinner=True)
def build_rotation_graph_for_object(object_name):
    """
    Build the complete reachable rotation graph for one object.

    Node:
        full 6-face cube state

    Edge:
        one rotation operation

    This avoids blind sequence search.
    """
    original_faces = load_faces_for_object(object_name)

    start_faces = copy.deepcopy(original_faces)
    start_sig = full_cube_signature(start_faces)

    states_by_sig = {
        start_sig: {
            "signature": start_sig,
            "faces": start_faces,
            "sequence_from_original": [],
        }
    }

    graph = defaultdict(list)
    queue = deque([start_sig])

    while queue:
        current_sig = queue.popleft()
        current_state = states_by_sig[current_sig]
        current_faces = current_state["faces"]
        current_sequence = current_state["sequence_from_original"]

        for rotation in ALL_ROTATIONS:
            next_faces = apply_rotation(current_faces, rotation)
            next_sig = full_cube_signature(next_faces)

            graph[current_sig].append((rotation, next_sig))

            if next_sig not in states_by_sig:
                states_by_sig[next_sig] = {
                    "signature": next_sig,
                    "faces": next_faces,
                    "sequence_from_original": current_sequence + [rotation],
                }

                queue.append(next_sig)

    fru_index = defaultdict(list)

    for sig, state in states_by_sig.items():
        fsig = fru_signature(state["faces"])
        fru_index[fsig].append(sig)

    return {
        "states_by_sig": dict(states_by_sig),
        "graph": dict(graph),
        "fru_index": dict(fru_index),
    }


def shortest_paths_between_state_sets(
    graph,
    source_sigs,
    target_sigs,
    max_paths=20,
):
    """
    Find shortest paths from any source state to any target state.
    """
    target_sigs = set(target_sigs)

    queue = deque()
    visited_depth = {}

    for source_sig in source_sigs:
        queue.append((source_sig, []))
        visited_depth[source_sig] = 0

    paths = []
    best_depth = None

    while queue:
        current_sig, sequence = queue.popleft()
        depth = len(sequence)

        if best_depth is not None and depth > best_depth:
            continue

        if current_sig in target_sigs:
            best_depth = depth

            if len(paths) < max_paths:
                paths.append(sequence)

            continue

        for rotation, next_sig in graph.get(current_sig, []):
            next_depth = depth + 1

            if best_depth is not None and next_depth > best_depth:
                continue

            old_depth = visited_depth.get(next_sig)

            if old_depth is not None and old_depth < next_depth:
                continue

            visited_depth[next_sig] = next_depth
            queue.append((next_sig, sequence + [rotation]))

    return paths

# ============================================================================
# GRAPH EXTRACTION / VISUALIZATION HELPERS
# ============================================================================

def stable_hash(value, n=10):
    """
    Create a short stable hash for long signatures.
    Useful for CSV/GraphML exports without storing huge tuple strings.
    """
    text = repr(value).encode("utf-8")
    return hashlib.md5(text).hexdigest()[:n]


def build_graph_label_maps(graph_data):
    """
    Assign readable node names S0, S1, S2, ... to full cube signatures.

    The order follows the insertion order of states_by_sig, which comes
    from the breadth-first graph construction.
    """
    states_by_sig = graph_data["states_by_sig"]

    sig_to_label = {}
    label_to_sig = {}

    for idx, sig in enumerate(states_by_sig.keys()):
        label = f"S{idx}"
        sig_to_label[sig] = label
        label_to_sig[label] = sig

    return sig_to_label, label_to_sig


def build_rotation_graph_tables(graph_data):
    """
    Create two pandas DataFrames:
    - nodes_df: readable node information
    - edges_df: labelled rotation edges
    """
    states_by_sig = graph_data["states_by_sig"]
    graph = graph_data["graph"]
    fru_index = graph_data["fru_index"]

    sig_to_label, _ = build_graph_label_maps(graph_data)

    node_rows = []

    for sig, state in states_by_sig.items():
        label = sig_to_label[sig]
        sequence = state["sequence_from_original"]
        fsig = fru_signature(state["faces"])

        node_rows.append({
            "node": label,
            "depth_from_original": len(sequence),
            "sequence_from_original": format_sequence(sequence),
            "full_signature_hash": stable_hash(sig),
            "fru_signature_hash": stable_hash(fsig),
            "same_FRU_state_count": len(fru_index.get(fsig, [])),
        })

    edge_rows = []

    for source_sig, outgoing in graph.items():
        source_label = sig_to_label[source_sig]

        for rotation, target_sig in outgoing:
            target_label = sig_to_label[target_sig]

            edge_rows.append({
                "source": source_label,
                "rotation": rotation,
                "target": target_label,
            })

    nodes_df = pd.DataFrame(node_rows)
    edges_df = pd.DataFrame(edge_rows)

    return nodes_df, edges_df


def build_networkx_rotation_graph(graph_data):
    """
    Build a NetworkX MultiDiGraph from the rotation graph.

    Nodes are labelled S0, S1, ...
    Edges are labelled by the rotation operator.
    """
    states_by_sig = graph_data["states_by_sig"]
    graph = graph_data["graph"]
    fru_index = graph_data["fru_index"]

    sig_to_label, _ = build_graph_label_maps(graph_data)

    G = nx.MultiDiGraph()

    for sig, state in states_by_sig.items():
        label = sig_to_label[sig]
        sequence = state["sequence_from_original"]
        fsig = fru_signature(state["faces"])

        G.add_node(
            label,
            sequence=format_sequence(sequence),
            depth=len(sequence),
            full_signature_hash=stable_hash(sig),
            fru_signature_hash=stable_hash(fsig),
            same_FRU_state_count=len(fru_index.get(fsig, [])),
        )

    for source_sig, outgoing in graph.items():
        source_label = sig_to_label[source_sig]

        for rotation, target_sig in outgoing:
            target_label = sig_to_label[target_sig]

            G.add_edge(
                source_label,
                target_label,
                rotation=rotation,
            )

    return G


def shortest_node_paths_between_state_sets(
    graph,
    source_sigs,
    target_sigs,
    max_paths=20,
):
    """
    Same idea as shortest_paths_between_state_sets, but returns both:
    - the rotation sequence
    - the node path

    This is useful for highlighting the inferred path in the graph.
    """
    target_sigs = set(target_sigs)

    queue = deque()
    visited_depth = {}

    for source_sig in source_sigs:
        queue.append((source_sig, [], [source_sig]))
        visited_depth[source_sig] = 0

    paths = []
    best_depth = None

    while queue:
        current_sig, sequence, node_path = queue.popleft()
        depth = len(sequence)

        if best_depth is not None and depth > best_depth:
            continue

        if current_sig in target_sigs:
            best_depth = depth

            if len(paths) < max_paths:
                paths.append({
                    "rotations": sequence,
                    "nodes": node_path,
                })

            continue

        for rotation, next_sig in graph.get(current_sig, []):
            next_depth = depth + 1

            if best_depth is not None and next_depth > best_depth:
                continue

            old_depth = visited_depth.get(next_sig)

            if old_depth is not None and old_depth < next_depth:
                continue

            visited_depth[next_sig] = next_depth
            queue.append((
                next_sig,
                sequence + [rotation],
                node_path + [next_sig],
            ))

    return paths


def rotation_graph_to_dot(graph_data):
    """
    Export the graph as DOT text.

    This does not require pygraphviz or pydot.
    You can paste the output into Graphviz tools.
    """
    states_by_sig = graph_data["states_by_sig"]
    graph = graph_data["graph"]

    sig_to_label, _ = build_graph_label_maps(graph_data)

    lines = []
    lines.append("digraph RotationGraph {")
    lines.append("  rankdir=LR;")
    lines.append("  node [shape=box, style=rounded];")

    for sig, state in states_by_sig.items():
        label = sig_to_label[sig]
        sequence = short_sequence(state["sequence_from_original"], max_chars=40)
        node_label = f"{label}\\n{sequence}"
        lines.append(f'  {label} [label="{node_label}"];')

    for source_sig, outgoing in graph.items():
        source_label = sig_to_label[source_sig]

        for rotation, target_sig in outgoing:
            target_label = sig_to_label[target_sig]
            lines.append(
                f'  {source_label} -> {target_label} '
                f'[label="{rotation}"];'
            )

    lines.append("}")

    return "\n".join(lines)


def draw_rotation_graph(
    graph_data,
    highlight_node_path=None,
    title="Rotation graph",
    figsize=(11, 8),
):
    """
    Draw a readable graph inside Streamlit.

    highlight_node_path:
        optional list of full signatures forming the inferred shortest path.
    """
    states_by_sig = graph_data["states_by_sig"]
    graph = graph_data["graph"]

    sig_to_label, _ = build_graph_label_maps(graph_data)

    # Use a simple DiGraph for plotting. If multiple rotations connect
    # the same pair of nodes, their labels are combined.
    G = nx.DiGraph()
    edge_label_map = defaultdict(list)

    for sig, state in states_by_sig.items():
        node = sig_to_label[sig]
        seq = state["sequence_from_original"]

        G.add_node(
            node,
            draw_label=f"{node}\n{short_sequence(seq, max_chars=24)}",
        )

    for source_sig, outgoing in graph.items():
        source_label = sig_to_label[source_sig]

        for rotation, target_sig in outgoing:
            target_label = sig_to_label[target_sig]

            G.add_edge(source_label, target_label)
            edge_label_map[(source_label, target_label)].append(rotation)

    plot_edge_labels = {
        edge: ",".join(sorted(set(labels)))
        for edge, labels in edge_label_map.items()
    }

    highlight_nodes = set()
    highlight_edges = set()

    if highlight_node_path:
        highlight_labels = [
            sig_to_label[sig]
            for sig in highlight_node_path
            if sig in sig_to_label
        ]

        highlight_nodes = set(highlight_labels)

        for a, b in zip(highlight_labels, highlight_labels[1:]):
            highlight_edges.add((a, b))

    pos = nx.spring_layout(G, seed=7, k=1.1)

    node_colors = [
        "#FFD166" if node in highlight_nodes else "#DCEBFF"
        for node in G.nodes()
    ]

    edge_colors = [
        "#D62828" if edge in highlight_edges else "#A0A0A0"
        for edge in G.edges()
    ]

    edge_widths = [
        2.8 if edge in highlight_edges else 1.0
        for edge in G.edges()
    ]

    fig, ax = plt.subplots(figsize=figsize)
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.axis("off")

    nx.draw_networkx_nodes(
        G,
        pos,
        node_color=node_colors,
        edgecolors="black",
        linewidths=0.8,
        node_size=1700,
        ax=ax,
    )

    nx.draw_networkx_edges(
        G,
        pos,
        edge_color=edge_colors,
        width=edge_widths,
        arrows=True,
        arrowsize=15,
        connectionstyle="arc3,rad=0.08",
        ax=ax,
    )

    node_draw_labels = {
        node: G.nodes[node]["draw_label"]
        for node in G.nodes()
    }

    nx.draw_networkx_labels(
        G,
        pos,
        labels=node_draw_labels,
        font_size=7,
        ax=ax,
    )

    nx.draw_networkx_edge_labels(
        G,
        pos,
        edge_labels=plot_edge_labels,
        font_size=6,
        label_pos=0.5,
        ax=ax,
    )

    plt.tight_layout()
    return fig

def fru_distance(candidate_faces, target_fru):
    """
    Fuzzy mismatch rate between candidate FRU and target FRU.

    0.0 means exact.
    1.0 means totally different.
    """
    mismatches = 0
    total = 0

    for face in FRU_FACES:
        candidate = candidate_faces[face]
        target = target_fru[face]

        for r in range(len(target)):
            for c in range(len(target[r])):
                total += 1

                if candidate[r][c] != target[r][c]:
                    mismatches += 1

    if total == 0:
        return 1.0

    return mismatches / total


def infer_rotation_between_current_fru(object_name):
    """
    Infer shortest rotation sequence from fixed FRU to transformed FRU.
    """
    graph_data = build_rotation_graph_for_object(object_name)

    graph = graph_data["graph"]
    states_by_sig = graph_data["states_by_sig"]
    fru_index = graph_data["fru_index"]

    fixed_faces = st.session_state.fixed_faces[object_name]
    transformed_faces = st.session_state.transformed_faces[object_name]

    source_fru_sig = fru_signature(fixed_faces)
    target_fru_sig = fru_signature(transformed_faces)

    source_sigs = fru_index.get(source_fru_sig, [])
    target_sigs = fru_index.get(target_fru_sig, [])

    if source_sigs and target_sigs:
        paths = shortest_paths_between_state_sets(
            graph,
            source_sigs,
            target_sigs,
            max_paths=20,
        )

        return {
            "mode": "exact",
            "source_candidates": len(source_sigs),
            "target_candidates": len(target_sigs),
            "paths": paths,
            "best_sequence": paths[0] if paths else None,
            "best_score": 0.0 if paths else None,
        }

    # Fuzzy fallback.
    target_fru = {
        "front": transformed_faces["front"],
        "right": transformed_faces["right"],
        "up": transformed_faces["up"],
    }

    scored = []

    for sig, state in states_by_sig.items():
        score = fru_distance(state["faces"], target_fru)
        scored.append((score, state))

    scored.sort(
        key=lambda item: (
            item[0],
            len(item[1]["sequence_from_original"]),
        )
    )

    best_score, best_state = scored[0]

    if source_sigs:
        paths = shortest_paths_between_state_sets(
            graph,
            source_sigs,
            [best_state["signature"]],
            max_paths=20,
        )
    else:
        paths = []

    return {
        "mode": "fuzzy",
        "source_candidates": len(source_sigs),
        "target_candidates": len(target_sigs),
        "paths": paths,
        "best_sequence": paths[0] if paths else best_state["sequence_from_original"],
        "best_score": best_score,
    }


# ============================================================================
# SMALL 2D CUBE NET
# ============================================================================

def draw_cube_grid_compact(faces, title=None, figsize=(2.25, 2.25), face_palette=None):
    """
    Draw compact cube net:

           [Up]
    [Left][Front][Right]
          [Down][Back]
    """
    fig, axes = plt.subplots(3, 3, figsize=figsize)

    if title:
        fig.suptitle(title, fontsize=8, fontweight="bold")

    for row in axes:
        for ax in row:
            ax.set_visible(False)

    positions = {
        "up": (0, 1),
        "left": (1, 0),
        "front": (1, 1),
        "right": (1, 2),
        "down": (2, 1),
        "back": (2, 2),
    }

    for face_name, (row, col) in positions.items():
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
        ax.set_title(face_name.upper(), fontsize=5, fontweight="bold", pad=1)
        palette_face = resolve_face_palette(face_palette, face_name)

        for r, row_data in enumerate(matrix):
            for c, value in enumerate(row_data):
                color = face_cell_rgba(palette_face, value, transparent=True)

                rect = Rectangle(
                    (c - 0.4, r - 0.4),
                    0.8,
                    0.8,
                    facecolor=color,
                    edgecolor="black",
                    linewidth=0.45,
                )

                ax.add_patch(rect)

                ax.text(
                    c,
                    r,
                    value,
                    ha="center",
                    va="center",
                    fontsize=5,
                    fontweight="bold",
                    color="black",
                )

    plt.tight_layout(pad=0.1)
    return fig


# ============================================================================
# SMALL 3D VOXEL VIEW
# ============================================================================

def _map_face_to_xyz(face_name, r, c, layer):
    if face_name == "front":
        x = c
        y = r
        z = layer

    elif face_name == "back":
        x = 2 - c
        y = r
        z = 2 - layer

    elif face_name == "left":
        x = layer
        y = r
        z = 2 - c

    elif face_name == "right":
        x = 2 - layer
        y = r
        z = c

    elif face_name == "up":
        x = c
        y = layer
        z = 2 - r

    elif face_name == "down":
        x = c
        y = 2 - layer
        z = r

    else:
        x = y = z = -1

    return x, y, z


def reconstruct_voxels_from_faces(faces, size=3):
    occ = np.zeros((size, size, size), dtype=bool)
    colors = np.zeros((size, size, size, 4), dtype=float)

    face_order = [
        "front",
        "right",
        "back",
        "left",
        "up",
        "down",
    ]

    for face_name in face_order:
        mat = faces.get(face_name)

        if mat is None:
            continue

        for r in range(len(mat)):
            for c in range(len(mat[r])):
                val = mat[r][c]

                if val == "*":
                    continue

                layer = DEPTH_TO_LAYER.get(val, 2)
                x, y, z = _map_face_to_xyz(face_name, r, c, layer)

                if 0 <= x < size and 0 <= y < size and 0 <= z < size:
                    if not occ[x, y, z]:
                        occ[x, y, z] = True

                        colors[x, y, z] = face_cell_rgba(
                            face_name,
                            val,
                            transparent=False,
                        )

    return occ, colors


def apply_axis_ops(occ, colors, perm=DEFAULT_PERM, flips=DEFAULT_FLIPS):
    occ_t = np.transpose(occ, perm)
    colors_t = np.transpose(colors, perm + (3,))

    for axis, do_flip in enumerate(flips):
        if do_flip:
            occ_t = np.flip(occ_t, axis=axis)
            colors_t = np.flip(colors_t, axis=axis)

    return occ_t, colors_t


def _unapply_axis_ops_to_coords(coord_t, perm=DEFAULT_PERM, flips=DEFAULT_FLIPS, size=3):
    coord_after_unflip = [0, 0, 0]

    for k in range(3):
        value = coord_t[k]

        if flips[k]:
            value = size - 1 - value

        coord_after_unflip[k] = value

    inv_perm = [0, 0, 0]

    for trans_axis, orig_axis in enumerate(perm):
        inv_perm[orig_axis] = trans_axis

    coord_orig = [0, 0, 0]

    for orig_axis in range(3):
        coord_orig[orig_axis] = coord_after_unflip[inv_perm[orig_axis]]

    return tuple(coord_orig)


def _transform_vector_to_original(vec_t, perm=DEFAULT_PERM, flips=DEFAULT_FLIPS):
    inv_perm = [0, 0, 0]

    for trans_axis, orig_axis in enumerate(perm):
        inv_perm[orig_axis] = trans_axis

    vec_orig = [0, 0, 0]

    for orig_axis in range(3):
        component = vec_t[inv_perm[orig_axis]]

        if flips[inv_perm[orig_axis]]:
            component = -component

        vec_orig[orig_axis] = component

    return tuple(vec_orig)


def _compute_orig_normal_to_face():
    mapping = {}

    for face in ["front", "right", "back", "left", "up", "down"]:
        r, c = 1, 1
        x0, y0, z0 = _map_face_to_xyz(face, r, c, 0)
        x1, y1, z1 = _map_face_to_xyz(face, r, c, 1)

        vector = (x1 - x0, y1 - y0, z1 - z0)
        outward_normal = (
            -int(np.sign(vector[0])),
            -int(np.sign(vector[1])),
            -int(np.sign(vector[2])),
        )

        mapping[outward_normal] = face

    return mapping


_ORIG_NORMAL_TO_FACE = _compute_orig_normal_to_face()


def _voxel_face_vertices_transformed(x, y, z, direction, offset=0.02):
    x0, x1 = x, x + 1
    y0, y1 = y, y + 1
    z0, z1 = z, z + 1

    if direction == "+x":
        x1 = x1 + offset
        return [[x1, y0, z0], [x1, y1, z0], [x1, y1, z1], [x1, y0, z1]]

    if direction == "-x":
        x0 = x0 - offset
        return [[x0, y0, z1], [x0, y1, z1], [x0, y1, z0], [x0, y0, z0]]

    if direction == "+y":
        y1 = y1 + offset
        return [[x0, y1, z0], [x1, y1, z0], [x1, y1, z1], [x0, y1, z1]]

    if direction == "-y":
        y0 = y0 - offset
        return [[x0, y0, z1], [x1, y0, z1], [x1, y0, z0], [x0, y0, z0]]

    if direction == "+z":
        z1 = z1 + offset
        return [[x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]]

    if direction == "-z":
        z0 = z0 - offset
        return [[x0, y1, z0], [x1, y1, z0], [x1, y0, z0], [x0, y0, z0]]

    return []


def draw_voxel_compact(
    faces,
    title=None,
    figsize=(2.25, 2.25),
    elev=30,
    azim=45,
    uniform_color=DEFAULT_VOXEL_COLOR,
    face_palette=None,
):
    face_palette = face_palette or DEFAULT_FACE_PALETTE

    occ, colors = reconstruct_voxels_from_faces(faces, size=3)

    proj_map = {}

    for face_name in ["front", "right", "back", "left", "up", "down"]:
        mat = faces.get(face_name)

        if mat is None:
            continue

        for r in range(len(mat)):
            for c in range(len(mat[r])):
                val = mat[r][c]

                if val == "*":
                    continue

                layer = DEPTH_TO_LAYER.get(val, 2)
                x_o, y_o, z_o = _map_face_to_xyz(face_name, r, c, layer)

                if 0 <= x_o < 3 and 0 <= y_o < 3 and 0 <= z_o < 3:
                    proj_map[(x_o, y_o, z_o, face_name)] = val

    occ_t, colors_t = apply_axis_ops(occ, colors)

    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(111, projection="3d")

    facecolors = np.zeros_like(colors_t)
    facecolors[...] = colors_t
    facecolors[~occ_t] = (0, 0, 0, 0)

    if uniform_color:
        try:
            uniform_rgba = mcolors.to_rgba(uniform_color)
        except Exception:
            uniform_rgba = (0.85, 0.55, 0.0, 1.0)

        facecolors[occ_t] = uniform_rgba

    ax.voxels(
        occ_t,
        facecolors=facecolors,
        edgecolor="k",
        linewidth=0.35,
    )

    size = occ_t.shape[0]

    neighbors = [
        ((1, 0, 0), "+x"),
        ((-1, 0, 0), "-x"),
        ((0, 1, 0), "+y"),
        ((0, -1, 0), "-y"),
        ((0, 0, 1), "+z"),
        ((0, 0, -1), "-z"),
    ]

    for x in range(size):
        for y in range(size):
            for z in range(size):
                if not occ_t[x, y, z]:
                    continue

                for (dx, dy, dz), dir_key in neighbors:
                    nx, ny, nz = x + dx, y + dy, z + dz
                    exposed = False

                    if not (0 <= nx < size and 0 <= ny < size and 0 <= nz < size):
                        exposed = True
                    elif not occ_t[nx, ny, nz]:
                        exposed = True

                    if not exposed:
                        continue

                    orig_coord = _unapply_axis_ops_to_coords((x, y, z))
                    n_orig = _transform_vector_to_original((dx, dy, dz))
                    face_name = _ORIG_NORMAL_TO_FACE.get(tuple(int(v) for v in n_orig))

                    color = None

                    if face_name is not None:
                        val = proj_map.get((orig_coord[0], orig_coord[1], orig_coord[2], face_name))

                        if val is not None:
                            color = face_cell_rgb(resolve_face_palette(face_palette, face_name), val)

                    if color is None:
                        color = mcolors.to_rgba("#C8C8C8", 1.0)

                    verts = _voxel_face_vertices_transformed(x, y, z, dir_key)

                    if not verts:
                        continue

                    poly = Poly3DCollection(
                        [verts],
                        facecolor=color,
                        edgecolor="#202020",
                        linewidth=0.15,
                    )
                    ax.add_collection3d(poly)

    ax.set_xlim(0, 3)
    ax.set_ylim(0, 3)
    ax.set_zlim(0, 3)
    ax.set_box_aspect((1, 1, 1))

    ax.set_axis_off()
    ax.view_init(elev=elev, azim=azim)

    if title:
        ax.set_title(title, fontsize=8, fontweight="bold")

    plt.tight_layout(pad=0.05)
    return fig


VOXEL_FACE_DIRECTIONS = [
    "front",
    "back",
    "left",
    "right",
    "up",
    "down",
]

VOXEL_FACE_NEIGHBORS = {
    "front": (0, 0, 1),
    "back": (0, 0, -1),
    "left": (-1, 0, 0),
    "right": (1, 0, 0),
    "up": (0, -1, 0),
    "down": (0, 1, 0),
}


def voxel_face_vertices(x, y, z, face_name, epsilon=0.01):
    x0 = x
    x1 = x + 1
    y0 = y
    y1 = y + 1
    z0 = z
    z1 = z + 1

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


def build_voxel_surface_color_maps(faces, size=3, depth_tinted=False, face_palette=None):
    occ = np.zeros((size, size, size), dtype=bool)
    face_colors = {
        face_name: np.full((size, size, size, 4), np.nan, dtype=float)
        for face_name in VOXEL_FACE_DIRECTIONS
    }

    for face_name in VOXEL_FACE_DIRECTIONS:
        mat = faces.get(face_name)

        if mat is None:
            continue

        for r in range(len(mat)):
            for c in range(len(mat[r])):
                val = mat[r][c]

                if val == "*":
                    continue

                layer = DEPTH_TO_LAYER.get(val, 2)
                x, y, z = _map_face_to_xyz(face_name, r, c, layer)

                if 0 <= x < size and 0 <= y < size and 0 <= z < size:
                    occ[x, y, z] = True
                    palette_face = resolve_face_palette(face_palette, face_name)
                    face_colors[face_name][x, y, z] = face_cell_rgba(
                        palette_face,
                        val,
                        transparent=depth_tinted,
                    )

    return occ, face_colors


def draw_surface_colored_voxels_compact(
    faces,
    title=None,
    figsize=(2.25, 2.25),
    elev=30,
    azim=45,
    depth_tinted=False,
    face_palette=None,
):
    occ, face_colors = build_voxel_surface_color_maps(
        faces,
        size=3,
        depth_tinted=depth_tinted,
        face_palette=face_palette,
    )

    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(111, projection="3d")

    base_colors = np.full((3, 3, 3, 4), (0.88, 0.88, 0.88, 1.0), dtype=float)
    base_colors[~occ] = (0, 0, 0, 0)

    ax.voxels(
        occ,
        facecolors=base_colors,
        edgecolor="#202020",
        linewidth=0.35,
    )

    for x, y, z in np.argwhere(occ):
        for face_name, (dx, dy, dz) in VOXEL_FACE_NEIGHBORS.items():
            nx, ny, nz = x + dx, y + dy, z + dz

            exposed = not (
                0 <= nx < occ.shape[0]
                and 0 <= ny < occ.shape[1]
                and 0 <= nz < occ.shape[2]
                and occ[nx, ny, nz]
            )

            if not exposed:
                continue

            color = face_colors[face_name][x, y, z]

            if np.isnan(color).any():
                continue

            vertices = voxel_face_vertices(x, y, z, face_name)

            if not vertices:
                continue

            poly = Poly3DCollection(
                [vertices],
                facecolor=color,
                edgecolor="#202020",
                linewidth=0.15,
            )
            ax.add_collection3d(poly)

    ax.set_xlim(0, 3)
    ax.set_ylim(0, 3)
    ax.set_zlim(0, 3)
    ax.set_box_aspect((1, 1, 1))
    ax.set_axis_off()
    ax.view_init(elev=elev, azim=azim)

    if title:
        ax.set_title(title, fontsize=8, fontweight="bold")

    plt.tight_layout(pad=0.05)
    return fig


def draw_colored_side_cube_compact(
    faces,
    title=None,
    figsize=(2.25, 2.25),
    elev=30,
    azim=45,
    side_style="surface",
    face_palette=None,
):
    if side_style == "surface_depth":
        return draw_voxel_compact(
            faces,
            title=title,
            figsize=figsize,
            elev=elev,
            azim=azim,
            face_palette=face_palette,
        )

    if side_style == "surface":
        return draw_voxel_compact(
            faces,
            title=title,
            figsize=figsize,
            elev=elev,
            azim=azim,
            face_palette=face_palette,
        )

    return draw_voxel_compact(
        faces,
        title=title,
        figsize=figsize,
        elev=elev,
        azim=azim,
        face_palette=face_palette,
    )


# ============================================================================
# DATASET TABLE
# ============================================================================

def build_current_dataset_rows():
    rows = []

    for object_name in OBJECT_NAMES:
        inference = infer_rotation_between_current_fru(object_name)

        actual_history = st.session_state.actual_history.get(object_name, [])
        inferred = inference.get("best_sequence")

        if inferred is None:
            inferred_text = "no path found"
        else:
            inferred_text = format_sequence(inferred)

        rows.append({
            "object": object_name,
            "actual_applied_moves": display_sequence(actual_history),
            "inferred_rotation": (inferred_text if inferred is None else display_sequence(inferred)),
            "match_mode": inference["mode"],
            "source_FRU_candidates": inference["source_candidates"],
            "target_FRU_candidates": inference["target_candidates"],
            "alternative_shortest_paths": len(inference.get("paths", [])),
            "fuzzy_score": inference["best_score"],
        })

    return rows


# ============================================================================
# STREAMLIT UI
# ============================================================================

st.set_page_config(
    page_title="FRU Rotation Inference Dataset Demo",
    layout="wide",
)

st.title("FRU Rotation Inference Dataset Demo")

st.write(
    "This demo builds an interactive dataset for **object1 to object6**. "
    "Each row has a fixed original object, a movable transformed object, "
    "and an automatically inferred rotation sequence from the fixed FRU to the transformed FRU."
)

initialize_session_state()

st.sidebar.header("Display settings")

show_3d = st.sidebar.checkbox(
    "Show 3D voxel views",
    value=True,
)

elev = st.sidebar.slider(
    "3D elevation",
    min_value=0,
    max_value=90,
    value=30,
    step=5,
)

azim = st.sidebar.slider(
    "3D azimuth",
    min_value=-180,
    max_value=180,
    value=45,
    step=5,
)

st.sidebar.divider()

if st.sidebar.button("Reset all transformed objects", use_container_width=True):
    reset_all_objects()
    st.rerun()


# ============================================================================
# DATASET SUMMARY
# ============================================================================

st.subheader("Current dataset")

dataset_rows = build_current_dataset_rows()
dataset_df = pd.DataFrame(dataset_rows)

st.dataframe(
    dataset_df,
    use_container_width=True,
    hide_index=True,
)

csv_data = dataset_df.to_csv(index=False).encode("utf-8")

st.download_button(
    "Download current dataset CSV",
    data=csv_data,
    file_name="fru_rotation_inference_dataset_object1_to_object6.csv",
    mime="text/csv",
)

# ============================================================================
# ROTATION GRAPH EXTRACTION
# ============================================================================

st.divider()
st.subheader("Rotation graph extraction")

graph_col1, graph_col2, graph_col3 = st.columns([1.2, 1.2, 2])

with graph_col1:
    graph_object = st.selectbox(
        "Object for graph extraction",
        OBJECT_NAMES,
        index=0,
        key="graph_object_select",
    )

with graph_col2:
    show_graph_plot = st.checkbox(
        "Show graph plot",
        value=True,
        key="show_graph_plot",
    )

with graph_col3:
    highlight_current_path = st.checkbox(
        "Highlight current inferred shortest path",
        value=True,
        key="highlight_current_path",
    )

graph_data = build_rotation_graph_for_object(graph_object)
nodes_df, edges_df = build_rotation_graph_tables(graph_data)

num_nodes = len(nodes_df)
num_edges = len(edges_df)
num_fru_classes = len(graph_data["fru_index"])

m1, m2, m3 = st.columns(3)

with m1:
    st.metric("Graph nodes", num_nodes)

with m2:
    st.metric("Graph edges", num_edges)

with m3:
    st.metric("Unique FRU signatures", num_fru_classes)

highlight_node_path = None
highlight_sequence_text = "No path highlighted."

if highlight_current_path:
    fixed_faces = st.session_state.fixed_faces[graph_object]
    transformed_faces = st.session_state.transformed_faces[graph_object]

    source_fru_sig = fru_signature(fixed_faces)
    target_fru_sig = fru_signature(transformed_faces)

    source_sigs = graph_data["fru_index"].get(source_fru_sig, [])
    target_sigs = graph_data["fru_index"].get(target_fru_sig, [])

    node_paths = shortest_node_paths_between_state_sets(
        graph_data["graph"],
        source_sigs,
        target_sigs,
        max_paths=20,
    )

    if node_paths:
        best_node_path = node_paths[0]
        highlight_node_path = best_node_path["nodes"]
        highlight_sequence_text = display_sequence(best_node_path["rotations"])

st.markdown("**Highlighted inferred path**")
st.code(highlight_sequence_text)

if show_graph_plot:
    fig = draw_rotation_graph(
        graph_data,
        highlight_node_path=highlight_node_path,
        title=f"Rotation graph for {graph_object}",
        figsize=(12, 8),
    )
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

with st.expander("Show node table"):
    st.dataframe(
        nodes_df,
        use_container_width=True,
        hide_index=True,
    )

with st.expander("Show edge table"):
    st.dataframe(
        edges_df,
        use_container_width=True,
        hide_index=True,
    )

# Downloads
nodes_csv = nodes_df.to_csv(index=False).encode("utf-8")
edges_csv = edges_df.to_csv(index=False).encode("utf-8")
dot_text = rotation_graph_to_dot(graph_data).encode("utf-8")

G_nx = build_networkx_rotation_graph(graph_data)
graphml_buffer = io.BytesIO()
nx.write_graphml(G_nx, graphml_buffer)
graphml_data = graphml_buffer.getvalue()

d1, d2, d3, d4 = st.columns(4)

with d1:
    st.download_button(
        "Download nodes CSV",
        data=nodes_csv,
        file_name=f"{graph_object}_rotation_graph_nodes.csv",
        mime="text/csv",
    )

with d2:
    st.download_button(
        "Download edges CSV",
        data=edges_csv,
        file_name=f"{graph_object}_rotation_graph_edges.csv",
        mime="text/csv",
    )

with d3:
    st.download_button(
        "Download DOT",
        data=dot_text,
        file_name=f"{graph_object}_rotation_graph.dot",
        mime="text/vnd.graphviz",
    )

with d4:
    st.download_button(
        "Download GraphML",
        data=graphml_data,
        file_name=f"{graph_object}_rotation_graph.graphml",
        mime="application/graphml+xml",
    )

# ============================================================================
# OBJECT ROWS
# ============================================================================

st.divider()
st.subheader("Interactive rows")

for object_name in OBJECT_NAMES:
    inference = infer_rotation_between_current_fru(object_name)

    actual_history = st.session_state.actual_history.get(object_name, [])
    inferred_sequence = inference.get("best_sequence")

    if inferred_sequence is None:
        inferred_text = "no path found"
    else:
        inferred_text = display_sequence(inferred_sequence)

    header = (
        f"{object_name} | inferred: {short_sequence(inferred_sequence or [])} "
        f"| mode: {inference['mode']} "
        f"| alternatives: {len(inference.get('paths', []))}"
    )

    with st.expander(header, expanded=(object_name == "object1")):
        fixed_faces = st.session_state.fixed_faces[object_name]
        transformed_faces = st.session_state.transformed_faces[object_name]
        fixed_palette = copy.deepcopy(DEFAULT_FACE_PALETTE)
        transformed_palette = st.session_state.face_palettes.get(
            object_name,
            copy.deepcopy(DEFAULT_FACE_PALETTE),
        )

        st.markdown(f"### {object_name}")

        info_col1, info_col2, info_col3 = st.columns([2, 2, 2])

        with info_col1:
            st.markdown("**Actual applied moves**")
            st.code(display_sequence(actual_history))

        with info_col2:
            st.markdown("**Inferred shortest sequence**")
            st.code(inferred_text)

        with info_col3:
            st.markdown("**Inference details**")
            st.write(
                {
                    "mode": inference["mode"],
                    "source_FRU_candidates": inference["source_candidates"],
                    "target_FRU_candidates": inference["target_candidates"],
                    "alternative_shortest_paths": len(inference.get("paths", [])),
                    "fuzzy_score": inference["best_score"],
                }
            )

        if inference.get("paths"):
            with st.popover("Show alternative shortest paths"):
                for idx, path in enumerate(inference["paths"], start=1):
                    st.write(f"{idx}. {display_sequence(path)}")

        st.markdown("#### Move transformed object")

        b1, b2, b3, b4, b5, b6, b7 = st.columns(7)

        with b1:
            if st.button("Up", key=f"{object_name}_up", use_container_width=True):
                move_transformed_object(object_name, "towards_up")
                st.rerun()

        with b2:
            if st.button("Down", key=f"{object_name}_down", use_container_width=True):
                move_transformed_object(object_name, "towards_down")
                st.rerun()

        with b3:
            if st.button("Left", key=f"{object_name}_left", use_container_width=True):
                move_transformed_object(object_name, "towards_left")
                st.rerun()

        with b4:
            if st.button("Right", key=f"{object_name}_right", use_container_width=True):
                move_transformed_object(object_name, "towards_right")
                st.rerun()

        with b5:
            if st.button(display_rotation("1q"), key=f"{object_name}_1q", use_container_width=True):
                move_transformed_object(object_name, "1q")
                st.rerun()

        with b6:
            if st.button(display_rotation("-1q"), key=f"{object_name}_minus_1q", use_container_width=True):
                move_transformed_object(object_name, "-1q")
                st.rerun()

        with b7:
            if st.button("Reset", key=f"{object_name}_reset", use_container_width=True):
                reset_transformed_object(object_name)
                st.rerun()

        st.markdown("#### Fixed object vs transformed object")

        if show_3d:
            c1, c2, c3, c4 = st.columns(4)

            with c1:
                st.markdown("**Fixed 2D FRU/full net**")
                fig = draw_cube_grid_compact(
                    fixed_faces,
                    title=f"{object_name} fixed 2D",
                    face_palette=fixed_palette,
                )
                st.pyplot(fig, use_container_width=False)
                plt.close(fig)

            with c2:
                st.markdown("**Fixed 3D**")
                fig = draw_voxel_compact(
                    fixed_faces,
                    title=f"{object_name} fixed 3D",
                    elev=elev,
                    azim=azim,
                    face_palette=fixed_palette,
                )
                st.pyplot(fig, use_container_width=False)
                plt.close(fig)

            with c3:
                st.markdown("**Transformed 2D FRU/full net**")
                fig = draw_cube_grid_compact(
                    transformed_faces,
                    title=f"{object_name} transformed 2D",
                    face_palette=transformed_palette,
                )
                st.pyplot(fig, use_container_width=False)
                plt.close(fig)

            with c4:
                st.markdown("**Transformed 3D**")
                fig = draw_voxel_compact(
                    transformed_faces,
                    title=f"{object_name} transformed 3D",
                    elev=elev,
                    azim=azim,
                    face_palette=transformed_palette,
                )
                st.pyplot(fig, use_container_width=False)
                plt.close(fig)

        else:
            c1, c2 = st.columns(2)

            with c1:
                st.markdown("**Fixed 2D FRU/full net**")
                fig = draw_cube_grid_compact(
                    fixed_faces,
                    title=f"{object_name} fixed 2D",
                    figsize=(2.6, 2.6),
                    face_palette=fixed_palette,
                )
                st.pyplot(fig, use_container_width=False)
                plt.close(fig)

            with c2:
                st.markdown("**Transformed 2D FRU/full net**")
                fig = draw_cube_grid_compact(
                    transformed_faces,
                    title=f"{object_name} transformed 2D",
                    figsize=(2.6, 2.6),
                    face_palette=transformed_palette,
                )
                st.pyplot(fig, use_container_width=False)
                plt.close(fig)


# ============================================================================
# NOTES
# ============================================================================

st.divider()

st.caption(
    "Note: inference uses only the visible FRU maps for matching, but it uses the known full object "
    "from q3d-ex.pl to build the rotation graph. If multiple cube states share the same FRU, "
    "the app reports alternative shortest paths. If 1q and -1q (towards-up-right and towards-up-left) "
    "look identical, check the Prolog implementation of apply_in_plane_rotation_minus1q/13."
)