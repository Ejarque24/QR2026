# Shortest Path Dataset

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

- objects: ['object1', 'object2', 'object3', 'object4', 'object5', 'object6']
- max_sequence_len: 2
- graph_depth: 3
- sample_count: 444
- distractor_count: 1332
- solvable_count: 297
- unsolved_count: 147
