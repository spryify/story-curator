# Coding Standards

## Table of Contents
- [Python Style Guidelines](#python-style-guidelines)
- [Naming Conventions](#naming-conventions)
- [Type Hints](#type-hints)
- [Documentation Standards](#documentation-standards)
- [Import Organization](#import-organization)
- [Error Handling Patterns](#error-handling-patterns)
- [Testing Standards](#testing-standards)
- [Security Guidelines](#security-guidelines)
- [Performance Standards](#performance-standards)
- [Tool Configuration](#tool-configuration)

## Python Style Guidelines

### General Principles
- **Readability over cleverness**: Code should be self-documenting
- **Explicit over implicit**: Make intentions clear
- **Consistency**: Follow established patterns throughout the codebase
- **Simplicity**: Prefer simple solutions over complex ones

### Code Formatting
We use **Black** with these settings:
```toml
[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'
extend-exclude = '''
/(
  # Exclude generated files
  migrations/
  | build/
  | dist/
)/
'''
```

### Line Length and Wrapping
- **Maximum line length**: 88 characters (Black default)
- **Function/method calls**: Break after opening parenthesis
- **Long strings**: Use implicit string concatenation or textwrap.dedent()


### Blank Lines
- **2 blank lines**: Between top-level classes and functions
- **1 blank line**: Between methods in a class
- **1 blank line**: To separate logical sections within functions (sparingly)


## Naming Conventions

### Variables and Functions
- **snake_case** for variables, functions, and methods
- **Descriptive names** over abbreviated ones
- **Verbs for functions**, **nouns for variables**



### Classes and Exceptions
- **PascalCase** for class names
- **Descriptive, specific names**
- **Exception suffix** for exception classes


### Constants
- **UPPER_SNAKE_CASE** for constants
- **Module-level placement** preferred


### Private Members
- **Single leading underscore** for internal use
- **Double leading underscore** for name mangling (rare cases)


### File and Directory Names
- **snake_case** for Python files
- **lowercase** for directories
- **Descriptive names** that indicate purpose


## Type Hints

### Required Type Hints
- **All function signatures** must have type hints
- **Class attributes** should be type hinted
- **Return types** must be specified (use `-> None` for procedures)


### Union Types and Optional
- **Use `Union`** for multiple possible types
- **Use `Optional`** for nullable values (equivalent to `Union[T, None]`)
- **Python 3.10+ union syntax** allowed: `str | int` instead of `Union[str, int]`


### Protocols and Generics
- **Use Protocol** for structural typing
- **Use TypeVar** for generic types
- **Be specific** about generic constraints


## Documentation Standards

### Docstring Style
We use **Google-style docstrings** for all public functions, classes, and methods.


### Class Documentation

### Module Documentation

### Inline Comments
- **Use sparingly** for complex logic
- **Explain why, not what**
- **Keep comments up-to-date** with code changes


## Import Organization

### Import Order (isort configuration)
1. **Standard library imports**
2. **Related third-party imports**
3. **Local application imports**

```python
# Standard library
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod

# Third-party
import click
import pytest
from pydantic import BaseModel, validator

# Local imports

```

### Import Guidelines
- **Use absolute imports** for external packages
- **Use relative imports** only within the same package
- **Import specific items** rather than entire modules when possible
- **Avoid wildcard imports** (`from module import *`)



### Conditional Imports

## Error Handling Patterns

### Exception Hierarchy
- **Create specific exceptions** for different error types
- **Inherit from appropriate base classes**
- **Include helpful error messages**


### Logging Errors


## Testing Standards

### Test Organization


### Test Naming
- **Descriptive test names** that explain what is being tested
- **Follow pattern**: `test_<method>_<scenario>_<expected_outcome>`
- **Use docstrings** for complex test scenarios



## Security Guidelines

### Input Validation

### Safe Error Messages

## Performance Standards

### Optimization Guidelines

### Memory Management

## Tool Configuration

### pyproject.toml Configuration
```toml
[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
known_first_party = ["project"]

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true

[tool.ruff]
target-version = "py311"
line-length = 88
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
]
ignore = [
    "E501",  # line too long, handled by black
    "B008",  # do not perform function calls in argument defaults
]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--strict-markers",
    "--strict-config",
    "--cov=src",
    "--cov-report=term-missing",
    "--cov-report=html",
    "--cov-fail-under=95",
]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
]

[tool.coverage.run]
source = ["src"]
omit = [
    "*/tests/*",
    "*/test_*.py",
    "*/conftest.py",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if self.debug:",
    "if settings.DEBUG",
    "raise AssertionError",
    "raise NotImplementedError",
    "if 0:",
    "if __name__ == .__main__.:",
]
```

**Note for AI Agents**: These standards are enforced by automated tools (Black, Ruff, mypy) and should be followed in all generated code. When in doubt, refer to existing code patterns in the examples/ directory.
