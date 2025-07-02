# Project Phoenix - Developer Guide

## 1. Getting Started
### Prerequisites
- Python 3.8+
- Git

### Development Environment Setup
1. Fork and clone the repository.
2. Create a virtual environment: `python -m venv venv`
3. Activate it: `source venv/bin/activate` (or `venv\Scripts\activate` on Windows)
4. Install all dependencies: `pip install -r requirements-dev.txt`

## 2. Code Style and Linting
- We follow the **PEP 8** style guide.
- We use **Black** for auto-formatting and **Flake8** for linting.
- Run linters before committing: `flake8 .` and `black .`

## 3. Running Tests
- All tests are located in the `/tests` directory.
- Run all tests using pytest: `pytest`
- To run tests with coverage: `pytest --cov=phoenix_recovery`

## 4. Branching Strategy
- `main`: Stable, production-ready code.
- `develop`: Integration branch. All feature branches merge into here.
- `feature/*`: For new features (e.g., `feature/exfat-parser`).
- `bugfix/*`: For fixing bugs.
- `hotfix/*`: For critical production bugs.

## 5. How to Contribute
- Please see `CONTRIBUTING.md`.
- Create a feature branch from `develop`.
- Make your changes, add tests, and ensure all checks pass.
- Open a Pull Request against the `develop` branch.