#!/usr/bin/env python3
# SPDX-License-Identifier: MIT-0
#
# Implement the systemd notify protocol without external dependencies.
# Supports both readiness notification on startup and on reloading,
# according to the protocol defined at:
# https://www.freedesktop.org/software/systemd/man/latest/sd_notify.html
# This protocol is guaranteed to be stable as per:
# https://systemd.io/PORTABILITY_AND_STABILITY/

import errno
import os
import signal
import socket
import sys
import time
from types import FrameType
from typing import Optional

# import sd_debug

reloading = False
terminating = False
faking_death = False
remote_debug = False
debug = os.environ.get("DEBUG", "False").lower() == "true"
pid = os.getpid()


def start_debugging() -> None:
    global debug, remote_debug
    import debugpy

    debug = True
    remote_debug = False
    debugpy.listen(5678)
    print("Waiting for debugger attach")
    # debugpy.wait_for_client()
    # debugpy.breakpoint()


def notify(message: bytes) -> None:
    if not message:
        raise ValueError("notify() requires a message")

    socket_path = os.environ.get("NOTIFY_SOCKET")
    if not socket_path:
        return

    if socket_path[0] not in ("/", "@"):
        raise OSError(errno.EAFNOSUPPORT, "Unsupported socket type")

    # Handle abstract socket.
    if socket_path[0] == "@":
        socket_path = "\0" + socket_path[1:]

    with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM | socket.SOCK_CLOEXEC) as sock:
        sock.connect(socket_path)
        sock.sendall(message)


def notify_ready() -> None:
    notify(b"READY=1")


def notify_reloading() -> None:
    microsecs = time.clock_gettime_ns(time.CLOCK_MONOTONIC) // 1000
    notify(f"RELOADING=1\nMONOTONIC_USEC={microsecs}".encode())


def notify_stopping() -> None:
    notify(b"STOPPING=1")


def reload(signum: int, frame: Optional[FrameType]) -> None:
    global reloading
    reloading = True


def remote_debugging(signum: int, frame: Optional[FrameType]) -> None:
    notify(b"DEBUG=1")
    print("Remote debugging enabled")
    start_debugging()


def fake_death(signum: int, frame: Optional[FrameType]) -> None:
    global faking_death
    global reloading
    reloading = True
    faking_death = True


def terminate(signum: int, frame: Optional[FrameType]) -> None:
    global terminating
    terminating = True


def main() -> None:
    print("Doing initial setup")
    global reloading, terminating, faking_death, debug, remote_debug, pid

    pid = os.getpid()

    # Set up signal handlers.
    print("Setting up signal handlers, pid:", pid)
    signal.signal(signal.SIGHUP, reload)
    signal.signal(signal.SIGINT, terminate)
    signal.signal(signal.SIGUSR1, fake_death)
    signal.signal(signal.SIGUSR2, remote_debugging)
    signal.signal(signal.SIGTERM, terminate)

    # Do any other setup work here.

    # Once all setup is done, signal readiness.
    print("Done setting up")
    notify_ready()

    print("Starting loop")
    while not terminating:
        pid = os.getpid()
        if reloading:
            print("Reloading")
            reloading = False

            # Support notifying the manager when reloading configuration.
            # This allows accurate state tracking as well as automatically
            # enabling 'systemctl reload' without needing to manually
            # specify an ExecReload= line in the unit file.

            notify_reloading()

            # Do some reconfiguration work here.
            if faking_death:
                sys.exit("SIGUSR1 received, faking death")

            print("Done reloading")
            notify_ready()

        if remote_debug:
            remote_debugging(signal.SIGUSR2, None)
            print("Remote debugging")

        # Do the real work here ...
        print(f"Debug: {debug}, pid: {pid}")
        print("Sleeping for five seconds")
        time.sleep(5)

    print("Terminating")
    notify_stopping()


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    # sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)
    print("Starting app, pid:", pid)
    main()
    print("Stopped app")
