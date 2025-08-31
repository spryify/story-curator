# GitHub Copilot Instructions for Python

## General Coding Standards

- **PEP 8 Compliance:** All Python code must adhere to the PEP 8 style guide.
- **Clarity and Readability:** Use descriptive variable, function, and class names.
- **Documentation:** Every public function, class, and method must have a docstring that explains its purpose, arguments, and return values. Use the Google or NumPy docstring format.
- **Type Hinting:** Use type hints for function arguments and return values to improve code clarity and enable static analysis.
- **Error Handling:** Use `try...except` blocks for all operations that might fail (e.g., file I/O, network requests). Do not use bare `except` statements.
- **Single Responsibility Principle:** Functions and classes should be designed to do one thing and do it well.

## Specific Instructions

- **Virtual Environments:** Remind developers to use a virtual environment for all dependencies.
- **Dependency Management:** Use `requirements.txt` or `pyproject.toml` with `poetry` for managing dependencies. Do not hardcode dependencies.
- **Testing:** When writing a new function or class, also write corresponding unit tests using the `pytest` framework.
- **Imports:** Place imports at the top of the file. Group standard library imports, third-party imports, and local application imports, each on a separate line.
- **Logging:** Use the `logging` module for logging instead of `print` statements. Configure logging levels appropriately (DEBUG, INFO, WARNING, ERROR, CRITICAL).


## Architectural and Design Patterns

- **Modular Design:** Organize code into small, independent modules (e.g., separate data models, business logic, and API endpoints into distinct files or folders).
- **Dependency Injection:** Pass dependencies (e.g., database connections, external clients) as arguments to functions or class constructors instead of creating them internally.
- **Configuration Management:** All application configuration, including database URLs and API keys, must be loaded from environment variables using a library like `python-dotenv` or `pydantic.Settings`. Do not hardcode these values.


## Security Best Practices

- **Input Validation:** All user input must be validated and sanitized to prevent common vulnerabilities like SQL injection or cross-site scripting (XSS).
- **Secrets Management:** Do not store API keys or other secrets in the codebase or commit them to version control. They must be loaded from environment variables.
- **Principle of Least Privilege:** When interacting with external services, use the minimum necessary permissions required for the task.
- **Dependency Auditing:** Be mindful of the security of project dependencies. If a dependency is introduced, consider its security track record and potential vulnerabilities.


## Performance and Optimization

- **Asynchronous Operations:** For I/O-bound tasks (e.g., network requests, database queries), use asynchronous programming with `asyncio` to prevent blocking the main thread.
- **Efficient Data Structures:** Use the most efficient data structure for the task (e.g., `set` for fast membership testing, `dict` for key-value lookups).
- **Avoid N+1 Queries:** When querying a database, prefer to fetch related data in a single query rather than making multiple queries in a loop. Use `JOIN` or `SELECT IN` statements.
- **Caching:** Use caching mechanisms (e.g., `functools.lru_cache` for functions or a dedicated caching library) to store the results of expensive operations.