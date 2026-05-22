# QR2026

Cube-rotation and object-reasoning demos built with Python and SWI-Prolog.

## Requirements

- Python 3.10+
- SWI-Prolog
- Packages listed in `requirements.txt`

## Install

From the repo root:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Make sure `swipl` is available in your PATH.

## Run

Main demo:

```powershell
streamlit run interactive_demo.py
```

Rotation demo:

```powershell
streamlit run interactive_rotation.py
```

Results viewer:

```powershell
streamlit run interactive_result.py
```

## Dataset tools

Generate the dataset:

```powershell
python test_objects_qor\generate_shortest_path_dataset.py
```

Run the solver:

```powershell
python test_objects_qor\solve_shortest_path_dataset.py
```