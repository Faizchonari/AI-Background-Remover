# Contributing to AI Background Remover

Thank you for your interest in contributing to **AI Background Remover**! We welcome bug fixes, performance enhancements, model integrations, and documentation improvements.

---

## Code of Conduct

All contributors and participants are expected to follow our [Code of Conduct](../CODE_OF_CONDUCT.md) to maintain a respectful and welcoming environment for everyone.

---

## How to Report Bugs

Before submitting a bug report:
1. Check the [Troubleshooting Guide](troubleshooting.md) to see if a known solution exists.
2. Search existing [GitHub Issues](https://github.com/Faizchonari/AI-Background-Remover/issues) to avoid duplicates.

When submitting a bug report:
- Use the **Bug Report** issue template.
- Include your Windows version (e.g. Windows 11 23H2).
- Specify CPU, RAM, and GPU model.
- Include sanitized excerpts from `logs/app.log` (make sure no personal paths or confidential information are exposed).
- Provide minimal steps to reproduce the issue.

---

## How to Propose Features or New Models

- Use the **Feature Request** or **Model Request** issue template.
- Clearly describe the problem the feature solves.
- If proposing an AI model, specify its license, parameters, and Hugging Face repository link.

---

## Development & Testing Workflow

1. **Fork and Branch**:
   Create a feature branch from `main`:
   ```powershell
   git checkout -b feature/my-enhancement
   ```

2. **Follow Coding Standards**:
   - Follow PEP 8 style conventions.
   - Use meaningful variable and function names.
   - Include type annotations where appropriate.
   - Keep GUI logic decoupled from background worker threads.
   - Do not log sensitive user data (paths, images, keys).

3. **Run Tests**:
   Ensure all existing and new tests pass:
   ```powershell
   python -m unittest discover -s tests -v
   ```

4. **Submit a Pull Request**:
   - Open a PR targeting the `main` branch.
   - Fill out the Pull Request template completely.
   - Link any related issues (e.g. `Fixes #123`).
