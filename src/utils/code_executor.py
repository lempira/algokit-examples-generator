"""Utility to execute generated examples"""

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ExecutionResult:
    """Result of executing an example"""
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    error_message: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "success": self.success,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "exit_code": self.exit_code,
            "error_message": self.error_message,
        }


class CodeExecutor:
    """Executes generated example code"""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    async def run(self, example_path: Path) -> ExecutionResult:
        """Execute an example
        
        Args:
            example_path: Path to the example folder
            
        Returns:
            ExecutionResult with execution details
        """
        return self.run_sync(example_path)

    def run_sync(self, example_path: Path) -> ExecutionResult:
        """Synchronous version of run
        
        Looks for common entry points and executes them:
        - package.json (npm install && npm start)
        - requirements.txt (pip install && python main.py)
        - main.py, main.ts, index.ts, etc.
        """
        if not example_path.exists():
            return ExecutionResult(
                success=False,
                stdout="",
                stderr="",
                exit_code=-1,
                error_message=f"Example path does not exist: {example_path}"
            )

        # Detect example type and execution strategy
        if (example_path / "package.json").exists():
            return self._run_node_example(example_path)
        elif (example_path / "requirements.txt").exists():
            return self._run_python_example(example_path)
        elif (example_path / "main.py").exists():
            return self._run_python_file(example_path / "main.py")
        elif (example_path / "main.ts").exists():
            return self._run_typescript_file(example_path / "main.ts")
        else:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr="",
                exit_code=-1,
                error_message="No recognized entry point found (package.json, main.py, etc.)"
            )

    def _run_node_example(self, example_path: Path) -> ExecutionResult:
        """Run a Node.js/TypeScript example"""
        try:
            # Install dependencies
            install_result = subprocess.run(
                ["npm", "install"],
                cwd=example_path,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            if install_result.returncode != 0:
                return ExecutionResult(
                    success=False,
                    stdout=install_result.stdout,
                    stderr=install_result.stderr,
                    exit_code=install_result.returncode,
                    error_message="npm install failed"
                )

            # Run the example (try npm start, then npm run dev)
            for command in [["npm", "start"], ["npm", "run", "dev"]]:
                run_result = subprocess.run(
                    command,
                    cwd=example_path,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout
                )

                if run_result.returncode == 0:
                    return ExecutionResult(
                        success=True,
                        stdout=run_result.stdout,
                        stderr=run_result.stderr,
                        exit_code=run_result.returncode
                    )

            return ExecutionResult(
                success=False,
                stdout=run_result.stdout,
                stderr=run_result.stderr,
                exit_code=run_result.returncode,
                error_message="npm start/dev failed"
            )

        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr="",
                exit_code=-1,
                error_message=f"Execution timeout after {self.timeout}s"
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr="",
                exit_code=-1,
                error_message=f"Execution error: {str(e)}"
            )

    def _run_python_example(self, example_path: Path) -> ExecutionResult:
        """Run a Python example with dependencies"""
        try:
            # Install dependencies
            install_result = subprocess.run(
                ["pip", "install", "-r", "requirements.txt"],
                cwd=example_path,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            if install_result.returncode != 0:
                return ExecutionResult(
                    success=False,
                    stdout=install_result.stdout,
                    stderr=install_result.stderr,
                    exit_code=install_result.returncode,
                    error_message="pip install failed"
                )

            # Run main.py
            return self._run_python_file(example_path / "main.py")

        except Exception as e:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr="",
                exit_code=-1,
                error_message=f"Execution error: {str(e)}"
            )

    def _run_python_file(self, file_path: Path) -> ExecutionResult:
        """Run a single Python file"""
        try:
            result = subprocess.run(
                ["python", str(file_path)],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            return ExecutionResult(
                success=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode
            )

        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr="",
                exit_code=-1,
                error_message=f"Execution timeout after {self.timeout}s"
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr="",
                exit_code=-1,
                error_message=f"Execution error: {str(e)}"
            )

    def _run_typescript_file(self, file_path: Path) -> ExecutionResult:
        """Run a TypeScript file"""
        try:
            result = subprocess.run(
                ["ts-node", str(file_path)],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            return ExecutionResult(
                success=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode
            )

        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr="",
                exit_code=-1,
                error_message=f"Execution timeout after {self.timeout}s"
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr="",
                exit_code=-1,
                error_message=f"Execution error: {str(e)}"
            )

