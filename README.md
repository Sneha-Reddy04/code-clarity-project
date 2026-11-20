# CodeClarity — AI-Powered Code Analyzer and Programming Tutor

CodeClarity is a Flask + MySQL learning project for analyzing and understanding **Python, Java, C and C++** programs. It provides a Monaco code editor, local compile/run support, Gemini-powered analysis and tutoring, saved analysis history, reports, account pages and feedback.

## Features

- User registration and login with hashed passwords.
- Monaco editor with Python, Java, C and C++ syntax modes.
- Program execution and compiler/runtime output.
- Gemini actions: analyze, find errors, suggest corrected code and teach the submitted program.
- Four separate MySQL database connections: users, analysis, reports and feedback.
- Analysis history, saved reports, profile, feedback, help and about pages.
- Responsive dark navy / purple interface.

## Setup (macOS)

1. Install Python 3.10+ and MySQL Server. For C/C++, install Xcode Command Line Tools (`xcode-select --install`). For Java, install a JDK and ensure `java` and `javac` are on PATH.
2. Create and activate a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Copy `.env.example` to `.env`, then fill in your MySQL credentials, database names, a long random `SECRET_KEY`, Gemini API key and model. Never commit `.env`.
5. Ensure the four databases named in `.env` already exist. The project keeps the four-database design. Initialize the tables:

   ```bash
   python -m databases.init_db
   ```

6. Start the application:

   ```bash
   python app.py
   ```

7. Open `http://127.0.0.1:5001`.

## Environment variables

See `.env.example`. The MySQL user must have privileges on all four configured databases. Existing database contents are not dropped by initialization; it uses `CREATE TABLE IF NOT EXISTS`.

## Important execution safety note

The included executor launches submitted programs as local operating-system processes. It is intended for a **single-user local college demonstration with trusted code**. It is not a secure multi-user code sandbox. Do not expose this application to the public internet or run untrusted code on a machine containing sensitive data. A production deployment needs isolated containers/VMs, restricted networking, CPU/memory/process limits, non-root execution and additional security review.

## AI configuration

AI responses require a valid `GEMINI_API_KEY` and supported `GEMINI_MODEL`. If the key is absent or quota is exhausted, execution can still run, but AI analysis/tutoring will return a configuration or provider message.

## Project layout

```text
CodeClarity/
├── analyzer/       # AI prompts and combined analysis
├── databases/      # Four MySQL connection modules and schema initializer
├── executor/       # Local Python/C/C++/Java execution
├── static/css/     # Styling
├── templates/      # Flask/Jinja pages
├── tests/          # Existing test scripts
├── app.py
├── config.py
├── requirements.txt
└── .env.example
```
