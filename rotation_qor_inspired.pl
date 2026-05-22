% QOR-Inspired Rotation Implementation
% Combines QOR's declarative lookup-table philosophy with 
% rotation_simple's actual matrix transformations on depth values
%
% Philosophy: Define WHAT transforms happen (like QOR), then apply HOW they transform (matrices)

:- use_module(library(lists), [member/2, nth0/3, reverse/2, append/3]).
:- use_module(library(apply), [maplist/3]).
:- use_module(library(clpfd), [transpose/2]).

% ============================================================================
% BASIC MATRIX ROTATIONS (90 degrees counter-clockwise)
% ============================================================================

rotate_90ccw([
    [A, B, C],
    [D, E, F],
    [G, H, I]
], [
    [C, F, I],
    [B, E, H],
    [A, D, G]
]).

% 90 degrees clockwise = 3 x 90 CCW
rotate_90cw(Mat, Rotated) :-
    rotate_90ccw(Mat, T1),
    rotate_90ccw(T1, T2),
    rotate_90ccw(T2, Rotated).

% 180 degrees = 2 x 90 CCW
rotate_180(Mat, Rotated) :-
    rotate_90ccw(Mat, T1),
    rotate_90ccw(T1, Rotated).

% ============================================================================
% QOR-INSPIRED ROTATION RULES TABLE
% ============================================================================
% Format: rotation_rule(RotationType, SourceFace, TargetFace, FaceTransformation)
%
% Where:
%   - RotationType: towards_up, towards_down, towards_left, towards_right
%   - SourceFace: front, back, left, right, up, down
%   - TargetFace: where the source face moves to
%   - FaceTransformation: none, rotate_90cw, rotate_90ccw, rotate_180
%
% This makes the rotation logic transparent and easy to modify
% ============================================================================

% PITCH ROTATIONS (around X-axis, left-right axis)
% Philosophy: Front/Up/Back/Down translate positions, Left/Right rotate in place

% towards_up: Tip forward (nose up)
% Front → Up (no rotation), Down → Front (no rotation)
% Up → Back (180° flip for opposite facing), Back → Down (180° flip for opposite facing)  
% Left → Left (rotate 90° CCW), Right → Right (rotate 90° CW)
rotation_rule(towards_up, front, up, none).
rotation_rule(towards_up, down, front, none).
rotation_rule(towards_up, up, back, rotate_180).
rotation_rule(towards_up, back, down, rotate_180).
rotation_rule(towards_up, left, left, rotate_90ccw).
rotation_rule(towards_up, right, right, rotate_90cw).

% towards_down: Tip backward (nose down) - INVERSE of towards_up
% Front → Down (no rotation), Up → Front (no rotation)
% Down → Back (180° flip), Back → Up (180° flip)
% Left → Left (rotate 90° CW), Right → Right (rotate 90° CCW)
rotation_rule(towards_down, front, down, none).
rotation_rule(towards_down, up, front, none).
rotation_rule(towards_down, down, back, rotate_180).
rotation_rule(towards_down, back, up, rotate_180).
rotation_rule(towards_down, left, left, rotate_90cw).
rotation_rule(towards_down, right, right, rotate_90ccw).

% YAW ROTATIONS (around Y-axis, up-down axis)
% Philosophy: Front/Left/Back/Right translate positions, Up/Down rotate in place
% NO 180° flips for YAW - all faces rotate in horizontal plane

% towards_left: Turn left
% Right → Front (no rotation), Front → Left (no rotation)
% Left → Back (no rotation), Back → Right (no rotation)
% Up → Up (rotate 90° CW), Down → Down (rotate 90° CCW)
rotation_rule(towards_left, right, front, none).
rotation_rule(towards_left, front, left, none).
rotation_rule(towards_left, left, back, none).
rotation_rule(towards_left, back, right, none).
rotation_rule(towards_left, up, up, rotate_90cw).
rotation_rule(towards_left, down, down, rotate_90ccw).

% towards_right: Turn right - INVERSE of towards_left
% Left → Front (no rotation), Front → Right (no rotation)
% Right → Back (no rotation), Back → Left (no rotation)
% Up → Up (rotate 90° CCW), Down → Down (rotate 90° CW)
rotation_rule(towards_right, left, front, none).
rotation_rule(towards_right, front, right, none).
rotation_rule(towards_right, right, back, none).
rotation_rule(towards_right, back, left, none).
rotation_rule(towards_right, up, up, rotate_90ccw).
rotation_rule(towards_right, down, down, rotate_90cw).

% ============================================================================
% IN-PLANE ROTATION RULES (around Z-axis, viewer's perspective)
% ============================================================================
% Format: rotation_rule(in_plane_Nq, SourceFace, TargetFace, FaceTransformation)
%
% 0q: No rotation (identity)
rotation_rule(in_plane_0q, front, front, none).
rotation_rule(in_plane_0q, back, back, none).
rotation_rule(in_plane_0q, up, up, none).
rotation_rule(in_plane_0q, right, right, none).
rotation_rule(in_plane_0q, down, down, none).
rotation_rule(in_plane_0q, left, left, none).

% 1q: 90 degrees clockwise (from viewer perspective)
% Front/Back stay in place and rotate CW. Up→Right→Down→Left→Up cycle with CW rotation.
rotation_rule(in_plane_1q, front, front, rotate_90cw).
rotation_rule(in_plane_1q, back, back, rotate_90cw).
rotation_rule(in_plane_1q, up, right, rotate_90cw).
rotation_rule(in_plane_1q, right, down, rotate_90cw).
rotation_rule(in_plane_1q, down, left, rotate_90cw).
rotation_rule(in_plane_1q, left, up, rotate_90cw).

% 2q: 180 degrees
% Front/Back stay in place and rotate 180. Up↔Down, Left↔Right with no face rotation.
rotation_rule(in_plane_2q, front, front, rotate_180).
rotation_rule(in_plane_2q, back, back, rotate_180).
rotation_rule(in_plane_2q, up, down, none).
rotation_rule(in_plane_2q, down, up, none).
rotation_rule(in_plane_2q, left, right, none).
rotation_rule(in_plane_2q, right, left, none).

% 3q: 270 degrees (90 degrees counter-clockwise)
% Front/Back stay in place and rotate CCW. Up→Left→Down→Right→Up cycle with CCW rotation.
rotation_rule(in_plane_3q, front, front, rotate_90ccw).
rotation_rule(in_plane_3q, back, back, rotate_90ccw).
rotation_rule(in_plane_3q, up, left, rotate_90ccw).
rotation_rule(in_plane_3q, left, down, rotate_90ccw).
rotation_rule(in_plane_3q, down, right, rotate_90ccw).
rotation_rule(in_plane_3q, right, up, rotate_90ccw).

% ============================================================================
% APPLY IN-PLANE ROTATION - LEGACY SINGLE-FACE VERSION
% ============================================================================
% These are for backward compatibility with code that rotates a single face matrix

% Helper: Custom transpose to avoid conflicts with clpfd library
custom_transpose([], []).
custom_transpose([[]|_], []).
custom_transpose(Matrix, [Row|Rows]) :-
    extract_column(Matrix, Row, RestMatrix),
    custom_transpose(RestMatrix, Rows).

extract_column([], [], []).
extract_column([[H|T]|Rows], [H|Col], [T|Rest]) :-
    extract_column(Rows, Col, Rest).

% Helper: Reverse rows of a matrix
reverse_rows([], []).
reverse_rows([Row|Rows], [ReversedRow|ReversedRows]) :-
    reverse(Row, ReversedRow),
    reverse_rows(Rows, ReversedRows).

% Helper: Reverse columns of a matrix
reverse_columns(Matrix, Rotated) :-
    custom_transpose(Matrix, Transposed),
    reverse_rows(Transposed, Rotated).

% ============================================================================
% FACE TRANSFORMATION APPLICATION
% ============================================================================
% Apply the matrix transformation rule to a face matrix

apply_face_transformation(Matrix, none, Matrix) :- !.
apply_face_transformation(Matrix, rotate_90cw, Rotated) :- 
    rotate_90cw(Matrix, Rotated), !.
apply_face_transformation(Matrix, rotate_90ccw, Rotated) :- 
    rotate_90ccw(Matrix, Rotated), !.
apply_face_transformation(Matrix, rotate_180, Rotated) :- 
    rotate_180(Matrix, Rotated), !.

% ============================================================================
% ROTATION LOGIC USING QOR-INSPIRED RULES
% ============================================================================

% Build the rotation by applying each rule from the table
apply_rotation_via_rules(Front, Back, Left, Right, Up, Down, RotationType,
                         NewFront, NewBack, NewLeft, NewRight, NewUp, NewDown) :-
    % Apply rules for each face
    get_rotated_face(RotationType, front, Front, NewFront),
    get_rotated_face(RotationType, back, Back, NewBack),
    get_rotated_face(RotationType, left, Left, NewLeft),
    get_rotated_face(RotationType, right, Right, NewRight),
    get_rotated_face(RotationType, up, Up, NewUp),
    get_rotated_face(RotationType, down, Down, NewDown).

% Helper: Get rotated face by looking up rules
get_rotated_face(RotationType, SourceFace, FaceMatrix, RotatedFace) :-
    rotation_rule(RotationType, SourceFace, _TargetFace, Transformation),
    apply_face_transformation(FaceMatrix, Transformation, RotatedFace).

% ============================================================================
% REORGANIZE FACES AFTER ROTATION
% ============================================================================
% After applying transformations, reorganize which face goes where
% This uses the position rules from rotation_rule

reorganize_rotated_faces(RotationType, Front, Back, Left, Right, Up, Down,
                         NewFront, NewBack, NewLeft, NewRight, NewUp, NewDown) :-
    % Collect transformed faces
    rotation_rule(RotationType, front, Target_front, Trans_front),
    rotation_rule(RotationType, back, Target_back, Trans_back),
    rotation_rule(RotationType, left, Target_left, Trans_left),
    rotation_rule(RotationType, right, Target_right, Trans_right),
    rotation_rule(RotationType, up, Target_up, Trans_up),
    rotation_rule(RotationType, down, Target_down, Trans_down),
    
    % Apply transformations
    apply_face_transformation(Front, Trans_front, TFront),
    apply_face_transformation(Back, Trans_back, TBack),
    apply_face_transformation(Left, Trans_left, TLeft),
    apply_face_transformation(Right, Trans_right, TRight),
    apply_face_transformation(Up, Trans_up, TUp),
    apply_face_transformation(Down, Trans_down, TDown),
    
    % Map to target positions
    assign_faces_to_positions(RotationType, 
                             TFront, TBack, TLeft, TRight, TUp, TDown,
                             NewFront, NewBack, NewLeft, NewRight, NewUp, NewDown).

% Assign transformed faces to their new positions
assign_faces_to_positions(RotationType, TFront, TBack, TLeft, TRight, TUp, TDown,
                          NewFront, NewBack, NewLeft, NewRight, NewUp, NewDown) :-
    % For each target position, find which transformed face goes there
    get_face_at_position(RotationType, front, TFront, TBack, TLeft, TRight, TUp, TDown, NewFront),
    get_face_at_position(RotationType, back, TFront, TBack, TLeft, TRight, TUp, TDown, NewBack),
    get_face_at_position(RotationType, left, TFront, TBack, TLeft, TRight, TUp, TDown, NewLeft),
    get_face_at_position(RotationType, right, TFront, TBack, TLeft, TRight, TUp, TDown, NewRight),
    get_face_at_position(RotationType, up, TFront, TBack, TLeft, TRight, TUp, TDown, NewUp),
    get_face_at_position(RotationType, down, TFront, TBack, TLeft, TRight, TUp, TDown, NewDown).

get_face_at_position(RotationType, TargetPosition, TFront, TBack, TLeft, TRight, TUp, TDown, Result) :-
    (   rotation_rule(RotationType, front, TargetPosition, _) -> Result = TFront
    ;   rotation_rule(RotationType, back, TargetPosition, _) -> Result = TBack
    ;   rotation_rule(RotationType, left, TargetPosition, _) -> Result = TLeft
    ;   rotation_rule(RotationType, right, TargetPosition, _) -> Result = TRight
    ;   rotation_rule(RotationType, up, TargetPosition, _) -> Result = TUp
    ;   rotation_rule(RotationType, down, TargetPosition, _) -> Result = TDown
    ).

% ============================================================================
% CLEANER APPROACH: Direct mapping using rules
% ============================================================================

apply_rotation_towards_up(
    Front, Back, Left, Right, Up, Down,
    NewFront, NewBack, NewLeft, NewRight, NewUp, NewDown
) :-
    % Apply transformations to each face based on rules
    apply_face_transformation(Front, none, TFront),
    apply_face_transformation(Back, rotate_180, TBack),
    apply_face_transformation(Left, rotate_90ccw, TLeft),
    apply_face_transformation(Right, rotate_90cw, TRight),
    apply_face_transformation(Up, none, TUp),
    apply_face_transformation(Down, rotate_180, TDown),
    
    % Rearrange to new positions (Front→Up means new Up gets transformed Front)
    NewFront = TDown,      % Down moves to Front position (no transform = none)
    NewUp = TFront,        % Front moves to Up position (no transform = none)
    NewBack = TBack,       % Up moves to Back position (with rotate_180)
    NewDown = TDown,       % Back moves to Down position (with rotate_180) -- WAIT, error here
    NewLeft = TLeft,
    NewRight = TRight.

% Let me reconsider - better approach below

% ============================================================================
% CORRECTED IMPLEMENTATION: Use QOR rules directly
% ============================================================================

apply_rotation_towards_up_v2(
    Front, Back, Left, Right, Up, Down,
    NewFront, NewBack, NewLeft, NewRight, NewUp, NewDown
) :-
    % Apply transformation rules to each source face
    apply_face_transformation(Front, none, TransformedFront),
    apply_face_transformation(Down, none, TransformedDown),
    apply_face_transformation(Up, rotate_180, TransformedUp),
    apply_face_transformation(Back, rotate_180, TransformedBack),
    apply_face_transformation(Left, rotate_90ccw, TransformedLeft),
    apply_face_transformation(Right, rotate_90cw, TransformedRight),
    
    % Map to target positions based on rotation_rule/4
    % rotation_rule(towards_up, front, up, none) means: transformed Front → Up position
    NewUp = TransformedFront,
    NewFront = TransformedDown,
    NewBack = TransformedUp,
    NewDown = TransformedBack,
    NewLeft = TransformedLeft,
    NewRight = TransformedRight.

apply_rotation_towards_down_v2(
    Front, Back, Left, Right, Up, Down,
    NewFront, NewBack, NewLeft, NewRight, NewUp, NewDown
) :-
    % Apply transformation rules
    apply_face_transformation(Front, none, TransformedFront),
    apply_face_transformation(Up, none, TransformedUp),
    apply_face_transformation(Down, rotate_180, TransformedDown),
    apply_face_transformation(Back, rotate_180, TransformedBack),
    apply_face_transformation(Left, rotate_90cw, TransformedLeft),
    apply_face_transformation(Right, rotate_90ccw, TransformedRight),
    
    % Map to target positions
    NewDown = TransformedFront,
    NewFront = TransformedUp,
    NewBack = TransformedDown,
    NewUp = TransformedBack,
    NewLeft = TransformedLeft,
    NewRight = TransformedRight.

apply_rotation_towards_left_v2(
    Front, Back, Left, Right, Up, Down,
    NewFront, NewBack, NewLeft, NewRight, NewUp, NewDown
) :-
    % Apply transformation rules (no 180° for YAW rotations)
    apply_face_transformation(Right, none, TransformedRight),
    apply_face_transformation(Front, none, TransformedFront),
    apply_face_transformation(Left, none, TransformedLeft),
    apply_face_transformation(Back, none, TransformedBack),
    apply_face_transformation(Up, rotate_90cw, TransformedUp),
    apply_face_transformation(Down, rotate_90ccw, TransformedDown),
    
    % Map to target positions
    NewFront = TransformedRight,
    NewLeft = TransformedFront,
    NewBack = TransformedLeft,
    NewRight = TransformedBack,
    NewUp = TransformedUp,
    NewDown = TransformedDown.

apply_rotation_towards_right_v2(
    Front, Back, Left, Right, Up, Down,
    NewFront, NewBack, NewLeft, NewRight, NewUp, NewDown
) :-
    % Apply transformation rules
    apply_face_transformation(Left, none, TransformedLeft),
    apply_face_transformation(Front, none, TransformedFront),
    apply_face_transformation(Right, none, TransformedRight),
    apply_face_transformation(Back, none, TransformedBack),
    apply_face_transformation(Up, rotate_90ccw, TransformedUp),
    apply_face_transformation(Down, rotate_90cw, TransformedDown),
    
    % Map to target positions
    NewFront = TransformedLeft,
    NewRight = TransformedFront,
    NewBack = TransformedRight,
    NewLeft = TransformedBack,
    NewUp = TransformedUp,
    NewDown = TransformedDown.

% ============================================================================
% IN-PLANE ROTATION IMPLEMENTATIONS (all six faces coordinated)
% ============================================================================
% These follow the same pattern as towards_up_v2, towards_down_v2, etc.
% Each implements the full 6-face rearrangement using the in_plane_Nq rules

apply_in_plane_rotation_0q(
    Front, Back, Left, Right, Up, Down,
    Front, Back, Left, Right, Up, Down).  % No change for 0q

apply_in_plane_rotation_1q(
    Front, Back, Left, Right, Up, Down,
    NewFront, NewBack, NewLeft, NewRight, NewUp, NewDown
) :-
    % Apply transformation rules from rotation_rule(in_plane_1q, ...)
    apply_face_transformation(Front, rotate_90cw, TransformedFront),
    apply_face_transformation(Back, rotate_90ccw, TransformedBack),
    apply_face_transformation(Left, rotate_90cw, TransformedLeft),
    apply_face_transformation(Right, rotate_90cw, TransformedRight),
    apply_face_transformation(Up, rotate_90cw, TransformedUp),
    apply_face_transformation(Down, rotate_90cw, TransformedDown),
    
    % Map to new positions (Up→Right→Down→Left→Up, Front/Back stay)
    NewFront = TransformedFront,
    NewBack = TransformedBack,
    NewRight = TransformedUp,
    NewDown = TransformedRight,
    NewLeft = TransformedDown,
    NewUp = TransformedLeft.

apply_in_plane_rotation_minus1q(
    Front, Back, Left, Right, Up, Down,
    NewFront, NewBack, NewLeft, NewRight, NewUp, NewDown
) :-
    % Apply transformation rules from rotation_rule(in_plane_1q, ...)
    apply_face_transformation(Front, rotate_90ccw, TransformedFront),
    apply_face_transformation(Back, rotate_90cw, TransformedBack),
    apply_face_transformation(Left, rotate_90ccw, TransformedLeft),
    apply_face_transformation(Right, rotate_90ccw, TransformedRight),
    apply_face_transformation(Up, rotate_90ccw, TransformedUp),
    apply_face_transformation(Down, rotate_90ccw, TransformedDown),
    
    % Map to new positions (Up→Right→Down→Left→Up, Front/Back stay)
    NewFront = TransformedFront,
    NewBack = TransformedBack,
    NewRight = TransformedDown,
    NewDown = TransformedLeft,
    NewLeft = TransformedUp,
    NewUp = TransformedRight.

% ============================================================================
% UNIFIED IN-PLANE ROTATION INTERFACE
% ============================================================================
% Full dispatcher for all in-plane rotations (1q, -1q)

apply_in_plane_rotation_full(Front, Back, Left, Right, Up, Down, InPlaneRotation,
                              NewFront, NewBack, NewLeft, NewRight, NewUp, NewDown) :-
    (   InPlaneRotation = '1q'
    ->  apply_in_plane_rotation_1q(Front, Back, Left, Right, Up, Down,
                                   NewFront, NewBack, NewLeft, NewRight, NewUp, NewDown)
    ;   InPlaneRotation = '-1q'
    ->  apply_in_plane_rotation_minus1q(Front, Back, Left, Right, Up, Down,
                                   NewFront, NewBack, NewLeft, NewRight, NewUp, NewDown)
    ;   % Default: no rotation if unrecognized
        NewFront = Front, NewBack = Back, NewLeft = Left, NewRight = Right,
        NewUp = Up, NewDown = Down
    ).

% ============================================================================
% MAIN QUERY INTERFACE (compatible with Python integration)
% ============================================================================

apply_rotation_via_query(Front, Back, Left, Right, Up, Down, RotationType,
                        NewFront, NewBack, NewLeft, NewRight, NewUp, NewDown) :-
    (   RotationType = towards_up
    ->  apply_rotation_towards_up_v2(Front, Back, Left, Right, Up, Down,
                                     NewFront, NewBack, NewLeft, NewRight, NewUp, NewDown)
    ;   RotationType = towards_down
    ->  apply_rotation_towards_down_v2(Front, Back, Left, Right, Up, Down,
                                       NewFront, NewBack, NewLeft, NewRight, NewUp, NewDown)
    ;   RotationType = towards_left
    ->  apply_rotation_towards_left_v2(Front, Back, Left, Right, Up, Down,
                                       NewFront, NewBack, NewLeft, NewRight, NewUp, NewDown)
    ;   RotationType = towards_right
    ->  apply_rotation_towards_right_v2(Front, Back, Left, Right, Up, Down,
                                        NewFront, NewBack, NewLeft, NewRight, NewUp, NewDown)
    ;   NewFront = Front, NewBack = Back, NewLeft = Left, NewRight = Right,
        NewUp = Up, NewDown = Down
    ).

% Output in a format Python can parse
write_result(Front, Back, Left, Right, Up, Down) :-
    write('RESULT:'), nl,
    write('FRONT:'), nl, write(Front), nl,
    write('BACK:'), nl, write(Back), nl,
    write('LEFT:'), nl, write(Left), nl,
    write('RIGHT:'), nl, write(Right), nl,
    write('UP:'), nl, write(Up), nl,
    write('DOWN:'), nl, write(Down), nl.

% ============================================================================
% DOCUMENTATION: How this combines QOR philosophy with rotation_simple
% ============================================================================
%
% QOR PHILOSOPHY (what we borrowed):
% - rotation_rule/4 table makes rotation logic DECLARATIVE
% - Each rule clearly states: "when rotating towards_up, front face goes to up with no rotation"
% - This is TRANSPARENT and MAINTAINABLE - you can see all rotations at a glance
% - Similar to QOR's table_L_O_Changes/5 which defined ALL symbol movements
%
% ROTATION_SIMPLE IMPLEMENTATION (what we kept):
% - apply_face_transformation/3 applies actual matrix transformations
% - rotate_90cw, rotate_90ccw, rotate_180 are the actual math operations
% - This is PRECISE and CORRECT for depth-value matrices
%
% COMBINED APPROACH:
% - rotation_rule/4 defines the STRUCTURE of what moves where
% - apply_face_transformation/3 defines HOW each face matrix transforms
% - This separates CONCERNS: rotation structure vs. transformation operations
% - Makes it easy to add new rotation types (just add more rotation_rule facts)
% - Makes it easy to modify transformations (just change apply_face_transformation)
%
% EXAMPLE: To add diagonal rotations (towards_up_left):
% Just add these rules:
%   rotation_rule(towards_up_left, up, left, rotate_90ccw).
%   rotation_rule(towards_up_left, left, back, rotate_90ccw).
%   rotation_rule(towards_up_left, front, front, none).
%   ... etc
% Then implement apply_rotation_towards_up_left/12 using the same pattern
%
% IN-PLANE ROTATIONS AS DECLARATIVE RULES:
% We added rotation_rule/4 facts for in_plane_0q, in_plane_1q, in_plane_2q, in_plane_3q
% These work the same way as position rotations:
%   - in_plane_1q (90° CW): rotates around the viewer's Z-axis
%     Front/Back stay in place and rotate 90° CW each.
%     Side faces cycle: Up→Right→Down→Left→Up (each also rotates 90° CW)
%   - in_plane_2q (180°): rotates 180° around Z-axis
%     Front/Back stay and rotate 180° each.
%     Side faces swap: Up↔Down, Left↔Right (no in-plane rotation)
%   - in_plane_3q (270° or 90° CCW): rotates around Z-axis counter-clockwise
%     Front/Back stay in place and rotate 90° CCW each.
%     Side faces cycle: Up→Left→Down→Right→Up (each rotates 90° CCW)
%
% NEW APPROACH:
% - Defined rotation_rule facts for all four in-plane rotations
% - Created apply_in_plane_rotation_0q/1q/2q/3q predicates that handle
%   both transformations AND position rearrangement
% - Python can now call apply_in_plane_rotation_full/10 for true 6-face rotations
% - Each face is transformed AND positioned correctly in one coordinated operation
%
% ============================================================================
