"""Docker Sandbox Backend for Deep Agents.

Executes arbitrary shell commands in an isolated Docker container mounting
the workspace directory, while providing fast host filesystem operations.
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

from deepagents.backends import FilesystemBackend
from deepagents.backends.sandbox import ExecuteResponse, SandboxBackendProtocol

logger = logging.getLogger(__name__)


def _check_docker_available() -> str | None:
    """Check if Docker daemon is running."""
    try:
        subprocess.run(
            ["docker", "info"],
            capture_output=True,
            check=True,
            timeout=5,
        )
    except FileNotFoundError:
        return "Docker not installed or not in PATH"
    except subprocess.CalledProcessError:
        return "Docker daemon not running"
    except subprocess.TimeoutExpired:
        return "Docker daemon not responding"
    except Exception as e:
        return f"Docker check error: {e}"
    return None


class DockerSandboxBackend(FilesystemBackend, SandboxBackendProtocol):
    """Sandbox backend executing shell commands inside an isolated Docker container.

    Inherits file operations (ls, read, write, edit, delete, glob, grep) from
    FilesystemBackend on the host workspace directory, and satisfies
    SandboxBackendProtocol by providing containerized `execute()`.
    """

    def __init__(
        self,
        root_dir: str | Path,
        docker_image: str | None = None,
        default_timeout: int = 120,
        memory_limit: str | None = None,
        cpu_limit: str | None = None,
        network: str | None = None,
        max_output_bytes: int = 100_000,
    ) -> None:
        super().__init__(
            root_dir=root_dir,
            virtual_mode=True,
            max_file_size_mb=10,
        )
        self.docker_image = docker_image or os.getenv("DOCKER_SANDBOX_IMAGE", "python:3.12-slim")
        self.default_timeout = int(os.getenv("DOCKER_SANDBOX_TIMEOUT", str(default_timeout)))
        self.memory_limit = memory_limit or os.getenv("DOCKER_SANDBOX_MEMORY", "512m")
        self.cpu_limit = cpu_limit or os.getenv("DOCKER_SANDBOX_CPUS", "1")
        self.network = network or os.getenv("DOCKER_SANDBOX_NETWORK", "none")
        self._max_output_bytes = max_output_bytes
        self._sandbox_id = f"docker-{uuid.uuid4().hex[:8]}"

    @property
    def id(self) -> str:
        return self._sandbox_id

    def execute(
        self,
        command: str,
        *,
        timeout: int | None = None,
    ) -> ExecuteResponse:
        """Execute a shell command inside the Docker container."""
        if not command or not isinstance(command, str):
            return ExecuteResponse(
                output="Error: Command must be a non-empty string.",
                exit_code=1,
                truncated=False,
            )

        docker_err = _check_docker_available()
        if docker_err:
            return ExecuteResponse(
                output=f"Error: Docker execution failed - {docker_err}",
                exit_code=1,
                truncated=False,
            )

        effective_timeout = timeout if timeout is not None else self.default_timeout
        if effective_timeout <= 0:
            effective_timeout = self.default_timeout

        cmd = [
            "docker",
            "run",
            "--rm",
            "-i",
            f"--network={self.network}",
            f"--memory={self.memory_limit}",
            f"--cpus={self.cpu_limit}",
            "-v",
            f"{self.cwd}:/workspace",
            "-w",
            "/workspace",
            self.docker_image,
            "/bin/sh",
            "-c",
            command,
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                stdin=subprocess.DEVNULL,
                text=True,
                timeout=effective_timeout,
                check=False,
            )

            output_parts: list[str] = []
            if result.stdout:
                output_parts.append(result.stdout)
            if result.stderr:
                stderr_lines = result.stderr.strip().split("\n")
                output_parts.extend(f"[stderr] {line}" for line in stderr_lines if line)

            output = "\n".join(output_parts) if output_parts else "<no output>"

            truncated = False
            if len(output) > self._max_output_bytes:
                output = output[: self._max_output_bytes] + f"\n\n... Output truncated at {self._max_output_bytes} bytes."
                truncated = True

            if result.returncode != 0 and not output.endswith(f"Exit code: {result.returncode}"):
                output = f"{output.rstrip()}\n\nExit code: {result.returncode}"

            return ExecuteResponse(
                output=output,
                exit_code=result.returncode,
                truncated=truncated,
            )

        except subprocess.TimeoutExpired:
            return ExecuteResponse(
                output=f"Error: Command timed out after {effective_timeout} seconds.",
                exit_code=124,
                truncated=False,
            )
        except Exception as e:
            return ExecuteResponse(
                output=f"Error executing in Docker ({type(e).__name__}): {e}",
                exit_code=1,
                truncated=False,
            )
