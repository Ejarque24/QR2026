#!/usr/bin/env python3
"""
Interactive cube rotation demo.

Requirements:
    pip install streamlit matplotlib numpy

Run:
    streamlit run interactive_cube_demo.py

This app uses visualize_cubes_qor.py for:
- extracting object faces from q3d-ex.pl
- applying normal rotations through Prolog
- applying in-plane rotations through Prolog apply_in_plane_rotation_full/13

Supported rotations:
- towards_up
- towards_down
- towards_left
- towards_right
- 1q
- -1q
"""

import copy
import re
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.patches import Rectangle
import streamlit as st

import visualize_cubes_qor as vcq


# ============================================================================
# CONFIG
# ============================================================================

Q3D_PATH = Path(__file__).parent / "q3d-ex.pl"

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
    """
    Rotate the face-color assignment with the cube so colors travel with faces.
    face_palette maps current face position -> original face identity.
    """
    mapping = ROTATION_FACE_TARGETS.get(rotation_name)

    if not mapping:
        return copy.deepcopy(face_palette)

    new_palette = {}
    for source_face, target_face in mapping.items():
        new_palette[target_face] = face_palette.get(source_face, source_face)

    # Keep any untouched faces stable.
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
                    linewidth=0.25,
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
    figsize=(3.2, 3.2),
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
        ax.set_title(title, fontsize=9, fontweight="bold")

    plt.tight_layout(pad=0.1)
    return fig


# ============================================================================
# OBJECT LOADING HELPERS
# ============================================================================

def natural_sort_key(name):
    """
    Sort object1, object2, ..., object10 naturally.
    """
    match = re.search(r"(\d+)$", name)

    if match:
        return name[:match.start()], int(match.group(1))

    return name, 0


@st.cache_data
def list_objects_from_q3d():
    """
    Read q3d-ex.pl and find all object names used in view/5 facts.
    """
    if not Q3D_PATH.exists():
        return []

    text = Q3D_PATH.read_text(encoding="utf-8", errors="replace")

    pattern = re.compile(
        r"view\(\s*"
        r"(front|back|left|right|up|down)"
        r"\s*,\s*"
        r"([a-zA-Z_][a-zA-Z0-9_]*)"
        r"\s*,",
        re.MULTILINE,
    )

    objects = set()

    for match in pattern.finditer(text):
        objects.add(match.group(2))

    return sorted(objects, key=natural_sort_key)


@st.cache_data
def load_faces_for_object(object_name):
    """
    Load object faces using visualize_cubes_qor.py.
    """
    faces = vcq.extract_faces_from_q3d(object_name)

    required = ["front", "back", "left", "right", "up", "down"]

    if not all(faces.get(face) is not None for face in required):
        raise ValueError(f"{object_name} does not have all six faces.")

    return faces


def ensure_object_loaded(object_name):
    """
    Add object to session state if it is not already loaded.
    """
    if "original_faces" not in st.session_state:
        st.session_state.original_faces = {}

    if "current_faces" not in st.session_state:
        st.session_state.current_faces = {}

    if "rotation_history" not in st.session_state:
        st.session_state.rotation_history = {}

    if "face_palettes" not in st.session_state:
        st.session_state.face_palettes = {}

    if object_name not in st.session_state.original_faces:
        faces = load_faces_for_object(object_name)

        st.session_state.original_faces[object_name] = copy.deepcopy(faces)
        st.session_state.current_faces[object_name] = copy.deepcopy(faces)
        st.session_state.rotation_history[object_name] = []
        st.session_state.face_palettes[object_name] = copy.deepcopy(DEFAULT_FACE_PALETTE)


def reset_selected_objects(selected_objects):
    """
    Reset selected objects to their original extracted faces.
    """
    for object_name in selected_objects:
        if object_name in st.session_state.original_faces:
            st.session_state.current_faces[object_name] = copy.deepcopy(
                st.session_state.original_faces[object_name]
            )
            st.session_state.rotation_history[object_name] = []
            st.session_state.face_palettes[object_name] = copy.deepcopy(DEFAULT_FACE_PALETTE)


def apply_rotation_to_selected(selected_objects, rotation_name):
    """
    Apply one rotation to every selected object.
    """
    for object_name in selected_objects:
        faces = st.session_state.current_faces[object_name]
        face_palette = st.session_state.face_palettes.get(
            object_name,
            copy.deepcopy(DEFAULT_FACE_PALETTE),
        )

        if rotation_name in NORMAL_ROTATIONS:
            rotated = vcq.apply_rotation_via_prolog(faces, rotation_name)

        elif rotation_name in IN_PLANE_ROTATIONS:
            rotated = vcq.apply_in_plane_rotation(faces, rotation_name)

        else:
            rotated = faces

        st.session_state.current_faces[object_name] = rotated
        st.session_state.face_palettes[object_name] = rotate_face_palette(
            face_palette,
            rotation_name,
        )
        st.session_state.rotation_history[object_name].append(rotation_name)


# ============================================================================
# 2D CUBE-NET DRAWING
# ============================================================================

def draw_cube_grid_compact(faces, title=None, face_palette=None):
    """
    Draw a compact cube net:

           [Up]
    [Left][Front][Right]
          [Down][Back]
    """
    fig, axes = plt.subplots(3, 3, figsize=(3.2, 3.2))

    if title:
        fig.suptitle(title, fontsize=9, fontweight="bold")

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
        palette_face = resolve_face_palette(face_palette, face_name)
        ax.set_title(face_name.upper(), fontsize=6, fontweight="bold", pad=1)

        for r, row_data in enumerate(matrix):
            for c, value in enumerate(row_data):
                color = face_cell_rgba(palette_face, value, transparent=True)

                rect = Rectangle(
                    (c - 0.4, r - 0.4),
                    0.8,
                    0.8,
                    facecolor=color,
                    edgecolor="black",
                    linewidth=0.7,
                )

                ax.add_patch(rect)

                ax.text(
                    c,
                    r,
                    value,
                    ha="center",
                    va="center",
                    fontsize=6,
                    fontweight="bold",
                    color="black",
                )

    plt.tight_layout(pad=0.2)

    return fig


# ============================================================================
# 3D VOXEL RECONSTRUCTION
# ============================================================================

def _map_face_to_xyz(face_name, r, c, layer):
    """
    Map face, row, col, layer to voxel x,y,z using 3x3x3 convention.
    """
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
    """
    Reconstruct a simple 3x3x3 voxel object from six depth maps.

    This uses a priority/union-style reconstruction:
    - each visible depth cell projects to one voxel
    - first hit wins
    """
    occ = np.zeros((size, size, size), dtype=bool)
    colors = np.zeros((size, size, size, 4), dtype=float)

    face_order = ["front", "right", "back", "left", "up", "down"]

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

                        colors[x, y, z] = face_cell_rgba(face_name, val, transparent=False)

    return occ, colors


def apply_axis_ops(occ, colors, perm=DEFAULT_PERM, flips=DEFAULT_FLIPS):
    """
    Apply visual axis mapping used by the voxel renderer.
    """
    occ_t = np.transpose(occ, perm)
    colors_t = np.transpose(colors, perm + (3,))

    for axis, do_flip in enumerate(flips):
        if do_flip:
            occ_t = np.flip(occ_t, axis=axis)
            colors_t = np.flip(colors_t, axis=axis)

    return occ_t, colors_t


def _unapply_axis_ops_to_coords(coord_t, perm=DEFAULT_PERM, flips=DEFAULT_FLIPS, size=3):
    """
    Convert a coordinate in the transformed (visual) space back to the
    original reconstruction coordinate system.
    """
    # undo flips first
    coord_after_unflip = [0, 0, 0]
    for k in range(3):
        v = coord_t[k]
        if flips[k]:
            v = size - 1 - v
        coord_after_unflip[k] = v

    # inverse transpose: find inv_perm so that inv_perm[orig_axis] = trans_axis
    inv_perm = [0, 0, 0]
    for trans_axis, orig_axis in enumerate(perm):
        inv_perm[orig_axis] = trans_axis

    coord_orig = [0, 0, 0]
    for orig_axis in range(3):
        coord_orig[orig_axis] = coord_after_unflip[inv_perm[orig_axis]]

    return tuple(coord_orig)


def _transform_vector_to_original(vec_t, perm=DEFAULT_PERM, flips=DEFAULT_FLIPS):
    """
    Transform a direction vector from transformed space back to original space.
    """
    # inv_perm as above
    inv_perm = [0, 0, 0]
    for trans_axis, orig_axis in enumerate(perm):
        inv_perm[orig_axis] = trans_axis

    vec_orig = [0, 0, 0]
    for orig_axis in range(3):
        comp = vec_t[inv_perm[orig_axis]]
        if flips[inv_perm[orig_axis]]:
            comp = -comp
        vec_orig[orig_axis] = comp

    return tuple(vec_orig)




def _compute_orig_normal_to_face():
    """
    Inspect _map_face_to_xyz to compute the outward integer normal for each
    face name in the reconstruction coordinate system. Returns a dict mapping
    normal-tuples to face names.
    """
    mapping = {}
    face_names = ["front", "right", "back", "left", "up", "down"]
    for face in face_names:
        # pick a sample cell r=1,c=1 and look at layer 0 and layer 1
        r, c = 1, 1
        layer0 = 0
        layer1 = 1
        x0, y0, z0 = _map_face_to_xyz(face, r, c, layer0)
        x1, y1, z1 = _map_face_to_xyz(face, r, c, layer1)

        # vector pointing into the object (from outer layer towards inner)
        v = (x1 - x0, y1 - y0, z1 - z0)

        # outward normal is -v; convert to integer unit vector
        on = (-int(np.sign(v[0])), -int(np.sign(v[1])), -int(np.sign(v[2])))

        mapping[on] = face

    return mapping


_ORIG_NORMAL_TO_FACE = _compute_orig_normal_to_face()


def _voxel_face_vertices_transformed(x, y, z, direction, offset=0.02):
    """Return 4 vertices for the face of a unit cube at (x,y,z) in transformed coords.
    direction is one of '+x','-x','+y','-y','+z','-z'."""
    x0, x1 = x, x + 1
    y0, y1 = y, y + 1
    z0, z1 = z, z + 1

    if direction == '+x':
        x1 = x1 + offset
        return [[x1, y0, z0], [x1, y1, z0], [x1, y1, z1], [x1, y0, z1]]
    if direction == '-x':
        x0 = x0 - offset
        return [[x0, y0, z1], [x0, y1, z1], [x0, y1, z0], [x0, y0, z0]]
    if direction == '+y':
        y1 = y1 + offset
        return [[x0, y1, z0], [x1, y1, z0], [x1, y1, z1], [x0, y1, z1]]
    if direction == '-y':
        y0 = y0 - offset
        return [[x0, y0, z1], [x1, y0, z1], [x1, y0, z0], [x0, y0, z0]]
    if direction == '+z':
        z1 = z1 + offset
        return [[x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]]
    if direction == '-z':
        z0 = z0 - offset
        return [[x0, y1, z0], [x1, y1, z0], [x1, y0, z0], [x0, y0, z0]]

    return []


def draw_voxel_compact(
    faces,
    title=None,
    elev=30,
    azim=45,
    uniform_color=DEFAULT_VOXEL_COLOR,
    face_palette=None,
):
    """
    Draw a compact 3D voxel representation.
    """
    face_palette = face_palette or DEFAULT_FACE_PALETTE

    # Reconstruct occupancy and per-voxel colors in original coordinates
    occ, colors = reconstruct_voxels_from_faces(faces, size=3)

    # Build a projection map from original voxel coords to the face matrix
    # cells that projected to that voxel: key = (x,y,z,face_name) -> value
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

    # Apply visual axis ops (transpose + flips) to occ/colors for rendering
    occ_t, colors_t = apply_axis_ops(occ, colors)

    fig = plt.figure(figsize=(3.2, 3.2))
    ax = fig.add_subplot(111, projection="3d")

    facecolors = np.zeros_like(colors)
    facecolors[...] = mcolors.to_rgba("#D8D8D8", 1.0)
    facecolors[~occ_t] = (0, 0, 0, 0)

    ax.voxels(
        occ_t,
        facecolors=facecolors,
        edgecolor="k",
        linewidth=0.5,
    )

    # Overlay exposed faces as colored polygons derived from the original
    # face matrices. This preserves voxel occupancy while coloring visible
    # sides according to the matrix values.
    size = occ_t.shape[0]

    # neighbor directions in transformed coords and corresponding face keys
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
                    else:
                        if not occ_t[nx, ny, nz]:
                            exposed = True

                    if not exposed:
                        continue

                    # Map transformed voxel coords and face normal back to
                    # original reconstruction coordinates and face name.
                    orig_coord = _unapply_axis_ops_to_coords((x, y, z))
                    n_orig = _transform_vector_to_original((dx, dy, dz))

                    face_name = _ORIG_NORMAL_TO_FACE.get(tuple(int(v) for v in n_orig))

                    color = None

                    if face_name is not None:
                        val = proj_map.get((orig_coord[0], orig_coord[1], orig_coord[2], face_name))
                        if val is not None:
                            color = face_cell_rgb(resolve_face_palette(face_palette, face_name), val)

                    if color is None:
                        # fallback to voxel's assigned color (if any)
                        color = mcolors.to_rgba("#C8C8C8", 1.0)

                    verts = _voxel_face_vertices_transformed(x, y, z, dir_key)
                    if not verts:
                        continue

                    poly = Poly3DCollection(
                        [verts],
                        facecolor=color,
                        edgecolor="#202020",
                        linewidth=0.25,
                    )
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


def draw_colored_side_cube_compact(
    faces,
    title=None,
    elev=30,
    azim=45,
    side_style="surface",
    face_palette=None,
):
    if side_style == "surface_depth":
        return draw_surface_cube_compact(
            faces,
            title=title,
            elev=elev,
            azim=azim,
            depth_tinted=True,
        )

    if side_style == "surface":
        return draw_surface_cube_compact(
            faces,
            title=title,
            elev=elev,
            azim=azim,
            depth_tinted=False,
        )

    return draw_voxel_compact(
        faces,
        title=title,
        elev=elev,
        azim=azim,
        uniform_color=DEFAULT_VOXEL_COLOR,
        face_palette=face_palette,
    )


# ============================================================================
# STREAMLIT UI
# ============================================================================

st.set_page_config(
    page_title="Interactive Cube Rotation Demo",
    layout="wide",
)

st.title("Interactive Cube Rotation Demo")

st.write(
    "Select one or more objects, then click a rotation button. "
    "Each selected object updates cumulatively."
)

objects = list_objects_from_q3d()

if not objects:
    st.error("No objects found in q3d-ex.pl.")
    st.stop()

default_selection = ["object1"] if "object1" in objects else [objects[0]]

selected_objects = st.multiselect(
    "Select objects",
    objects,
    default=default_selection,
)

if not selected_objects:
    st.warning("Select at least one object.")
    st.stop()

for object_name in selected_objects:
    try:
        ensure_object_loaded(object_name)
    except Exception as exc:
        st.error(f"Could not load {object_name}: {exc}")
        st.stop()


# ============================================================================
# SIDEBAR SETTINGS
# ============================================================================

st.sidebar.header("Display settings")

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


# ============================================================================
# ROTATION BUTTONS
# ============================================================================

st.divider()

st.subheader("Normal cube rotations")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("Towards Up", use_container_width=True):
        apply_rotation_to_selected(selected_objects, "towards_up")
        st.rerun()

with col2:
    if st.button("Towards Down", use_container_width=True):
        apply_rotation_to_selected(selected_objects, "towards_down")
        st.rerun()

with col3:
    if st.button("Towards Left", use_container_width=True):
        apply_rotation_to_selected(selected_objects, "towards_left")
        st.rerun()

with col4:
    if st.button("Towards Right", use_container_width=True):
        apply_rotation_to_selected(selected_objects, "towards_right")
        st.rerun()

st.subheader("In-plane rotations")

col5, col6, col7 = st.columns(3)

with col5:
    if st.button(f"In-plane {display_rotation('1q')}", use_container_width=True):
        apply_rotation_to_selected(selected_objects, "1q")
        st.rerun()

with col6:
    if st.button(f"In-plane {display_rotation('-1q')}", use_container_width=True):
        apply_rotation_to_selected(selected_objects, "-1q")
        st.rerun()

with col7:
    if st.button("Reset Selected", use_container_width=True):
        reset_selected_objects(selected_objects)
        st.rerun()


# ============================================================================
# DISPLAY SELECTED OBJECTS
# ============================================================================

st.divider()

st.subheader("Current selected objects")

tabs = st.tabs(selected_objects)

for tab, object_name in zip(tabs, selected_objects):
    with tab:
        faces = st.session_state.current_faces[object_name]
        face_palette = st.session_state.face_palettes.get(
            object_name,
            copy.deepcopy(DEFAULT_FACE_PALETTE),
        )
        history = st.session_state.rotation_history.get(object_name, [])

        st.caption("Rotation history: " + display_sequence(history))

        col_net, col_3d = st.columns([1, 1])

        with col_net:
            st.markdown("**2D cube net**")

            fig_net = draw_cube_grid_compact(
                faces,
                title=f"{object_name} - 2D",
                face_palette=face_palette,
            )

            st.pyplot(fig_net, use_container_width=False)
            plt.close(fig_net)

        with col_3d:
            st.markdown("**3D reconstruction**")
            fig_3d = draw_voxel_compact(
                faces,
                title=f"{object_name} - 3D",
                elev=elev,
                azim=azim,
                face_palette=face_palette,
            )

            st.pyplot(fig_3d, use_container_width=False)
            plt.close(fig_3d)