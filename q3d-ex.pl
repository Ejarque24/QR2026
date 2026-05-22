:- use_module(library(clpfd),  [transpose/2]).
:- use_module(library(lists),  [nth0/3, nth1/3, member/2, numlist/3, same_length/2, append/3, flatten/2]).
:- use_module(library(apply),  [maplist/3, foldl/4]).
:- use_module(library(ordsets), [ord_subtract/3]).

:- dynamic view/5.
:- dynamic inferred_view/6.

:- dynamic triggered_rule/6.
% triggered_rule(Obj, Face, Row, Col, RuleName, Value).

clear_inferred :- retractall(inferred_view(_,_,_,_,_,_)).
clear_triggered_rules :- retractall(triggered_rule(_,_,_,_,_,_)).

log_write(Obj, Face, Row, Col, RuleName, Value) :-
    assertz(triggered_rule(Obj, Face, Row, Col, RuleName, Value)).

/* =========================================================
   1) DATA (view/5 facts)
   --------------------------------------------------------- */

% ---------- Object 1 ----------
view(front, object1, 3, 3, [[c,c,*],[b,a,c],[a,a,a]]).
view(right, object1, 3, 3, [[*,*,b],[b,b,a],[a,a,a]]).
view(up,    object1, 3, 3, [[a,a,b],[b,b,c],[c,b,c]]).
view(back,  object1, 3, 3, [[*,a,a],[a,a,a],[a,a,a]]).
view(left,  object1, 3, 3, [[a,*,*],[a,a,b],[a,a,a]]).
view(down,  object1, 3, 3, [[a,a,a],[a,a,a],[a,a,a]]).

% ---------- Object 2 ----------
view(front, object2, 3, 3, [[c,*,*],[a,b,c],[a,a,b]]).
view(right, object2, 3, 3, [[*,*,c],[c,b,a],[b,a,a]]).
view(up,    object2, 3, 3, [[a,b,b],[b,b,c],[b,c,*]]).
view(back,  object2, 3, 3, [[*,*,a],[a,a,a],[a,a,a]]).
view(left,  object2, 3, 3, [[a,*,*],[a,a,a],[a,a,a]]).
view(down,  object2, 3, 3, [[a,a,*],[a,a,a],[a,a,a]]).

% ---------- Object 3 ----------
view(front, object3, 3, 3, [[a,*,a],[a,a,a],[a,a,a]]).
view(right, object3, 3, 3, [[a,*,a],[a,a,a],[a,a,a]]).
view(up,    object3, 3, 3, [[a,b,a],[b,b,b],[a,b,a]]).
view(back,  object3, 3, 3, [[a,*,a],[a,a,a],[a,a,a]]).
view(left,  object3, 3, 3, [[a,*,a],[a,a,a],[a,a,a]]).
view(down,  object3, 3, 3, [[a,a,a],[a,a,a],[a,a,a]]).

% ---------- Object 4 ----------
view(front, object4, 3, 3, [[b,a,a],[b,a,a],[a,a,a]]).
view(right, object4, 3, 3, [[a,b,a],[a,b,a],[a,b,a]]).
view(up,    object4, 3, 3, [[a,a,a],[a,a,*],[c,a,a]]).
view(back,  object4, 3, 3, [[a,a,a],[a,a,a],[a,a,a]]).
view(left,  object4, 3, 3, [[a,a,b],[a,a,b],[a,a,a]]).
view(down,  object4, 3, 3, [[a,a,a],[a,a,*],[a,a,a]]).

% ---------- DST_01 ----------
view(front, object5, 3, 3, [[c,*,*],[a,*,*],[a,a,a]]).
view(right, object5, 3, 3, [[*,*,c],[c,c,c],[a,b,b]]).
view(up,    object5, 3, 3, [[a,c,*],[b,c,*],[b,c,c]]).
view(back,  object5, 3, 3, [[*,*,a],[*,*,a],[c,a,a]]).
view(left,  object5, 3, 3, [[a,*,*],[a,a,a],[a,a,a]]).
view(down,  object5, 3, 3, [[a,a,a],[a,a,*],[a,a,*]]).

% ---------- DST_02 ----------
view(front, object6, 3, 3, [[*,b,*],[*,a,b],[*,a,a]]).
view(right, object6, 3, 3, [[*,b,*],[b,a,b],[a,a,a]]).
view(up,    object6, 3, 3, [[*,b,c],[*,a,b],[*,b,c]]).
view(back,  object6, 3, 3, [[*,b,*],[b,a,*],[a,a,*]]).
view(left,  object6, 3, 3, [[*,b,*],[b,b,b],[b,b,b]]).
view(down,  object6, 3, 3, [[*,a,a],[*,a,a],[*,a,a]]).

% ---------- DST_03 ----------
view(front, object7, 3, 3, [[*,b,*],[*,b,*],[*,a,c]]).
view(right, object7, 3, 3, [[*,b,*],[*,b,b],[b,b,a]]).
view(up,    object7, 3, 3, [[*,b,c],[*,a,*],[*,c,*]]).
view(back,  object7, 3, 3, [[*,b,*],[*,a,*],[a,a,*]]).
view(left,  object7, 3, 3, [[*,b,*],[b,b,*],[b,b,b]]).
view(down,  object7, 3, 3, [[*,a,*],[*,a,*],[*,a,a]]).

% ---------- PAT_5A ----------
view(front, object8, 4, 4, [[*,b,*,*],[*,a,b,*],[*,a,b,*],[a,a,a,b]]).
view(right, object8, 4, 4, [[*,c,*,*],[c,b,*,*],[c,b,*,*],[b,a,*,*]]).
view(up,    object8, 4, 4, [[*,*,*,*],[*,*,*,*],[d,a,b,d],[d,b,d,*]]).
view(back,  object8, 4, 4, [[*,*,c,*],[*,c,c,*],[*,c,c,*],[c,c,c,c]]).
view(left,  object8, 4, 4, [[*,*,b,*],[*,*,b,b],[*,*,b,b],[*,*,a,a]]).
view(down,  object8, 4, 4, [[a,a,a,*],[a,a,a,a],[*,*,*,*],[*,*,*,*]]).

% ---------- PAT_5B ----------
view(front, object9, 5, 5, [[*,*,*,*,*],[*,*,*,*,*],[*,*,*,*,a],[c,*,*,*,a],[a,a,a,a,a]]).
view(right, object9, 5, 5, [[*,*,*,*,*],[*,*,*,*,*],[a,*,*,*,*],[a,a,a,*,*],[a,a,a,*,*]]).
view(up,    object9, 5, 5, [[*,*,*,*,*],[*,*,*,*,*],[d,*,*,*,d],[e,*,e,*,d],[e,e,e,e,c]]).
view(back,  object9, 5, 5, [[*,*,*,*,*],[*,*,*,*,*],[e,*,*,*,*],[c,*,*,*,c],[c,e,d,e,c]]).
view(left,  object9, 5, 5, [[*,*,*,*,*],[*,*,*,*,*],[*,*,*,*,e],[*,*,a,e,e],[*,*,a,a,a]]).
view(down,  object9, 5, 5, [[a,a,a,a,a],[a,*,a,*,a],[a,*,*,*,a],[*,*,*,*,*],[*,*,*,*,*]]).

% ---------- PAT_5C ----------
view(front, object10, 4, 4, [[*,*,*,*],[*,d,*,*],[b,d,d,*],[a,a,c,d]]).
view(right, object10, 4, 4, [[*,*,*,*],[*,*,*,c],[*,d,d,b],[c,d,b,a]]).
view(up,    object10, 4, 4, [[c,b,c,d],[c,*,d,*],[c,*,*,*],[d,d,*,*]]).
view(back,  object10, 4, 4, [[*,*,*,*],[*,*,a,*],[*,a,a,a],[a,a,a,a]]).
view(left,  object10, 4, 4, [[*,*,*,*],[b,*,*,*],[a,a,a,*],[a,a,a,a]]).
view(down,  object10, 4, 4, [[a,a,*,*],[a,*,*,*],[a,*,a,*],[a,a,a,a]]).

% ---------- PAT_5D ----------
view(front, object11, 4, 4, [[*,*,c,*],[*,*,c,*],[*,*,c,c],[*,*,c,a]]).
view(right, object11, 4, 4, [[*,*,b,b],[*,*,b,b],[*,*,a,b],[a,a,a,a]]).
view(up,    object11, 4, 4, [[*,*,a,d],[*,*,a,c],[*,*,*,d],[*,*,*,d]]).
view(back,  object11, 4, 4, [[*,a,*,*],[*,a,*,*],[b,a,*,*],[a,a,*,*]]).
view(left,  object11, 4, 4, [[c,c,*,*],[c,c,*,*],[c,c,*,*],[c,c,d,d]]).
view(down,  object11, 4, 4, [[*,*,*,a],[*,*,*,a],[*,*,a,a],[*,*,a,a]]).

% ---------- PAT_5Z ----------
view(front, object12, 2, 2, [[b,*],[a,b]]).
view(right, object12, 2, 2, [[*,b],[b,a]]).
view(up,    object12, 2, 2, [[a,b],[b,*]]).
view(back,  object12, 2, 2, [[*,a],[a,a]]).
view(left,  object12, 2, 2, [[a,*],[a,a]]).
view(down,  object12, 2, 2, [[a,*],[a,a]]).

% ---------- PAT_100 ----------
view(front, object13, 5, 5, [[*,*,*,*,*],[a,*,*,*,*],[a,a,d,d,d],[a,e,e,e,e],[a,e,e,e,e]]).
view(right, object13, 5, 5, [[*,*,*,*,*],[e,e,e,e,e],[d,d,d,a,a],[e,e,e,e,a],[e,e,e,e,a]]).
view(up,    object13, 5, 5, [[b,c,c,c,c],[b,c,c,c,c],[b,c,*,*,*],[b,c,*,*,*],[b,c,*,*,*]]).
view(back,  object13, 5, 5, [[*,*,*,*,*],[*,*,*,*,a],[a,a,a,a,a],[a,a,a,a,a],[a,a,a,a,a]]).
view(left,  object13, 5, 5, [[*,*,*,*,*],[a,a,a,a,a],[a,a,a,a,a],[a,a,a,a,a],[a,a,a,a,a]]).
view(down,  object13, 5, 5, [[a,c,*,*,*],[a,c,*,*,*],[a,c,*,*,*],[a,c,c,c,c],[a,a,a,a,a]]).

% ---------- PAT_113 ----------
view(front, object14, 4, 4, [[*,d,d,d],[*,b,d,d],[*,a,d,d],[*,a,a,a]]).
view(right, object14, 4, 4, [[*,*,*,a],[*,c,c,a],[c,c,c,a],[a,a,a,a]]).
view(up,    object14, 4, 4, [[*,a,a,a],[*,b,*,d],[*,b,*,d],[*,c,d,d]]).
view(back,  object14, 4, 4, [[a,a,a,*],[a,a,a,*],[a,a,a,*],[a,a,a,*]]).
view(left,  object14, 4, 4, [[a,*,*,*],[a,a,a,*],[a,a,a,a],[a,a,a,a]]).
view(down,  object14, 4, 4, [[*,a,a,a],[*,a,*,a],[*,a,*,a],[*,a,a,a]]).

% ---------- PAT_222 ----------
view(front, object15, 3, 3, [[a,a,a],[a,a,a],[a,*,a]]).
view(right, object15, 3, 3, [[a,a,a],[a,a,a],[a,a,a]]).
view(up,    object15, 3, 3, [[a,*,a],[a,a,a],[a,a,a]]).
view(back,  object15, 3, 3, [[a,b,a],[a,b,a],[a,*,a]]).
view(left,  object15, 3, 3, [[a,a,a],[a,a,a],[a,a,a]]).
view(down,  object15, 3, 3, [[a,b,a],[a,b,a],[a,*,a]]).

% ---------- PAT_224 ----------
view(front, object16, 5, 5, [[*,*,*,*,*],[a,b,*,b,a],[a,b,b,b,a],[a,b,b,b,a],[a,a,a,a,a]]).
view(right, object16, 5, 5, [[*,*,*,*,*],[a,a,*,*,*],[a,a,*,*,*],[a,a,*,*,*],[a,a,*,*,*]]).
view(up,    object16, 5, 5, [[*,*,*,*,*],[*,*,*,*,*],[*,*,*,*,*],[b,b,c,b,b],[b,e,e,e,b]]).
view(back,  object16, 5, 5, [[*,*,*,*,*],[c,c,*,c,c],[c,c,c,c,c],[c,c,c,c,c],[c,c,c,c,c]]).
view(left,  object16, 5, 5, [[*,*,*,*,*],[*,*,*,a,a],[*,*,*,a,a],[*,*,*,a,a],[*,*,*,a,a]]).
view(down,  object16, 5, 5, [[a,a,a,a,a],[a,a,a,a,a],[*,*,*,*,*],[*,*,*,*,*],[*,*,*,*,*]]).

% ---------- PAT_225 ----------
view(front, object17, 4, 4, [[d,d,d,*],[c,c,c,*],[b,c,b,*],[b,c,b,*]]).
view(right, object17, 4, 4, [[*,*,*,b],[*,*,b,b],[*,b,b,b],[*,b,b,b]]).
view(up,    object17, 4, 4, [[a,a,a,*],[b,b,b,*],[c,*,c,*],[*,*,*,*]]).
view(back,  object17, 4, 4, [[*,a,a,a],[*,a,a,a],[*,a,a,a],[*,a,a,a]]).
view(left,  object17, 4, 4, [[a,*,*,*],[a,a,*,*],[a,a,a,*],[a,a,a,*]]).
view(down,  object17, 4, 4, [[*,*,*,*],[a,*,a,*],[a,a,a,*],[a,a,a,*]]).

% ---------- PAT_230 ----------
view(front, object18, 6, 6, [[a,a,a,a,a,a],[a,a,a,a,a,a],[a,a,a,a,a,a],[a,a,a,a,a,a],[a,a,a,a,a,a],[a,a,a,a,a,a]]).
view(right, object18, 6, 6, [[a,a,a,a,a,*],[a,a,a,a,a,*],[a,a,a,a,a,*],[a,a,a,a,a,*],[a,a,a,a,a,*],[a,a,a,a,a,*]]).
view(up,    object18, 6, 6, [[*,*,*,*,*,*],[a,a,a,a,a,a],[a,c,c,c,c,a],[a,c,*,*,c,a],[a,c,c,c,c,a],[a,a,a,a,a,a]]).
view(back,  object18, 6, 6, [[a,a,a,a,a,a],[a,a,a,a,a,a],[a,a,a,a,a,a],[a,a,a,a,a,a],[a,a,a,a,a,a],[a,a,a,a,a,a]]).
view(left,  object18, 6, 6, [[*,a,a,a,a,a],[*,a,a,a,a,a],[*,a,a,a,a,a],[*,a,a,a,a,a],[*,a,a,a,a,a],[*,a,a,a,a,a]]).
view(down,  object18, 6, 6, [[a,a,a,a,a,a],[a,a,a,a,a,a],[a,a,*,*,a,a],[a,a,a,a,a,a],[a,a,a,a,a,a],[*,*,*,*,*,*]]).

% ---------- PAT_219 ----------
view(front, object19, 5, 5, [[d,d,d,d,d],[d,d,d,d,d],[e,e,e,e,e],[a,a,a,a,a],[a,a,a,a,a]]).
view(right, object19, 5, 5, [[*,*,*,a,a],[*,*,*,a,a],[*,*,*,*,a],[a,a,a,a,a],[a,*,a,a,a]]).
view(up,    object19, 5, 5, [[a,a,a,a,a],[a,a,a,a,a],[d,d,d,d,d],[d,d,d,d,d],[d,d,d,d,d]]).
view(back,  object19, 5, 5, [[a,a,a,a,a],[a,a,a,a,a],[a,a,a,a,a],[a,a,a,a,a],[a,a,a,a,a]]).
view(left,  object19, 5, 5, [[a,a,*,*,*],[a,a,*,*,*],[a,*,*,*,*],[a,a,a,a,a],[a,a,a,*,a]]).
view(down,  object19, 5, 5, [[a,a,a,a,a],[b,b,b,b,b],[a,a,a,a,a],[a,a,a,a,a],[a,a,a,a,a]]).

% ---------- PAT_114 (rectangular) ----------
view(front, object20, 3, 7, [[a,a,a,a,*,*,*],[a,a,a,a,a,a,a],[a,a,*,*,*,a,a]]).
view(right, object20, 3, 6, [[d,d,*,*,d,d],[a,a,a,a,a,a],[a,a,a,a,a,a]]).
view(up,    object20, 6, 7, [[a,a,a,a,b,b,b],[a,a,a,a,b,b,b],[b,b,b,b,b,b,b],[b,b,b,b,b,b,b],[a,a,a,a,b,b,b],[a,a,a,a,b,b,b]]).
view(back,  object20, 3, 7, [[*,*,*,a,a,a,a],[a,a,a,a,a,a,a],[a,a,*,*,*,a,a]]).
view(left,  object20, 3, 6, [[a,a,*,*,a,a],[a,a,a,a,a,a],[a,a,a,a,a,a]]).
view(down,  object20, 6, 7, [[a,a,b,b,b,a,a],[a,a,b,b,b,a,a],[a,a,b,b,b,a,a],[a,a,b,b,b,a,a],[a,a,b,b,b,a,a],[a,a,b,b,b,a,a]]).

% ---------- PAT_200 ----------
view(front, object21, 1, 4, [[a,a,a,a]]).
view(right, object21, 1, 4, [[a,a,a,a]]).
view(up,    object21, 4, 4, [[a,a,a,a],[a,*,*,a],[a,*,*,a],[a,a,a,a]]).
view(back,  object21, 1, 4, [[a,a,a,a]]).
view(left,  object21, 1, 4, [[a,a,a,a]]).
view(down,  object21, 4, 4, [[a,a,a,a],[a,*,*,a],[a,*,*,a],[a,a,a,a]]).

% ---------- PAT_220 ----------
view(front, object22, 5, 7, [[*,*,a,a,a,*,*],[*,*,a,a,a,*,*],[a,a,a,a,a,a,a],[a,a,a,a,a,a,a],[a,*,*,*,*,*,a]]).
view(right, object22, 5, 4, [[c,c,c,c],[c,c,c,c],[a,a,a,a],[a,a,a,a],[a,a,a,a]]).
view(up,    object22, 4, 7, [[c,c,a,a,a,c,c],[c,c,a,a,a,c,c],[c,c,a,a,a,c,c],[c,c,a,a,a,c,c]]).
view(back,  object22, 5, 7, [[*,*,a,a,a,*,*],[*,*,a,a,a,*,*],[a,a,a,a,a,a,a],[a,a,a,a,a,a,a],[a,*,*,*,*,*,a]]).
view(left,  object22, 5, 4, [[c,c,c,c],[c,c,c,c],[a,a,a,a],[a,a,a,a],[a,a,a,a]]).
view(down,  object22, 4, 7, [[a,b,b,b,b,b,a],[a,b,b,b,b,b,a],[a,b,b,b,b,b,a],[a,b,b,b,b,b,a]]).

% ---------- PAT_221 ----------
view(front, object23, 4, 7, [[b,b,b,b,b,b,*],[b,a,a,a,a,a,a],[b,a,a,a,a,a,a],[b,a,a,a,a,a,a]]).
view(right, object23, 4, 4, [[*,b,b,b],[a,b,b,b],[a,b,b,b],[a,b,b,b]]).
view(up,    object23, 4, 7, [[a,a,a,a,a,a,*],[a,a,a,a,a,a,*],[a,a,a,a,a,a,*],[*,b,b,b,b,b,b]]).
view(back,  object23, 4, 7, [[*,a,a,a,a,a,a],[d,a,a,a,a,a,a],[d,a,a,a,a,a,a],[d,a,a,a,a,a,a]]).
view(left,  object23, 4, 4, [[a,a,a,*],[a,a,a,b],[a,a,a,b],[a,a,a,b]]).
view(down,  object23, 4, 7, [[*,a,a,a,a,a,a],[a,a,a,a,a,a,*],[a,a,a,a,a,a,*],[a,a,a,a,a,a,*]]).

% ---------- PAT_689 ----------
view(front, object24, 2, 6, [[a,a,b,b,a,a],[a,a,b,b,a,a]]).
view(right, object24, 2, 3, [[a,a,c],[a,a,c]]).
view(up,    object24, 3, 6, [[*,*,a,a,*,*],[a,a,a,a,a,a],[a,a,*,*,a,a]]).
view(back,  object24, 2, 6, [[b,b,a,a,b,b],[b,b,a,a,b,b]]).
view(left,  object24, 2, 3, [[c,a,a],[c,a,a]]).
view(down,  object24, 3, 6, [[a,a,*,*,a,a],[a,a,a,a,a,a],[*,*,a,a,*,*]]).

/* =========================================================
   2) Basic shape & symbol correctness
   --------------------------------------------------------- */

valid_cell(*)  :- !.
valid_cell('_') :- !.
valid_cell(Cell) :- atom(Cell), atom_length(Cell,1), char_type(Cell, lower).

matrix_dims(Matrix, Rows, Cols) :-
    is_list(Matrix),
    length(Matrix, Rows),
    ( Rows =:= 0 -> Cols = 0
    ; Matrix = [R|_], is_list(R), length(R, Cols), Cols >= 0, maplist(same_length(R), Matrix)
    ).

matrix_valid(Matrix) :- maplist(maplist(valid_cell), Matrix).

check_view_fact(view(Face, Obj, R, C, M)) :-
    ( matrix_dims(M, R0, C0) -> true
    ; format('ERROR ~w/~w: matrix not rectangular.~n', [Obj, Face]), fail ),
    ( R0=:=R, C0=:=C -> true
    ; format('ERROR ~w/~w: declared (~w por ~w) vs actual (~w por ~w).~n', [Obj, Face, R, C, R0, C0]), fail ),
    ( matrix_valid(M) -> true
    ; format('ERROR ~w/~w: invalid symbols (must be a..z or * or _).~n', [Obj, Face]), fail ),
    format('OK    ~w/~w: (~w por ~w) valid.~n', [Obj, Face, R, C]).

check_all_views :- forall(view(F, O, R, C, M), check_view_fact(view(F,O,R,C,M))).


/* =========================================================
   3) Object completeness
   --------------------------------------------------------- */

required_faces([front, right, up, back, left, down]).

object_faces(Obj, FacesSorted) :-
    setof(F, R^C^M^view(F, Obj, R, C, M), Faces), sort(Faces, FacesSorted), !.
object_faces(_, []).

list_objects_missing_faces :-
    setof(Obj, F^R^C^M^view(F, Obj, R, C, M), Objs),
    required_faces(Req),
    forall(member(O, Objs),
      ( object_faces(O, Faces),
        sort(Req, ReqS),
        ( Faces == ReqS -> true
        ; ord_subtract(ReqS, Faces, Missing),
          format('MISSING ~w: ~w~n', [O, Missing])
        )
      )).


/* =========================================================
   4) Helpers
   --------------------------------------------------------- */

depth_index0(L, I0) :- atom(L), atom_length(L,1), atom_codes(L,[C]), I0 is C - 97, I0 >= 0.

mirrored_index(K, Width, M) :-
    M is Width - 1 - K,
    M >= 0, M < Width.

col_top_down(Matrix, ColIdx, Col) :- transpose(Matrix, T), nth0(ColIdx, T, Col).
col_bottom_up(Matrix, ColIdx, ColBU) :- col_top_down(Matrix, ColIdx, ColTD), reverse(ColTD, ColBU).

row_underscores(N, Row) :- integer(N), N >= 0, length(Row, N), maplist(=('_'), Row).
row_stars(N, Row)       :- integer(N), N >= 0, length(Row, N), maplist(=('*'), Row).

blank_matrix(Rows, Cols, Mat) :-
    integer(Rows), integer(Cols), Rows >= 0, Cols >= 0,
    length(Mat, Rows),
    maplist({Cols}/[Row]>>row_underscores(Cols, Row), Mat).

set_nth0(In, I, Val, Out) :-
    same_length(In, Out),
    nth0(I, Out, Val, RestOut),
    nth0(I, In, _, RestOut).

safe_set_cell(MatIn, R, C, Val, MatOut) :-
    matrix_dims(MatIn, Rows, Cols),
    ( integer(R), integer(C), R >= 0, C >= 0, R < Rows, C < Cols ->
        nth0(R, MatIn, Row0, RestRows),
        set_nth0(Row0, C, Val, Row1),
        nth0(R, MatOut, Row1, RestRows)
    ; MatOut = MatIn
    ).

print_matrix([]).
print_matrix([Row|Rs]) :- format('  ~w~n', [Row]), print_matrix(Rs).

merge_cell('*',  _,   '*') :- !.
merge_cell(_,   '*',  '*') :- !.
merge_cell('a', '_',  'a') :- !.
merge_cell('_', 'a',  'a') :- !.
merge_cell('_', '_',  '_') :- !.
merge_cell(X,   _,    X)   :- !.

merge_rows([], [], []).
merge_rows([A|As], [B|Bs], [C|Cs]) :- merge_cell(A,B,C), merge_rows(As,Bs,Cs).
merge_mats([], [], []).
merge_mats([Ra|As], [Rb|Bs], [Rc|Cs]) :- merge_rows(Ra,Rb,Rc), merge_mats(As,Bs,Cs).
merge_many([M], M).
merge_many([A,B|Rest], Out) :- merge_mats(A,B,AB), merge_many([AB|Rest], Out).

include_nonempty(List, Out) :- exclude(=([]), List, Out).

normalize_to(TargetRows, TargetCols, In, Out) :-
    integer(TargetRows), integer(TargetCols),
    TargetRows >= 0, TargetCols >= 0,
    (   In = [] -> blank_matrix(TargetRows, TargetCols, Out)
    ;   length(In, InRows),
        ( InRows >= TargetRows
        -> length(Prefix, TargetRows), append(Prefix, _, In), Mid = Prefix
        ;  RPad is TargetRows - InRows,
           length(PadRows, RPad), maplist({TargetCols}/[R]>>row_underscores(TargetCols, R), PadRows),
           append(In, PadRows, Mid0),
           Mid = Mid0
        ),
        maplist(pad_or_crop_row(TargetCols), Mid, Out)
    ).

pad_or_crop_row(TargetCols, RowIn, RowOut) :-
    length(RowIn, InCols),
    ( InCols >= TargetCols
    -> length(Head, TargetCols), append(Head, _, RowIn), RowOut = Head
    ;  CPad is TargetCols - InCols, length(US, CPad), maplist(=('_'), US), append(RowIn, US, RowOut)
    ).

target_dims(Obj, back, Rows, Cols) :-  view(front, Obj, Rows, Cols, _).
target_dims(Obj, left, Rows, Cols) :-  view(right, Obj, Rows, Cols, _).
target_dims(Obj, down, Rows, Cols) :-  view(up,    Obj, Rows, Cols, _).

normalize_all_to(_R,_C, [], []).
normalize_all_to(R,C, [M|Ms], [MN|MNs]) :- normalize_to(R,C,M,MN), normalize_all_to(R,C,Ms,MNs).


/* =========================================================
   4.1) Axis-aware depths for rectangles
   --------------------------------------------------------- */
   
obj_depth_lr(Obj, D) :-
    ( view(front, Obj, _, CF, _) -> D = CF
    ; view(back,  Obj, _, CB, _) -> D = CB
    ; view(up,    Obj, _, CU, _) -> D = CU
    ; view(down,  Obj, _, CD, _) -> D = CD
    ; D = 0 ).

obj_depth_ud(Obj, D) :-
    ( view(up,    Obj, RU, _, _) -> D = RU
    ; view(down,  Obj, RD, _, _) -> D = RD
    ; view(right, Obj, _, CR, _) -> D = CR
    ; view(left,  Obj, _, CL, _) -> D = CL
    ; D = 0 ).

obj_deepest_letter_lr(Obj, Deep) :-
    obj_depth_lr(Obj, D),
    ( D =:= 0 -> Deep = '_'
    ; I0 is D - 1, Code is 97 + I0, char_code(Deep, Code) ).

obj_deepest_letter_ud(Obj, Deep) :-
    obj_depth_ud(Obj, D),
    ( D =:= 0 -> Deep = '_'
    ; I0 is D - 1, Code is 97 + I0, char_code(Deep, Code) ).


/* =========================================================
   5) FR/RF/FU/UF/RU/UR (consistency)
   ========================================================= */

fr_row_ok(FRow, RRow, LastColIdx) :-
    nth0(LastColIdx, FRow, Cell), !,
    (   Cell == * ->
        ( \+ member(a, RRow) -> true
        ;  format('VIOLATION FR: Front[*] but Right row contains "a": ~w~n', [RRow]), fail )
    ;   depth_index0(Cell, K),
        ( nth0(K, RRow, a) -> true
        ;  format('VIOLATION FR: Front[~w] expects Right[~d]="a" but Right row is ~w~n', [Cell, K, RRow]), fail )
    ).

fr_consistent_matrices(Front, Right) :-
    length(Front, RF), length(Right, RR),
    ( RF =:= RR -> true
    ; format('ERROR FR: Different row counts (Front=~w, Right=~w).~n', [RF, RR]), fail ),
    ( matrix_dims(Front, _R1, CF), CF > 0 -> true
    ; format('ERROR FR: Front has no columns or is non-rectangular.~n'), fail ),
    ( matrix_dims(Right, _R2, _C2) -> true
    ; format('ERROR FR: Right is non-rectangular.~n'), fail ),
    LastColIdx is CF - 1,
    EndR is RF - 1,
    numlist(0, EndR, Is),
    forall(member(I, Is),
      ( nth0(I, Front, FRow),
        nth0(I, Right, RRow),
        fr_row_ok(FRow, RRow, LastColIdx)
      )),
    format('FR OK: all ~w rows consistent (Front last-col - Right row).~n', [RF]).

fr_consistent_object(Obj) :-
    view(front, Obj, _RF, _CF, FMat),
    view(right, Obj, _RR, _CR, RMat),
    format('--- Checking FR (Front-Right) for ~w ---~n', [Obj]),
    (fr_consistent_matrices(FMat, RMat) -> true ; fail).

fr_consistent_all :-
    setof(O, (view(front,O,_,_,_), view(right,O,_,_,_)), Objs),
    forall(member(Obj, Objs), fr_consistent_object(Obj)).

rf_row_ok(RRow, FRow) :-
    nth0(0, RRow, Cell), !,
    (   Cell == * ->
        ( \+ member(a, FRow) -> true
        ;  format('VIOLATION RF: Right[*] but Front row contains "a": ~w~n', [FRow]), fail )
    ;   depth_index0(Cell, K),
        length(FRow, CF),
        mirrored_index(K, CF, MF),
        ( nth0(MF, FRow, a) -> true
        ;  format('VIOLATION RF: Right[~w] depth ~w - Front index ~w expects "a", but Front row is ~w~n',
                  [Cell, K, MF, FRow]), fail )
    ).

rf_consistent_matrices(Right, Front) :-
    length(Right, RR), length(Front, RF),
    ( RR =:= RF -> true
    ; format('ERROR RF: Different row counts (Right=~w, Front=~w).~n', [RR, RF]), fail ),
    ( matrix_dims(Right, _R1, CR), CR > 0 -> true
    ; format('ERROR RF: Right has no columns or is non-rectangular.~n'), fail ),
    ( matrix_dims(Front, _R2, _C2) -> true
    ; format('ERROR RF: Front is non-rectangular.~n'), fail ),
    EndRR is RR - 1,
    numlist(0, EndRR, Is),
    forall(member(I, Is),
      ( nth0(I, Right, RRow),
        nth0(I, Front, FRow),
        rf_row_ok(RRow, FRow)
      )),
    format('RF OK: all ~w rows consistent (Right first-col - Front row, mirrored).~n', [RR]).

rf_consistent_object(Obj) :-
    view(right, Obj, _RR, _CR, RMat),
    view(front, Obj, _RF, _CF, FMat),
    format('--- Checking RF (Right-Front, mirrored) for ~w ---~n', [Obj]),
    (rf_consistent_matrices(RMat, FMat) -> true ; fail).

rf_consistent_all :-
    setof(O, (view(right,O,_,_,_), view(front,O,_,_,_)), Objs),
    forall(member(Obj, Objs), rf_consistent_object(Obj)).

fr_rf_bidir_consistent_object(Obj) :-
    format('=== Bidirectional FR/RF for ~w ===~n', [Obj]),
    fr_consistent_object(Obj),
    rf_consistent_object(Obj),
    format('FR & RF OK: ~w is bidirectionally consistent.~n', [Obj]).

fr_rf_bidir_all :-
    setof(O, (view(front,O,_,_,_), view(right,O,_,_,_)), Objs),
    forall(member(Obj, Objs), fr_rf_bidir_consistent_object(Obj)).

fu_pos_ok(Cell, UpColBU) :-
    (   Cell == * ->
        ( \+ member(a, UpColBU) -> true
        ;  format('VIOLATION FU: Front[*] but Up column (bottom-up) contains "a": ~w~n', [UpColBU]), fail )
    ;   depth_index0(Cell, K),
        ( nth0(K, UpColBU, a) -> true
        ;  format('VIOLATION FU: Front[~w] expects UpColBU[~d]="a" but column is ~w~n', [Cell, K, UpColBU]), fail )
    ).

fu_consistent_matrices(Front, Up) :-
    ( matrix_dims(Front, RF, CF), RF > 0, CF > 0 -> true
    ; format('ERROR FU: Front has no rows/cols or is non-rectangular.~n'), fail ),
    ( matrix_dims(Up, RU, CU), RU > 0, CU =:= CF -> true
    ; format('ERROR FU: Up must be rectangular and have same number of columns as Front (CF).~n'), fail ),
    nth0(0, Front, FTop),
    EndC is CF - 1,
    numlist(0, EndC, Js),
    forall(member(J, Js),
      ( nth0(J, FTop, Cell),
        col_bottom_up(Up, J, UpColBU),
        fu_pos_ok(Cell, UpColBU)
      )),
    format('FU OK: all ~w columns consistent (Front top-row - Up columns bottom-up).~n', [CF]).

fu_consistent_object(Obj) :-
    view(front, Obj, _RF, _CF, FMat),
    view(up,    Obj, _RU, _CU, UMat),
    format('--- Checking FU (Front-Up) for ~w ---~n', [Obj]),
    (fu_consistent_matrices(FMat, UMat) -> true ; fail).

fu_consistent_all :-
    setof(O, (view(front,O,_,_,_), view(up,O,_,_,_)), Objs),
    forall(member(Obj, Objs), fu_consistent_object(Obj)).

uf_pos_ok(Cell, FrontColTD) :-
    (   Cell == * ->
        ( \+ member(a, FrontColTD) -> true
        ;  format('VIOLATION UF: Up[*] but Front column (top-down) contains "a": ~w~n', [FrontColTD]), fail )
    ;   depth_index0(Cell, K),
        ( nth0(K, FrontColTD, a) -> true
        ;  format('VIOLATION UF: Up[~w] expects FrontColTD[~d]="a" but column is ~w~n', [Cell, K, FrontColTD]), fail )
    ).

uf_consistent_matrices(Up, Front) :-
    ( matrix_dims(Up, RU, CU), RU > 0, CU > 0 -> true
    ; format('ERROR UF: Up has no rows/cols or is non-rectangular.~n'), fail ),
    ( matrix_dims(Front, RF, CF), RF > 0, CF =:= CU -> true
    ; format('ERROR UF: Front must be rectangular and have same number of columns as Up (CU).~n'), fail ),
    LastU is RU - 1,
    nth0(LastU, Up, UBottom),
    EndCU is CU - 1,
    numlist(0, EndCU, Js),
    forall(member(J, Js),
      ( nth0(J, UBottom, Cell),
        col_top_down(Front, J, FrontColTD),
        uf_pos_ok(Cell, FrontColTD)
      )),
    format('UF OK: all ~w columns consistent (Up bottom-row - Front columns top-down).~n', [CU]).

uf_consistent_object(Obj) :-
    view(up,    Obj, _RU, _CU, UMat),
    view(front, Obj, _RF, _CF, FMat),
    format('--- Checking UF (Up-Front) for ~w ---~n', [Obj]),
    (uf_consistent_matrices(UMat, FMat) -> true ; fail).

uf_consistent_all :-
    setof(O, (view(up,O,_,_,_), view(front,O,_,_,_)), Objs),
    forall(member(Obj, Objs), uf_consistent_object(Obj)).

fu_uf_bidir_consistent_object(Obj) :-
    format('=== Bidirectional FU/UF for ~w ===~n', [Obj]),
    fu_consistent_object(Obj),
    uf_consistent_object(Obj),
    format('FU & UF OK: ~w is bidirectionally consistent.~n', [Obj]).

ru_pos_ok(Cell, UpRowMirrored) :-
    (   Cell == * ->
        ( \+ member(a, UpRowMirrored) -> true
        ;  format('VIOLATION RU: Right[*] but mirrored Up row contains "a": ~w~n', [UpRowMirrored]), fail )
    ;   depth_index0(Cell, K),
        nth0(K, UpRowMirrored, a)
    ).

ru_consistent_matrices(Right, Up) :-
    ( matrix_dims(Up, URows, _UCols), URows > 0 -> true
    ; format('ERROR RU: Up has no rows or is non-rectangular.~n'), fail ),
    Right = [RightTopRow|_],
    length(RightTopRow, LenRTop),
    LastU is URows - 1,
    MaxI is min(LenRTop - 1, LastU),
    ( MaxI >= 0 -> true ; format('ERROR RU: No overlapping indices to compare.~n'), fail ),
    numlist(0, MaxI, Is),
    forall(member(I, Is),
      ( nth0(I, RightTopRow, Cell),
        URowIndex is LastU - I,
        nth0(URowIndex, Up, URow),
        reverse(URow, URowMir),
        ru_pos_ok(Cell, URowMir)
      )),
    format('RU OK: alignment success (overlap 0..~w).~n', [MaxI]).

ru_consistent_object(Obj) :-
    view(right, Obj, _RR, _CR, RMat),
    view(up,    Obj, _RU, _CU, UMat),
    format('--- Checking RU (Right-Up) for ~w ---~n', [Obj]),
    (ru_consistent_matrices(RMat, UMat) -> true ; fail).

ru_consistent_all :-
    setof(O, (view(right,O,_,_,_), view(up,O,_,_,_)), Objs),
    forall(member(Obj, Objs), ru_consistent_object(Obj)).

ur_pos_sat(Cell, RightColTD) :-
    (   Cell == * -> \+ member(a, RightColTD)
    ;   depth_index0(Cell, K),
        nth0(K, RightColTD, a)
    ).

ur_consistent_matrices(Up, Right) :-
    ( matrix_dims(Up, URows, UCols), URows > 0, UCols > 0 -> true
    ; format('ERROR UR: Up has no rows/cols or is non-rectangular.~n'), fail ),
    ( matrix_dims(Right, _RRows, RCols), RCols > 0 -> true
    ; format('ERROR UR: Right has no columns or is non-rectangular.~n'), fail ),
    ( RCols =:= URows -> true
    ; format('ERROR UR: Right.cols (=~w) must equal Up.rows (=~w).~n', [RCols, URows]), fail ),
    LastRowU is URows - 1,
    LastColU is UCols - 1,
    numlist(0, LastRowU, Is),
    forall(member(I, Is),
      ( nth0(I, Up, URow),
        nth0(LastColU, URow, Cell),
        Depth is LastRowU - I,
        col_top_down(Right, Depth, RightColTD),
        ur_pos_sat(Cell, RightColTD)
      )),
    format('UR OK: checked all ~w rows (Up rightmost-col - Right depth columns).~n', [URows]).

ur_consistent_object(Obj) :-
    view(up,    Obj, _RU, _CU, UMat),
    view(right, Obj, _RR, _CR, RMat),
    format('--- Checking UR (Up-Right) for ~w ---~n', [Obj]),
    (ur_consistent_matrices(UMat, RMat) -> true ; fail).

ur_consistent_all :-
    setof(O, (view(up,O,_,_,_), view(right,O,_,_,_)), Objs),
    forall(member(Obj, Objs), ur_consistent_object(Obj)).

ru_ur_bidir_consistent_object(Obj) :-
    format('=== Bidirectional RU/UR for ~w ===~n', [Obj]),
    ru_consistent_object(Obj),
    ur_consistent_object(Obj),
    format('RU & UR OK: ~w is bidirectionally consistent.~n', [Obj]).

ru_ur_bidir_all :-
    setof(O, (view(right,O,_,_,_), view(up,O,_,_,_)), Objs),
    forall(member(Obj, Objs), ru_ur_bidir_consistent_object(Obj)).


/* =========================================================
   6) Depth-relativity (FB, RL, UD) using axis-aware deepest
   (INSTRUMENTED)
   --------------------------------------------------------- */

% ---- Front -> Back depth marks, with logging
fb_infer_row(Obj, RowIdx, FRow, N, Deep, BRow) :-
    row_underscores(N, Base),
    End is N - 1, numlist(0, End, Js),
    foldl(
      {Obj,RowIdx,FRow,N,Deep}/[J,AccIn,AccOut]>>(
         nth0(J, FRow, Cell),
         ( Cell == Deep
         -> mirrored_index(J, N, M),
            set_nth0(AccIn, M, a, AccOut),
            log_write(Obj, back, RowIdx, M, 'FB_DEPTH', a)
         ;  AccOut = AccIn
         )
      ),
      Js, Base, BRow).

% Front -> Back
fb_enforce_obj(Obj, Front, _Back0, BackOut) :-
    ( Front = [FTop|_] -> length(FTop, Cols) ; Cols = 0 ),
    ( Cols =:= 0 -> BackOut = []
    ; obj_deepest_letter_lr(Obj, Deep),
      length(Front, Rows), EndR is Rows - 1, numlist(0, EndR, Is),
      maplist({Obj,Front,Cols,Deep}/[I,BRow]>>(
          nth0(I, Front, FRow),
          fb_infer_row(Obj, I, FRow, Cols, Deep, BRow)
      ), Is, BackOut)
    ).

% ---- Right -> Left depth marks, with logging
rl_infer_row(Obj, RowIdx, RRow, N, Deep, LRow) :-
    row_underscores(N, Base),
    End is N - 1, numlist(0, End, Js),
    foldl(
      {Obj,RowIdx,RRow,N,Deep}/[J,AccIn,AccOut]>>(
         nth0(J, RRow, Cell),
         ( Cell == Deep
         -> mirrored_index(J, N, M),
            set_nth0(AccIn, M, a, AccOut),
            log_write(Obj, left, RowIdx, M, 'RL_DEPTH', a)
         ;  AccOut = AccIn
         )
      ),
      Js, Base, LRow).

% Right -> Left
rl_enforce_obj(Obj, Right, _Left0, LeftOut) :-
    ( Right = [RTop|_] -> length(RTop, Cols) ; Cols = 0 ),
    ( Cols =:= 0 -> LeftOut = []
    ; obj_deepest_letter_lr(Obj, Deep),
      length(Right, Rows), EndR is Rows - 1, numlist(0, EndR, Is),
      maplist({Obj,Right,Cols,Deep}/[I,LRow]>>(
          nth0(I, Right, RRow),
          rl_infer_row(Obj, I, RRow, Cols, Deep, LRow)
      ), Is, LeftOut)
    ).

% ---- Up -> Down depth marks, with logging
ud_marks_from_up_row(Obj, UpRowIdx, Rows, Cols, UpRow, Deep, MarkRow) :-
    row_underscores(Cols, Base),
    EndC is Cols - 1, numlist(0, EndC, Js),
    DownRowIdx is Rows - 1 - UpRowIdx,
    foldl(
      {Obj,DownRowIdx,UpRow,Deep}/[J,AccIn,AccOut]>>(
         nth0(J, UpRow, Cell),
         ( Cell == Deep
         -> set_nth0(AccIn, J, a, AccOut),
            log_write(Obj, down, DownRowIdx, J, 'UD_DEPTH', a)
         ;  AccOut = AccIn
         )
      ),
      Js, Base, MarkRow).

% Up -> Down
ud_enforce_obj(Obj, Up, _Down0, DownOut) :-
    ( matrix_dims(Up, Rows, Cols) -> true ; Rows = 0, Cols = 0 ),
    ( Rows =:= 0 -> DownOut = []
    ; obj_deepest_letter_ud(Obj, Deep),
      EndR is Rows - 1, numlist(0, EndR, Is),
      maplist({Obj,Up,Rows,Cols,Deep}/[I,MRow]>>(
          nth0(I, Up, URow),
          ud_marks_from_up_row(Obj, I, Rows, Cols, URow, Deep, MRow)
      ), Is, Marks),
      % Marks were written already with DownRowIdx, so we can just reverse:
      reverse(Marks, DownOut)
    ).


/* =========================================================
   7) Hole Continuity (Front→Back | Right→Left | Up→Down)
   (INSTRUMENTED)
   --------------------------------------------------------- */

fb_holes_row(Obj, RowIdx, FRow, N, BRow) :-
    row_underscores(N, Base),
    End is N - 1, numlist(0, End, Js),
    foldl(
      {Obj,RowIdx,FRow,N}/[J,AccIn,AccOut]>>(
         nth0(J, FRow, Cell),
         ( Cell == *
         -> mirrored_index(J, N, M),
            set_nth0(AccIn, M, *, AccOut),
            log_write(Obj, back, RowIdx, M, 'FB_HOLES', *)
         ;  AccOut = AccIn
         )
      ),
      Js, Base, BRow).

fb_holes_enforce(Obj, Front, _Back0, BackOut) :-
    ( Front = [FTop|_] -> length(FTop, Cols) ; Cols = 0 ),
    ( Cols =:= 0 -> BackOut = []
    ; length(Front, Rows), EndR is Rows - 1, numlist(0, EndR, Is),
      maplist({Obj,Front,Cols}/[I,BRow]>>(
          nth0(I, Front, FRow),
          fb_holes_row(Obj, I, FRow, Cols, BRow)
      ), Is, BackOut)
    ).

rl_holes_row(Obj, RowIdx, RRow, N, LRow) :-
    row_underscores(N, Base),
    End is N - 1, numlist(0, End, Js),
    foldl(
      {Obj,RowIdx,RRow,N}/[J,AccIn,AccOut]>>(
         nth0(J, RRow, Cell),
         ( Cell == *
         -> mirrored_index(J, N, M),
            set_nth0(AccIn, M, *, AccOut),
            log_write(Obj, left, RowIdx, M, 'RL_HOLES', *)
         ;  AccOut = AccIn
         )
      ),
      Js, Base, LRow).

rl_holes_enforce(Obj, Right, _Left0, LeftOut) :-
    ( Right = [RTop|_] -> length(RTop, Cols) ; Cols = 0 ),
    ( Cols =:= 0 -> LeftOut = []
    ; length(Right, Rows), EndR is Rows - 1, numlist(0, EndR, Is),
      maplist({Obj,Right,Cols}/[I,LRow]>>(
          nth0(I, Right, RRow),
          rl_holes_row(Obj, I, RRow, Cols, LRow)
      ), Is, LeftOut)
    ).

ud_holes_marks_from_up_row(Obj, UpRowIdx, Rows, Cols, UpRow, MarkRow) :-
    row_underscores(Cols, Base),
    EndC is Cols - 1, numlist(0, EndC, Js),
    DownRowIdx is Rows - 1 - UpRowIdx,
    foldl(
      {Obj,DownRowIdx,UpRow}/[J,AccIn,AccOut]>>(
         nth0(J, UpRow, Cell),
         ( Cell == *
         -> set_nth0(AccIn, J, *, AccOut),
            log_write(Obj, down, DownRowIdx, J, 'UD_HOLES', *)
         ;  AccOut = AccIn
         )
      ),
      Js, Base, MarkRow).

ud_holes_enforce(Obj, Up, _Down0, DownOut) :-
    ( matrix_dims(Up, Rows, Cols) -> true ; Rows = 0, Cols = 0 ),
    ( Rows =:= 0 -> DownOut = []
    ; EndR is Rows - 1, numlist(0, EndR, Is),
      maplist({Obj,Up,Rows,Cols}/[I,MRow]>>(
          nth0(I, Up, URow),
          ud_holes_marks_from_up_row(Obj, I, Rows, Cols, URow, MRow)
      ), Is, Marks),
      reverse(Marks, DownOut)
    ).


/* =========================================================
   8) Extra inferences (unified)
      - Right→Back depth (last col)
      - Up→Back depth (top row)
      - Up→Left depth (leftmost col)
      - Right→Down depth
      - Front→Down depth
   --------------------------------------------------------- */

% Right → Back (depth): If Right[I][Last] has depth K, Back[I][K] = 'a'
inference_right_back(Obj, Right, BackOut) :-
    ( Right = [RTop|_] -> length(RTop, N) ; N=0 ),
    ( N =:= 0 -> BackOut = []
    ; length(Right, Rows), EndR is Rows - 1, numlist(0, EndR, Is),
      maplist({Obj,Right,N}/[I,BRow]>>(
          nth0(I, Right, RRow),
          rb_row(Obj, I, N, RRow, BRow)
      ), Is, BackOut)
    ).

rb_row(Obj, RowIdx, N, RRow, BRow) :-
    row_underscores(N, Base),
    Last is N-1,
    nth0(Last, RRow, Cell),
    ( depth_index0(Cell, K)
    -> set_nth0(Base, K, a, BRow),
       log_write(Obj, back, RowIdx, K, 'RB_DEPTH', a)
    ;  BRow = Base ).

% Up → Back (depth): If Up[0][J] has depth K, Back[K][mirror(J)] = 'a'
inference_up_back(Obj, Up, BackOut) :-
    ( matrix_dims(Up, Rows, Cols) -> true ; Rows=0, Cols=0 ),
    ( Rows=:=0 ; Cols=:=0 -> BackOut = []
    ; TopRowIdx = 0,
      nth0(TopRowIdx, Up, TopRow),
      blank_matrix(Rows, Cols, Back0),
      EndC is Cols-1, numlist(0, EndC, Js),
      foldl({Obj,TopRow,Cols}/[J,AccIn,AccOut]>>(
         nth0(J, TopRow, Cell),
         ( depth_index0(Cell, K),
           mirrored_index(J, Cols, MJ),
           nth0(K, AccIn, RowK, Rest),
           set_nth0(RowK, MJ, a, NewRowK),
           nth0(K, AccOut, NewRowK, Rest),
           log_write(Obj, back, K, MJ, 'UB_DEPTH', a)
         ; AccOut = AccIn
         )
      ), Js, Back0, BackOut)
    ).

% Up → Left (depth): If Up[I][0] has depth K, Left[K][I] = 'a'
inference_left_up(Obj, Up, LeftOut) :-
    ( matrix_dims(Up, Rows, Cols) -> true ; Rows=0, Cols=0 ),
    ( Rows=:=0 ; Cols=:=0 -> LeftOut = []
    ;
      blank_matrix(Rows, Cols, L0),
      EndR is Rows-1, numlist(0, EndR, Is),
      foldl({Obj,Up}/[I,AccIn,AccOut]>>(
          nth0(I, Up, URow),
          nth0(0, URow, Cell),
          ( depth_index0(Cell, K) ->
              nth0(K, AccIn, RowK, Rest),
              set_nth0(RowK, I, a, NewRowK),
              nth0(K, AccOut, NewRowK, Rest),
              log_write(Obj, left, K, I, 'LU_DEPTH', a)
          ; AccOut = AccIn
          )
      ), Is, L0, LeftOut)
    ).

% Down ← Right (depth): If Right[Last][J] has depth K, Down[J][Cols-1-K] = 'a'
inference_down_right(Obj, Right, Up, DownOut) :-
    ( matrix_dims(Up, RowsD, ColsD) -> true ; RowsD = 0, ColsD = 0 ),
    blank_matrix(RowsD, ColsD, D0),
    ( Right = [] -> DownOut = D0
    ; Right = [RTop|_], length(RTop, RCols),
      length(Right, RRows), LastRow is RRows - 1,
      ( LastRow < 0 -> DownOut = D0
      ; nth0(LastRow, Right, RLast),
        EndC is RCols - 1,
        ( EndC < 0 -> DownOut = D0
        ; numlist(0, EndC, Js),
          foldl({Obj,RLast,ColsD}/[J,Acc,Out]>>(
              nth0(J, RLast, Cell),
              ( depth_index0(Cell, K) ->
                  Col is ColsD - 1 - K,
                  Row is J,
                  safe_set_cell(Acc, Row, Col, a, Out),
                  log_write(Obj, down, Row, Col, 'DR_DEPTH', a)
              ; Out = Acc
              )
          ), Js, D0, DownOut)
        )
      )
    ).

% Down ← Front (depth): If Front[Last][J] has depth K, Down[K][J] = 'a'
inference_down_front(Obj, Front, Up, DownOut) :-
    ( matrix_dims(Up, RowsD, ColsD) -> true ; RowsD = 0, ColsD = 0 ),
    blank_matrix(RowsD, ColsD, D0),
    ( Front = [] -> DownOut = D0
    ; Front = [FRow|_], length(FRow, _FCols),
      length(Front, FRows), LastRow is FRows - 1,
      ( LastRow < 0 -> DownOut = D0
      ; nth0(LastRow, Front, FLast),
        EndC is ColsD - 1,
        ( EndC < 0 -> DownOut = D0
        ; numlist(0, EndC, Js),
          foldl({Obj,FLast}/[J,Acc,Out]>>(
              nth0(J, FLast, Cell),
              ( depth_index0(Cell, K) ->
                  Row is K,
                  Col is J,
                  safe_set_cell(Acc, Row, Col, a, Out),
                  log_write(Obj, down, Row, Col, 'DF_DEPTH', a)
              ; Out = Acc
              )
          ), Js, D0, DownOut)
        )
      )
    ).


/* =========================================================
   9) Save unified inferences per object
   --------------------------------------------------------- */

save_all_inferences :-
    findall(O, (view(front,O,_,_,_); view(right,O,_,_,_); view(up,O,_,_,_)), Os0),
    list_to_ord_set(Os0, AllObjs),
    forall(member(Obj, AllObjs), (
        % ---------- BACK: contributors ----------
        ( view(front, Obj, _, _, F) ->
              fb_enforce_obj(Obj, F, _, BackDepthFB),
              fb_holes_enforce(Obj, F, _, BackHolesFB)
        ; BackDepthFB=[], BackHolesFB=[] ),
        ( view(right, Obj, _, _, R) -> inference_right_back(Obj, R, BackDepthRB) ; BackDepthRB=[] ),
        ( view(up,    Obj, _, _, U) -> inference_up_back(Obj, U,   BackDepthUB) ; BackDepthUB=[] ),
        include_nonempty([BackDepthFB, BackDepthRB, BackDepthUB, BackHolesFB], BackContribs0),

        ( BackContribs0 = [] -> true
        ; target_dims(Obj, back, RB, CB),
          normalize_all_to(RB, CB, BackContribs0, BackContribs),
          merge_many(BackContribs, BackCombined),
          retractall(inferred_view(_, back, Obj, _, _, _)),
          assertz(inferred_view(combined, back, Obj, RB, CB, BackCombined)),
          format('~n[~w] SAVED combined/back:~n', [Obj]), print_matrix(BackCombined)
        ),

        % ---------- LEFT: contributors ----------
        ( view(right, Obj, _, _, R2) ->
              rl_enforce_obj(Obj, R2, _, LeftDepthRL),
              rl_holes_enforce(Obj, R2, _, LeftHolesRL)
        ; LeftDepthRL=[], LeftHolesRL=[] ),
        ( view(up,    Obj, _, _, U2) -> inference_left_up(Obj, U2, LeftDepthLU) ; LeftDepthLU=[] ),
        include_nonempty([LeftDepthRL, LeftDepthLU, LeftHolesRL], LeftContribs0),

        ( LeftContribs0 = [] -> true
        ; target_dims(Obj, left, RL, CL),
          normalize_all_to(RL, CL, LeftContribs0, LeftContribs),
          merge_many(LeftContribs, LeftCombined),
          retractall(inferred_view(_, left, Obj, _, _, _)),
          assertz(inferred_view(combined, left, Obj, RL, CL, LeftCombined)),
          format('~n[~w] SAVED combined/left:~n', [Obj]), print_matrix(LeftCombined)
        ),

        % ---------- DOWN: contributors ----------
        ( view(up, Obj, _, _, U3) ->
            ud_enforce_obj(Obj, U3, _, DownDepthUD),
            ud_holes_enforce(Obj, U3, _, DownHolesUD),
            ( view(right, Obj, _, _, R3) -> inference_down_right(Obj, R3, U3, DownDepthDR) ; DownDepthDR = [] ),
            ( view(front, Obj, _, _, F3) -> inference_down_front(Obj, F3, U3, DownDepthDF) ; DownDepthDF = [] ),
            include_nonempty([DownDepthUD, DownHolesUD, DownDepthDR, DownDepthDF], DownContribs0),

            ( DownContribs0 = [] -> true
            ; target_dims(Obj, down, RD, CD),
              normalize_all_to(RD, CD, DownContribs0, DownContribs),
              merge_many(DownContribs, DownCombined),
              retractall(inferred_view(_, down, Obj, _, _, _)),
              assertz(inferred_view(combined, down, Obj, RD, CD, DownCombined)),
              format('~n[~w] SAVED combined/down:~n', [Obj]), print_matrix(DownCombined)
            )
          ; true
        )
    )).


/* =========================================================
   10) Listing helpers
   --------------------------------------------------------- */

list_inferred_object(Obj) :-
    forall(member(Face,[back,left,down]),
      ( ( inferred_view(_, Face, Obj, _, _, Mat) ->
            format('~n[~w] combined/~w:~n', [Obj, Face]), print_matrix(Mat)
        ;   format('~n[~w] combined/~w: (none saved)~n', [Obj, Face])
        )
      )).

infer_all_save_and_list(Obj) :-
    clear_inferred,
    save_all_inferences,
    nl,
    list_inferred_object(Obj).


/* =========================================================
   11) CSV writer: RULES TRIGGERED PER CELL
   --------------------------------------------------------- */

cell_final_symbol(Values, Final) :-
    ( member(*, Values) -> Final = *
    ; member(a, Values) -> Final = a
    ; Final = '_' ).

write_rules_csv(File) :-
    setup_call_cleanup(
      open(File, write, S),
      (
        format(S, 'object,face,row,col,inferred_symbol,rules_triggered,rule_outputs,num_rules~n', []),
        ( setof((Obj,Face,R,C),
                Rule^Val^triggered_rule(Obj,Face,R,C,Rule,Val),
                Cells) -> true ; Cells = [] ),
        forall(member((Obj,Face,R,C), Cells),
          (
            findall(Rule, triggered_rule(Obj,Face,R,C,Rule,_), Rules),
            findall(Val,  triggered_rule(Obj,Face,R,C,_,Val),  Vals),
            cell_final_symbol(Vals, Final),
            atomic_list_concat(Rules, ';', RulesAtom),
            atomic_list_concat(Vals,  ';', ValsAtom),
            length(Rules, NRules),
            format(S, '~w,~w,~d,~d,~w,~w,~w,~d~n',
                   [Obj,Face,R,C,Final,RulesAtom,ValsAtom,NRules])
          )
        )
      ),
      close(S)
    ).

/* Convenience entry points */

infer_save_and_rules_csv(CsvFile) :-
    clear_inferred,
    clear_triggered_rules,
    save_all_inferences,
    write_rules_csv(CsvFile).

infer_save_list_and_rules_csv(Obj, CsvFile) :-
    clear_inferred,
    clear_triggered_rules,
    save_all_inferences,
    list_inferred_object(Obj),
    write_rules_csv(CsvFile).