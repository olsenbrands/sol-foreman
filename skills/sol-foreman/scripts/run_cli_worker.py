#!/usr/bin/env python3
"""Run one CLI worker without shell interpolation and preserve raw evidence."""

from __future__ import annotations

import argparse
import ctypes
import json
import os
import re
import secrets
import signal
import stat
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


PROCESS_TOKEN_ENV = "SOL_FOREMAN_PROCESS_TOKEN"
WINDOWS_CREATE_SUSPENDED = 0x00000004
DERIVED_METADATA_URL = re.compile(r"https?://[^\s\"'<>]+", re.IGNORECASE)


def within(path: Path, root: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(root.resolve(strict=True))
        return True
    except ValueError:
        return False


class WorkerCancelled(Exception):
    def __init__(self, signum: int):
        super().__init__(f"worker wrapper received signal {signum}")
        self.signum = signum


def redact_urls_from_derived_metadata(value: str) -> str:
    """Redact every URL from launcher-generated metadata, never worker streams."""
    return DERIVED_METADATA_URL.sub("<redacted-url>", value)


def _reject_artifact_symlink(path: Path) -> None:
    """Reject the artifact entry itself without resolving a dangling link away."""
    if path.is_symlink():
        raise ValueError(f"artifact path is a symlink: {path}")


def validate_artifacts(paths: list[Path], protected_roots: list[Path]) -> None:
    if len(paths) != 4:
        raise ValueError("ticket, stdout, stderr, and receipt paths are required")
    ticket, *evidence_paths = paths
    for path in paths:
        _reject_artifact_symlink(path)
    resolved = [path.resolve(strict=False) for path in paths]
    if len(set(resolved)) != len(resolved):
        raise ValueError("ticket, stdout, stderr, and receipt paths must be distinct")
    try:
        ticket_metadata = ticket.lstat()
    except FileNotFoundError:
        ticket_metadata = None
    if ticket_metadata is not None and not stat.S_ISREG(ticket_metadata.st_mode):
        raise ValueError(f"ticket must be a regular file: {ticket}")
    for path in evidence_paths:
        try:
            metadata = path.lstat()
        except FileNotFoundError:
            continue
        if not stat.S_ISREG(metadata.st_mode):
            raise ValueError(f"evidence path exists and is not a regular file: {path}")
        raise ValueError(f"evidence path already exists; use a fresh run path: {path}")
    for path in resolved:
        for root in protected_roots:
            if within(path, root):
                raise ValueError(f"evidence path must be outside protected root: {path}")


def validate_cwd(cwd: Path, protected_roots: list[Path], read_only_cwd_roots: list[Path]) -> None:
    for root in protected_roots:
        if within(cwd, root) and not any(within(cwd, allowed) for allowed in read_only_cwd_roots):
            raise ValueError(
                f"cwd is inside a protected root without an explicit read-only cwd allowance: {cwd}"
            )


def _windows_job(process: subprocess.Popen[bytes]) -> Optional[int]:
    if os.name != "nt":
        return None
    from ctypes import wintypes

    class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", ctypes.c_longlong),
            ("PerJobUserTimeLimit", ctypes.c_longlong),
            ("LimitFlags", wintypes.DWORD),
            ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t),
            ("ActiveProcessLimit", wintypes.DWORD),
            ("Affinity", ctypes.c_size_t),
            ("PriorityClass", wintypes.DWORD),
            ("SchedulingClass", wintypes.DWORD),
        ]

    class IO_COUNTERS(ctypes.Structure):
        _fields_ = [(name, ctypes.c_ulonglong) for name in (
            "ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
            "ReadTransferCount", "WriteTransferCount", "OtherTransferCount",
        )]

    class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
            ("IoInfo", IO_COUNTERS),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    kernel32.CreateJobObjectW.restype = wintypes.HANDLE
    kernel32.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    kernel32.SetInformationJobObject.restype = wintypes.BOOL
    kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    handle = kernel32.CreateJobObjectW(None, None)
    if not handle:
        return None
    information = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
    information.BasicLimitInformation.LimitFlags = 0x00002000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    configured = kernel32.SetInformationJobObject(
        handle, 9, ctypes.byref(information), ctypes.sizeof(information)
    )
    assigned = configured and kernel32.AssignProcessToJobObject(handle, int(process._handle))
    if not assigned:
        kernel32.CloseHandle(handle)
        return None
    return int(handle)


def _windows_resume_process(process: subprocess.Popen[bytes]) -> bool:
    """Resume the primary thread after Job Object assignment closes the launch race."""
    if os.name != "nt":
        return True
    from ctypes import wintypes

    class THREADENTRY32(ctypes.Structure):
        _fields_ = [
            ("dwSize", wintypes.DWORD),
            ("cntUsage", wintypes.DWORD),
            ("th32ThreadID", wintypes.DWORD),
            ("th32OwnerProcessID", wintypes.DWORD),
            ("tpBasePri", wintypes.LONG),
            ("tpDeltaPri", wintypes.LONG),
            ("dwFlags", wintypes.DWORD),
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel32.Thread32First.argtypes = [wintypes.HANDLE, ctypes.POINTER(THREADENTRY32)]
    kernel32.Thread32First.restype = wintypes.BOOL
    kernel32.Thread32Next.argtypes = [wintypes.HANDLE, ctypes.POINTER(THREADENTRY32)]
    kernel32.Thread32Next.restype = wintypes.BOOL
    kernel32.OpenThread.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenThread.restype = wintypes.HANDLE
    kernel32.ResumeThread.argtypes = [wintypes.HANDLE]
    kernel32.ResumeThread.restype = wintypes.DWORD
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL

    snapshot = kernel32.CreateToolhelp32Snapshot(0x00000004, 0)  # TH32CS_SNAPTHREAD
    if snapshot in (None, 0, wintypes.HANDLE(-1).value):
        return False
    entry = THREADENTRY32()
    entry.dwSize = ctypes.sizeof(entry)
    resumed = False
    try:
        available = bool(kernel32.Thread32First(snapshot, ctypes.byref(entry)))
        while available:
            if entry.th32OwnerProcessID == process.pid:
                thread = kernel32.OpenThread(0x0002, False, entry.th32ThreadID)  # THREAD_SUSPEND_RESUME
                if thread:
                    try:
                        resumed = kernel32.ResumeThread(thread) != 0xFFFFFFFF
                    finally:
                        kernel32.CloseHandle(thread)
                break
            available = bool(kernel32.Thread32Next(snapshot, ctypes.byref(entry)))
    finally:
        kernel32.CloseHandle(snapshot)
    return resumed


def _posix_group_exists(group_id: int) -> bool:
    try:
        os.killpg(group_id, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def _posix_token_pids(token: str) -> Optional[set[int]]:
    """Find descendants by an inherited run token, including processes that call setsid()."""
    marker = f"{PROCESS_TOKEN_ENV}={token}".encode()
    if sys.platform.startswith("linux") and Path("/proc").is_dir():
        matches: set[int] = set()
        try:
            entries = list(Path("/proc").iterdir())
        except OSError:
            return None
        for entry in entries:
            if not entry.name.isdigit():
                continue
            try:
                environment = (entry / "environ").read_bytes()
            except (OSError, PermissionError):
                continue
            if marker + b"\0" in environment:
                matches.add(int(entry.name))
        return matches

    try:
        observed = subprocess.run(
            ["ps", "eww", "-axo", "pid=,command="],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError:
        return None
    if observed.returncode != 0:
        return None
    matches = set()
    for line in observed.stdout.splitlines():
        fields = line.strip().split(None, 1)
        if len(fields) == 2 and fields[0].isdigit() and marker in fields[1]:
            matches.add(int(fields[0]))
    return matches


def _signal_posix_pids(pids: set[int], signum: int) -> bool:
    complete = True
    for pid in pids:
        if pid <= 1 or pid == os.getpid():
            complete = False
            continue
        try:
            os.kill(pid, signum)
        except ProcessLookupError:
            pass
        except PermissionError:
            complete = False
    return complete


def _signal_posix_group_or_child(process: subprocess.Popen[bytes], signum: int) -> bool:
    """Signal the session group, falling back to the known direct child."""
    try:
        os.killpg(process.pid, signum)
        return True
    except ProcessLookupError:
        return True
    except PermissionError:
        try:
            os.kill(process.pid, signum)
        except ProcessLookupError:
            return True
        except PermissionError:
            return False
        # The direct child was signalled, but descendants in its group remain
        # unproven until token tracking observes their closure.
        return False


def _pid_exists(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def close_process_tree(
    process: subprocess.Popen[bytes],
    job_handle: Optional[int],
    terminate: bool,
    process_token: Optional[str] = None,
) -> bool:
    if os.name == "nt":
        fallback_closed = False
        if terminate and process.poll() is None:
            killed = subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            fallback_closed = killed.returncode == 0
        if job_handle is not None:
            from ctypes import wintypes

            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
            kernel32.CloseHandle.restype = wintypes.BOOL
            kernel32.CloseHandle(wintypes.HANDLE(job_handle))
        if process.poll() is None:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        return job_handle is not None or fallback_closed

    scan_complete = process_token is not None
    token_pids: set[int] = set()
    if process_token is not None:
        observed = _posix_token_pids(process_token)
        if observed is None:
            scan_complete = False
        else:
            token_pids.update(observed)

    scan_complete = _signal_posix_group_or_child(process, signal.SIGTERM) and scan_complete
    scan_complete = _signal_posix_pids(token_pids, signal.SIGTERM) and scan_complete
    grace_deadline = time.monotonic() + 1.0
    while time.monotonic() < grace_deadline:
        if process_token is not None:
            observed = _posix_token_pids(process_token)
            if observed is None:
                scan_complete = False
            else:
                token_pids.update(observed)
        if not _posix_group_exists(process.pid) and not token_pids:
            break
        token_pids = {pid for pid in token_pids if _pid_exists(pid)}
        time.sleep(0.05)
    if _posix_group_exists(process.pid):
        scan_complete = _signal_posix_group_or_child(process, signal.SIGKILL) and scan_complete
    scan_complete = _signal_posix_pids(token_pids, signal.SIGKILL) and scan_complete
    if process.poll() is None:
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
    closure_deadline = time.monotonic() + 5.0
    remaining_token_pids = token_pids
    while time.monotonic() < closure_deadline:
        if process_token is not None:
            observed = _posix_token_pids(process_token)
            if observed is None:
                scan_complete = False
            else:
                remaining_token_pids = observed
        remaining_token_pids = {pid for pid in remaining_token_pids if _pid_exists(pid)}
        if not _posix_group_exists(process.pid) and not remaining_token_pids:
            break
        time.sleep(0.05)
    return scan_complete and not _posix_group_exists(process.pid) and not remaining_token_pids


def atomic_json(path: Path, payload: dict[str, Any], *, create: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        if create:
            try:
                os.link(temporary, path)
            except FileExistsError as exc:
                raise FileExistsError(f"receipt path already exists: {path}") from exc
            os.unlink(temporary)
        else:
            os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def run(
    command: list[str],
    cwd: Path,
    ticket: Path,
    stdout_path: Path,
    stderr_path: Path,
    receipt_path: Path,
    protected_roots: list[Path],
    read_only_cwd_roots: Optional[list[Path]] = None,
) -> int:
    if not command or command[0] == "--":
        raise ValueError("a command is required after --")
    validate_artifacts([ticket, stdout_path, stderr_path, receipt_path], protected_roots)
    cwd = cwd.resolve(strict=True)
    ticket = ticket.resolve(strict=True)
    if not cwd.is_dir() or not ticket.is_file():
        raise ValueError("cwd must be a directory and ticket must be a file")
    read_only_cwd_roots = read_only_cwd_roots or []
    validate_cwd(cwd, protected_roots, read_only_cwd_roots)
    for path in (stdout_path, stderr_path, receipt_path):
        path.parent.mkdir(parents=True, exist_ok=True)
        _reject_artifact_symlink(path)

    receipt_command = [redact_urls_from_derived_metadata(value) for value in command]

    started = datetime.now(timezone.utc)
    monotonic_start = time.monotonic()
    pid: Optional[int] = None
    exit_code = 1
    error: Optional[str] = None
    process: Optional[subprocess.Popen[bytes]] = None
    job_handle: Optional[int] = None
    cancelled = False
    process_tree_closed = False
    process_token = secrets.token_hex(16)
    old_handlers: dict[int, Any] = {}
    try:
        with ticket.open("rb") as stdin_handle:
            with stdout_path.open("xb") as stdout_handle:
                with stderr_path.open("xb") as stderr_handle:
                    popen_options: dict[str, Any] = {}
                    child_environment = os.environ.copy()
                    child_environment[PROCESS_TOKEN_ENV] = process_token
                    if os.name == "nt":
                        popen_options["creationflags"] = (
                            subprocess.CREATE_NEW_PROCESS_GROUP | WINDOWS_CREATE_SUSPENDED
                        )
                    else:
                        popen_options["start_new_session"] = True
                    process = subprocess.Popen(
                        command,
                        cwd=cwd,
                        stdin=stdin_handle,
                        stdout=stdout_handle,
                        stderr=stderr_handle,
                        shell=False,
                        env=child_environment,
                        **popen_options,
                    )
                    pid = process.pid
                    job_handle = _windows_job(process)
                    if os.name == "nt" and not _windows_resume_process(process):
                        close_process_tree(
                            process, job_handle, terminate=True, process_token=process_token
                        )
                        job_handle = None
                        raise OSError("could not resume suspended worker after Job Object assignment")
                    try:
                        atomic_json(
                            receipt_path,
                            {
                                "schema_version": 1,
                                "status": "running",
                                "command": receipt_command,
                                "cwd": str(cwd),
                                "ticket": str(ticket),
                                "stdout": str(stdout_path.resolve(strict=False)),
                                "stderr": str(stderr_path.resolve(strict=False)),
                                "pid": pid,
                                "started_at": started.isoformat(),
                            },
                            create=True,
                        )
                    except OSError:
                        close_process_tree(
                            process, job_handle, terminate=True, process_token=process_token
                        )
                        raise
                    if threading.current_thread() is threading.main_thread():
                        def cancelled_handler(signum: int, _frame: Any) -> None:
                            raise WorkerCancelled(signum)

                        for signum in (signal.SIGINT, signal.SIGTERM):
                            old_handlers[signum] = signal.getsignal(signum)
                            signal.signal(signum, cancelled_handler)
                    try:
                        exit_code = process.wait()
                    except WorkerCancelled as exc:
                        cancelled = True
                        error = str(exc)
                        exit_code = 128 + exc.signum
                        process_tree_closed = close_process_tree(
                            process, job_handle, terminate=True, process_token=process_token
                        )
                        job_handle = None
                    finally:
                        for signum, handler in old_handlers.items():
                            signal.signal(signum, handler)
                    if not cancelled:
                        process_tree_closed = close_process_tree(
                            process, job_handle, terminate=False, process_token=process_token
                        )
                        job_handle = None
    except OSError as exc:
        error = redact_urls_from_derived_metadata(f"worker process failed to start: {exc}")
        if process is not None:
            process_tree_closed = close_process_tree(
                process, job_handle, terminate=True, process_token=process_token
            )
        else:
            process_tree_closed = True

    ended = datetime.now(timezone.utc)
    receipt = {
        "schema_version": 1,
        "status": "terminal",
        "command": receipt_command,
        "cwd": str(cwd),
        "ticket": str(ticket),
        "stdout": str(stdout_path.resolve(strict=False)),
        "stderr": str(stderr_path.resolve(strict=False)),
        "pid": pid,
        "started_at": started.isoformat(),
        "ended_at": ended.isoformat(),
        "duration_seconds": round(time.monotonic() - monotonic_start, 3),
        "exit_code": exit_code,
        "error": error,
        "cancelled": cancelled,
        "process_tree_closed": process_tree_closed,
    }
    atomic_json(receipt_path, receipt)
    return exit_code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cwd", required=True, type=Path)
    parser.add_argument("--ticket", required=True, type=Path)
    parser.add_argument("--stdout", required=True, type=Path)
    parser.add_argument("--stderr", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--protected-root", action="append", default=[], type=Path)
    parser.add_argument("--read-only-cwd-root", action="append", default=[], type=Path)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    try:
        return run(
            command,
            args.cwd,
            args.ticket,
            args.stdout,
            args.stderr,
            args.receipt,
            args.protected_root,
            args.read_only_cwd_root,
        )
    except (OSError, ValueError) as exc:
        print(
            f"CLI worker launch failed: {redact_urls_from_derived_metadata(str(exc))}",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
