# Contributing to Secure Data Wiping (SDW)

First off, thank you for considering contributing to SDW! It's people like you who make the open-source community such an amazing place to learn, inspire, and create.

To maintain code quality and ensure safety across various platforms, please review the guidelines below.

---

## 🛠️ How to Contribute

### 1. Reporting Bugs & Issues
*   Check the [Issues tab](https://github.com/devivaddadi/secure_data_wiping/issues) first to ensure it hasn't already been reported.
*   Clearly describe the bug, including your operating system, Python version, and logs from `sdw_audit.log` if applicable.
*   Provide a minimal reproducible example or steps to reproduce the issue.

### 2. Suggesting Enhancements
*   Open an issue with the tag `enhancement`.
*   Explain the utility of the feature, how it fits into the current wiping paradigms, and how it impacts storage media safety.

### 3. Submitting Pull Requests
*   Fork the repository and create your branch from `main` (e.g., `feature/awesome-protocol` or `bugfix/windows-admin-check`).
*   Ensure your code matches the existing style and contains helpful comments explaining complex low-level operations.
*   Write clear, descriptive commit messages.
*   Ensure that all tests pass and dependencies are documented in `requirements.txt`.
*   Submit a Pull Request targeting the `main` branch.

---

## 💻 Development Workflow

1.  **Environment Setup:**
    ```bash
    python -m venv venv
    source venv/bin/activate # or venv\Scripts\activate on Windows
    pip install -r requirements.txt
    ```
2.  **Coding Standards:**
    *   Maintain Python PEP 8 guidelines.
    *   Do not remove or alter existing enterprise audit logs or certificate verification signatures without a strong architectural reason.
    *   Ensure cross-platform compatibility (Windows & Linux) when using system-level utilities.

---

## ⚖️ Code of Conduct
We expect all contributors to adhere to standard respectful communications, focusing on collaborative progress and safety.
