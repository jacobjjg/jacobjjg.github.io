"""Traffic sensors. Each yields Event objects.

* access-log sensor: nginx/Apache "combined" format (or JSON lines), tailed live or read whole.
* packet sensor: Linux AF_PACKET capture of inbound TCP SYNs (needs root). Sees every port,
  so it catches scans and floods that never reach the web server's log.
"""
from __future__ import annotations

import json
import os
import re
import socket
import struct
import time
from datetime import datetime
from typing import Iterator

from .events import Event

_COMBINED = re.compile(
    r'^(\S+) \S+ \S+ \[([^\]]+)\] "(\S+) (\S+)[^"]*" (\d{3}) \S+(?: "[^"]*" "([^"]*)")?'
)


def parse_log_line(line: str) -> Event | None:
    line = line.strip()
    if not line:
        return None
    if line.startswith("{"):
        try:
            d = json.loads(line)
            return Event(
                ts=float(d["ts"]),
                src=str(d["src"]),
                method=str(d.get("method", "GET")),
                path=str(d.get("path", "/")).split("?", 1)[0],
                status=int(d.get("status", 0)),
                ua=str(d.get("ua", "")),
            )
        except (ValueError, KeyError, TypeError):
            return None
    m = _COMBINED.match(line)
    if not m:
        return None
    src, when, method, path, status, ua = m.groups()
    try:
        ts = datetime.strptime(when, "%d/%b/%Y:%H:%M:%S %z").timestamp()
    except ValueError:
        return None
    return Event(
        ts=ts,
        src=src,
        method=method,
        path=path.split("?", 1)[0],
        status=int(status),
        ua=ua or "",
    )


def read_log(path: str) -> Iterator[Event]:
    with open(path, "r", errors="replace") as fh:
        for line in fh:
            ev = parse_log_line(line)
            if ev:
                yield ev


def follow_log(path: str, poll: float = 0.25) -> Iterator[Event]:
    """Tail a log file forever, surviving rotation.

    Events are stamped with the time they are read, not the time written in the log
    line, so every live sensor shares one clock and a malformed or forged timestamp
    cannot disturb the detection windows.
    """
    fh = open(path, "r", errors="replace")
    fh.seek(0, os.SEEK_END)
    inode = os.fstat(fh.fileno()).st_ino
    while True:
        line = fh.readline()
        if line:
            ev = parse_log_line(line)
            if ev:
                ev.ts = time.time()
                yield ev
            continue
        time.sleep(poll)
        try:
            st = os.stat(path)
        except FileNotFoundError:
            continue
        if st.st_ino != inode or st.st_size < fh.tell():
            fh.close()
            fh = open(path, "r", errors="replace")
            inode = os.fstat(fh.fileno()).st_ino


def parse_frame(frame: bytes, now: float) -> Event | None:
    """Return a conn Event for a TCP SYN (connection attempt) in an Ethernet frame."""
    if len(frame) < 34:
        return None
    ethertype = struct.unpack_from("!H", frame, 12)[0]
    off = 14
    if ethertype == 0x8100 and len(frame) >= 38:  # 802.1Q tag
        ethertype = struct.unpack_from("!H", frame, 16)[0]
        off = 18
    if ethertype == 0x0800:
        ihl = (frame[off] & 0x0F) * 4
        if frame[off + 9] != 6:
            return None
        src = socket.inet_ntop(socket.AF_INET, frame[off + 12 : off + 16])
        tcp = off + ihl
    elif ethertype == 0x86DD:
        if len(frame) < off + 40 or frame[off + 6] != 6:
            return None
        src = socket.inet_ntop(socket.AF_INET6, frame[off + 8 : off + 24])
        tcp = off + 40
    else:
        return None
    if len(frame) < tcp + 14:
        return None
    dport = struct.unpack_from("!H", frame, tcp + 2)[0]
    flags = frame[tcp + 13]
    if flags & 0x02 and not flags & 0x10:  # SYN without ACK
        return Event(ts=now, src=src, kind="conn", dport=dport)
    return None


def sniff(iface: str) -> Iterator[Event]:
    """Yield inbound connection attempts seen on a network interface (Linux, root)."""
    sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(0x0003))
    sock.bind((iface, 0))
    try:
        while True:
            frame, addr = sock.recvfrom(65535)
            if addr[2] == socket.PACKET_OUTGOING:
                continue
            ev = parse_frame(frame, time.time())
            if ev:
                yield ev
    finally:
        sock.close()
