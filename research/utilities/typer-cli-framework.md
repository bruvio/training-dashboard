# Typer CLI Framework

## Overview
- A Python library for building CLI applications
- Designed to be intuitive, easy to use, and based on Python type hints
- Created by the same developer as FastAPI

## Key Features
- Minimal code required to create CLI applications
- Automatic help and shell completion
- Uses Python type hints for defining CLI arguments and options
- Supports complex command structures with subcommands

## Installation
```
pip install typer
```

## Simple Usage Example
```python
import typer

def main(name: str):
    print(f"Hello {name}")

if __name__ == "__main__":
    typer.run(main)
```

## Advanced Example with Subcommands
```python
import typer

app = typer.Typer()

@app.command()
def hello(name: str):
    print(f"Hello {name}")

@app.command()
def goodbye(name: str, formal: bool = False):
    if formal:
        print(f"Goodbye Ms. {name}. Have a good day.")
    else:
        print(f"Bye {name}!")

if __name__ == "__main__":
    app()
```

## Key Benefits
- Automatic CLI argument parsing
- Built-in help generation
- Type-based validation
- Easy to create complex CLI applications
- Supports auto-completion for shells

## Dependencies
- Primarily relies on Click
- Optional dependencies include Rich and Shellingham
- Offers a `typer-slim` version with minimal dependencies

The framework emphasizes simplicity, leveraging Python's type system to create powerful and user-friendly command-line interfaces with minimal boilerplate code.