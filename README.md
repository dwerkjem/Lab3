# Fountain View Hall

## Running Project

### Pre-run Install

#### Requirements

No GPUs, high-powered CPU, or even graphical interfaces are needed. It could be ran over SSH thanks to the lightweight TUI. 

- Python 3.13:
    - see [version](.python-version) and [requirements](requirements.txt)

- 200 MB of space

#### Using uv (recommended)

Follow the [uv install instructions](https://docs.astral.sh/uv/getting-started/installation/) and run:

```cmd
uv sync
````

#### Using pip

```cmd
py -m pip install -r requirements.txt
```

### Running After Install

#### Using uv (recommended)

```cmd
uv run main
```

#### Using Python

```cmd
py src/lab3/main.py
```
