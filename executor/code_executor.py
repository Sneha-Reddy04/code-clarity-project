
import os
import re
import sys
import pty
import time
import select
import tempfile
import subprocess
import signal


def run_in_terminal(command, temp_dir, user_input="", timeout=5):

    master, slave = pty.openpty()

    process = None
    output = bytearray()

    try:

        process = subprocess.Popen(
            command,
            stdin=slave,
            stdout=slave,
            stderr=slave,
            cwd=temp_dir,
            close_fds=True,
            start_new_session=True
        )

        os.close(slave)
        slave = None

        input_data = user_input.encode("utf-8")

        if input_data and not input_data.endswith(b"\n"):
            input_data += b"\n"

        start_time = time.monotonic()
        input_sent = False

        while True:

            if time.monotonic() - start_time > timeout:

                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()

                raise subprocess.TimeoutExpired(command, timeout)

            # Send input after the program starts.
            if not input_sent and (
                output or time.monotonic() - start_time >= 0.15
            ):

                if input_data:
                    os.write(master, input_data)

                input_sent = True

            ready, _, _ = select.select(
                [master], [], [], 0.05
            )

            if ready:

                try:
                    chunk = os.read(master, 4096)

                    if chunk:
                        output.extend(chunk[:max(0, 100_000 - len(output))])
                        if len(output) >= 100_000:
                            try:
                                os.killpg(process.pid, signal.SIGKILL)
                            except ProcessLookupError:
                                pass
                            process.wait()
                            output.extend(b"\n[Output truncated: 100 KB limit reached.]\n")
                            break

                except OSError:
                    break

            if process.poll() is not None:

                ready, _, _ = select.select(
                    [master], [], [], 0.05
                )

                if ready:

                    try:
                        chunk = os.read(master, 4096)

                        if chunk:
                            output.extend(chunk)
                            continue

                    except OSError:
                        pass

                break

        if process.poll() is None:
            try:
                process.wait(timeout=0.5)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()

        return (
            process.returncode,
            output.decode(
                "utf-8",
                errors="replace"
            ).replace("\r\n", "\n").replace("\r", "\n")
        )

    finally:

        if process is not None and process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()

        if slave is not None:
            os.close(slave)

        os.close(master)


def execute_code(code, language, timeout=5, user_input=""):

    language = language.lower().strip()
    user_input = user_input or ""

    with tempfile.TemporaryDirectory() as temp_dir:

        source_file = None
        executable = None
        class_name = None

        # Python
        if language == "python":

            source_file = os.path.join(
                temp_dir,
                "main.py"
            )

            compile_command = None

            command = [
                sys.executable,
                source_file
            ]

        # C
        elif language == "c":

            source_file = os.path.join(
                temp_dir,
                "main.c"
            )

            executable = os.path.join(
                temp_dir,
                "program"
            )

            compile_command = [
                "clang",
                source_file,
                "-o",
                executable
            ]

        # C++
        elif language in ("c++", "cpp"):

            source_file = os.path.join(
                temp_dir,
                "main.cpp"
            )

            executable = os.path.join(
                temp_dir,
                "program"
            )

            compile_command = [
                "clang++",
                source_file,
                "-o",
                executable
            ]

        # Java
        elif language == "java":

            match = re.search(
                r"public\s+class\s+(\w+)|class\s+(\w+)",
                code
            )

            if not match:

                return {
                    "status": "compilation_error",
                    "input": user_input,
                    "output": "",
                    "error": "No Java class found."
                }

            class_name = match.group(1) or match.group(2)

            source_file = os.path.join(
                temp_dir,
                class_name + ".java"
            )

            compile_command = [
                "javac",
                source_file
            ]

        else:

            return {
                "status": "error",
                "input": user_input,
                "output": "",
                "error": "Unsupported programming language."
            }

        # Save source code
        with open(source_file, "w", encoding="utf-8") as file:
            file.write(code)

        try:

            # Compile C, C++, and Java
            if compile_command:

                compilation = subprocess.run(
                    compile_command,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=temp_dir
                )

                if compilation.returncode != 0:

                    return {
                        "status": "compilation_error",
                        "input": user_input,
                        "output": compilation.stdout,
                        "error": compilation.stderr
                    }

                # Java execution
                if language == "java":

                    command = [
                        "java",
                        "-cp",
                        temp_dir,
                        class_name
                    ]

                # C and C++ execution
                else:

                    command = [executable]

            # Run program
            return_code, output = run_in_terminal(
                command,
                temp_dir,
                user_input,
                timeout
            )

            # Detect missing input
            if not user_input.strip():

                if (
                    "EOFError" in output
                    or "NoSuchElementException" in output
                    or "InputMismatchException" in output
                ):

                    return {
                        "status": "input_required",
                        "input": user_input,
                        "output": output,
                        "error": "Your program requires input.",
                        "message": "Please enter the required input and run again."
                    }

            # Successful execution
            if return_code == 0:

                return {
                    "status": "success",
                    "input": user_input,
                    "output": output,
                    "error": ""
                }

            # Runtime error
            return {
                "status": "runtime_error",
                "input": user_input,
                "output": output,
                "error": f"Program exited with status code {return_code}."
            }

        except subprocess.TimeoutExpired:

            return {
                "status": "timeout",
                "input": user_input,
                "output": "",
                "error": "Program exceeded the execution time limit."
            }

        except FileNotFoundError as error:

            return {
                "status": "setup_error",
                "input": user_input,
                "output": "",
                "error": (
                    f"Required compiler or executable not found: "
                    f"{error.filename}"
                )
            }

        except Exception as error:

            return {
                "status": "error",
                "input": user_input,
                "output": "",
                "error": str(error)
            }
