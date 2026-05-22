#!/usr/bin/env python3
"""
3D visualization for Object 1 using depth-maps (raycast collisions)

Reconstructs a plausible 3x3x3 voxel occupancy from the six face depth-maps
and renders:

1. The original object
2. The four normal rotated variants:
   - towards_up
   - towards_down
   - towards_left
   - towards_right
3. For each normal rotation, the supported in-plane rotations:
   - 1q
   - -1q

This script imports helper functions from visualize_cubes_qor.py to extract
faces and apply the QOR-inspired Prolog rotations.

Important:
- In-plane rotations are cube-level rotations.
- This script does NOT call per-face in-plane rotation.
- This script assumes visualize_cubes_qor.py has apply_in_plane_rotation()
  implemented using Prolog apply_in_plane_rotation_full/13.
"""

from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

import visualize_cubes_qor as vcq


# ============================================================================
# OUTPUT CONFIG
# ============================================================================

OUTPUT_DIR = Path(__file__).parent / 'generated_apply_in_rotation_2026_05_12'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# VOXEL CONFIG
# ============================================================================

# Map depth labels to voxel layer index.
# Clamp deeper labels to the back layer.
DEPTH_TO_LAYER = {
    'a': 0,
    'b': 1,
    'c': 2,
    'd': 2,
    'e': 2,
}

DEFAULT_PERM = (2, 0, 1)
DEFAULT_FLIPS = (1, 0, 1)
DEFAULT_VOXEL_COLOR = '#FFD700'


# ============================================================================
# GEOMETRY HELPERS
# ============================================================================

def _map_face_to_xyz(face_name, r, c, layer):
    """Map face, row, col, layer to voxel x,y,z using 3x3x3 convention."""
    if face_name == 'front':
        x = c
        y = r
        z = layer

    elif face_name == 'back':
        x = 2 - c
        y = r
        z = 2 - layer

    elif face_name == 'left':
        x = layer
        y = r
        z = 2 - c

    elif face_name == 'right':
        x = 2 - layer
        y = r
        z = c

    elif face_name == 'up':
        x = c
        y = layer
        z = 2 - r

    elif face_name == 'down':
        x = c
        y = 2 - layer
        z = r

    else:
        x = y = z = -1

    return x, y, z


def _ray_indices_for_face(face_name, r, c, size):
    """Return list of (x,y,z) along ray from face into cube, nearest to farthest."""
    indices = []

    for layer in range(size):
        x, y, z = _map_face_to_xyz(face_name, r, c, layer)

        if 0 <= x < size and 0 <= y < size and 0 <= z < size:
            indices.append((x, y, z))

    return indices


def safe_rotation_name(rotation):
    """Make rotation names safe and readable in filenames."""
    return str(rotation).replace('-', 'minus_')


# ============================================================================
# VOXEL RECONSTRUCTION
# ============================================================================

def reconstruct_voxels_from_faces(faces, size=3, fusion='union'):
    """
    Return occupancy and per-voxel color based on face hits.

    faces:
        dict of 6 matrices:
        front, back, left, right, up, down

    fusion:
        - union
        - priority
        - majority
        - space_carving
    """
    occ = np.zeros((size, size, size), dtype=bool)
    colors = np.zeros((size, size, size, 4), dtype=float)

    face_order = ['front', 'right', 'back', 'left', 'up', 'down']

    if fusion in {'union', 'priority'}:
        for face_name in face_order:
            mat = faces.get(face_name)

            if mat is None:
                continue

            for r in range(len(mat)):
                for c in range(len(mat[r])):
                    val = mat[r][c]

                    if val == '*':
                        continue

                    layer = DEPTH_TO_LAYER.get(val, 2)
                    x, y, z = _map_face_to_xyz(face_name, r, c, layer)

                    if 0 <= x < size and 0 <= y < size and 0 <= z < size:
                        if not occ[x, y, z]:
                            occ[x, y, z] = True
                            hexcol = vcq.DEPTH_COLORS.get(val, '#999999')

                            try:
                                rgba = mcolors.to_rgba(hexcol)
                            except Exception:
                                rgba = (0.6, 0.6, 0.6, 1.0)

                            colors[x, y, z] = rgba

    elif fusion == 'majority':
        votes = np.zeros((size, size, size), dtype=int)
        vote_color = {}

        for face_name in face_order:
            mat = faces.get(face_name)

            if mat is None:
                continue

            for r in range(len(mat)):
                for c in range(len(mat[r])):
                    val = mat[r][c]

                    if val == '*':
                        continue

                    layer = DEPTH_TO_LAYER.get(val, 2)
                    x, y, z = _map_face_to_xyz(face_name, r, c, layer)

                    if 0 <= x < size and 0 <= y < size and 0 <= z < size:
                        votes[x, y, z] += 1

                        if (x, y, z) not in vote_color:
                            vote_color[(x, y, z)] = vcq.DEPTH_COLORS.get(val, '#999999')

        threshold = 2
        coords = np.argwhere(votes >= threshold)

        for x, y, z in coords:
            occ[x, y, z] = True
            hexcol = vote_color.get((x, y, z), '#999999')

            try:
                colors[x, y, z] = mcolors.to_rgba(hexcol)
            except Exception:
                colors[x, y, z] = (0.6, 0.6, 0.6, 1.0)

    elif fusion == 'space_carving':
        occ[:] = True

        for face_name in face_order:
            mat = faces.get(face_name)

            if mat is None:
                continue

            for r in range(len(mat)):
                for c in range(len(mat[r])):
                    val = mat[r][c]
                    ray = _ray_indices_for_face(face_name, r, c, size)

                    if val == '*':
                        for x, y, z in ray:
                            occ[x, y, z] = False
                            colors[x, y, z] = (0, 0, 0, 0)

                    else:
                        layer = DEPTH_TO_LAYER.get(val, 2)

                        for idx, (x, y, z) in enumerate(ray):
                            if idx > layer:
                                occ[x, y, z] = False
                                colors[x, y, z] = (0, 0, 0, 0)

                        sx, sy, sz = _map_face_to_xyz(face_name, r, c, layer)

                        if 0 <= sx < size and 0 <= sy < size and 0 <= sz < size:
                            occ[sx, sy, sz] = True
                            hexcol = vcq.DEPTH_COLORS.get(val, '#999999')

                            try:
                                colors[sx, sy, sz] = mcolors.to_rgba(hexcol)
                            except Exception:
                                colors[sx, sy, sz] = (0.6, 0.6, 0.6, 1.0)

    else:
        return reconstruct_voxels_from_faces(faces, size=size, fusion='union')

    return occ, colors


# ============================================================================
# PLOTTING
# ============================================================================

def plot_voxels(
    occ,
    colors,
    title=None,
    save_path=None,
    elev=30,
    azim=45,
    uniform_color=None
):
    """Render a single voxel grid and save as PNG."""
    fig = plt.figure(figsize=(4, 4))
    ax = fig.add_subplot(111, projection='3d')

    filled = occ

    facecolors = np.zeros_like(colors)
    facecolors[...] = colors
    facecolors[~filled] = (0, 0, 0, 0)

    if uniform_color:
        try:
            uniform_rgba = mcolors.to_rgba(uniform_color)
        except Exception:
            uniform_rgba = (0.85, 0.55, 0.0, 1.0)

        facecolors[filled] = uniform_rgba

    ax.voxels(filled, facecolors=facecolors, edgecolor='k')
    ax.set_axis_off()

    if title:
        ax.set_title(title)

    ax.view_init(elev=elev, azim=azim)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved: {save_path}")

    plt.close(fig)


def apply_axis_ops(occ, colors, perm=(2, 0, 1), flips=(1, 0, 1)):
    """
    Permute and flip axes of occ/colors.

    perm:
        permutation tuple for axes x,y,z

    flips:
        tuple of 0/1 indicating flip for each permuted axis
    """
    occ_t = np.transpose(occ, perm)
    colors_t = np.transpose(colors, perm + (3,))

    for axis, do_flip in enumerate(flips):
        if do_flip:
            occ_t = np.flip(occ_t, axis=axis)
            colors_t = np.flip(colors_t, axis=axis)

    return occ_t, colors_t


# ============================================================================
# RENDERING PIPELINE
# ============================================================================

def render_faces_as_voxels(
    faces,
    title,
    save_path,
    fusion='priority',
    elev=30,
    azim=45,
    uniform_color=DEFAULT_VOXEL_COLOR
):
    """Reconstruct, map, and render one cube state."""
    occ, colors = reconstruct_voxels_from_faces(faces, size=3, fusion=fusion)

    occ_t, colors_t = apply_axis_ops(
        occ,
        colors,
        perm=DEFAULT_PERM,
        flips=DEFAULT_FLIPS
    )

    plot_voxels(
        occ_t,
        colors_t,
        title,
        save_path,
        elev=elev,
        azim=azim,
        uniform_color=uniform_color
    )


def render_object1_3d():
    """Render object1 original, normal rotations, and 1q/-1q in-plane variants."""
    faces = vcq.extract_faces_from_q3d('object1')
    base = OUTPUT_DIR

    print("Rendering original object1...")

    render_faces_as_voxels(
        faces,
        'object1 - reconstructed (priority, mapped)',
        base / 'object1_3d_priority_mapped.png',
        fusion='priority'
    )

    rotations = [
        'towards_up',
        'towards_down',
        'towards_left',
        'towards_right'
    ]

    in_plane_rotations = [
        '1q',
        '-1q'
    ]

    for rot in rotations:
        print(f"Computing rotation: {rot} (priority)")

        rotated = vcq.apply_rotation_via_prolog(faces, rot)

        savep = base / f'object1_3d_{rot}_priority_mapped.png'

        render_faces_as_voxels(
            rotated,
            f'object1 - {rot} (priority, mapped)',
            savep,
            fusion='priority'
        )

        for in_rot in in_plane_rotations:
            print(f"Computing in-plane rotation: {rot} + {in_rot} (priority)")

            in_rotated = vcq.apply_in_plane_rotation(rotated, in_rot)

            safe_in_rot = safe_rotation_name(in_rot)

            savep_in = base / f'object1_3d_{rot}_{safe_in_rot}_priority_mapped.png'

            render_faces_as_voxels(
                in_rotated,
                f'object1 - {rot} + {in_rot} (priority, mapped)',
                savep_in,
                fusion='priority'
            )


def render_all_fusion_policies():
    """
    Render original and normal rotations for all fusion policies.

    This function keeps fusion-policy comparisons focused on the normal cube rotations.
    It does not generate in-plane variants, to avoid producing many files.
    """
    faces = vcq.extract_faces_from_q3d('object1')
    base = OUTPUT_DIR

    policies = [
        'priority',
        'union',
        'majority',
        'space_carving'
    ]

    rotations = [
        'towards_up',
        'towards_down',
        'towards_left',
        'towards_right'
    ]

    for policy in policies:
        print(f"Rendering policy: {policy}")

        render_faces_as_voxels(
            faces,
            f'object1 - {policy}',
            base / f'object1_3d_{policy}_mapped.png',
            fusion=policy
        )

        for rot in rotations:
            print(f"Rendering policy {policy} with rotation {rot}")

            rotated = vcq.apply_rotation_via_prolog(faces, rot)

            render_faces_as_voxels(
                rotated,
                f'object1 - {policy} {rot}',
                base / f'object1_3d_{policy}_{rot}_mapped.png',
                fusion=policy
            )


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print('Rendering 3D voxel reconstructions for object1...')
    print('Supported in-plane rotations: 1q, -1q')
    print()

    render_object1_3d()

    print()
    print('Done.')