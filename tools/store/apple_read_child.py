"""Bounded read commands with exact child identities and retained cleanup evidence."""
import os
from contextlib import contextmanager
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import time

from apple_host_busy import parse_processes


def clock():
    return time.clock_gettime(time.CLOCK_MONOTONIC)


def table(deadline, timeout=2):
    remaining = deadline - clock()
    if remaining <= 0:
        raise TimeoutError("Read cleanup deadline")
    column = "ucomm=" if sys.platform == "darwin" else "comm="
    try:
        value = subprocess.check_output(["ps", "-axo", "pid=,ppid=,pgid=,lstart=," + column],
                                        text=True, timeout=min(timeout, remaining))
    except subprocess.TimeoutExpired as exc:
        raise TimeoutError("Process inspection deadline") from exc
    return parse_processes(value)


def same(a, b):
    return all(a[k] == b[k] for k in ("pid", "started"))


@contextmanager
def defer_cancellation(deliver=True):
    """Keep the child handle owned before cancellation; finish bounded cleanup."""
    pending = []
    def defer(sig, frame):
        if not pending: pending.append((sig, frame))
    previous = {}
    try:
        for sig in (signal.SIGALRM, signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
            previous[sig] = signal.signal(sig, defer)
        yield
    finally:
        for sig, handler in previous.items(): signal.signal(sig, handler)
        if deliver and pending:
            sig, frame = pending[0]
            handler = previous[sig]
            if callable(handler): handler(sig, frame)
            elif handler != signal.SIG_IGN:
                raise TimeoutError("Read cancelled at child creation")


class ReadCommands:
    def __init__(self, deadline, reserve=15, maximum=2_000_000,
                 inspection_timeout=2, observation_interval=0):
        self.deadline, self.reserve, self.maximum = deadline, reserve, maximum
        self.inspection_timeout, self.observation_interval = inspection_timeout, observation_interval
        self.records = []

    def process_table(self):
        return table(min(self.deadline, getattr(self, '_phase_deadline', self.deadline)),
                     self.inspection_timeout)

    def observe(self, record, child):
        child.poll()
        rows = self.process_table()
        known = record["identities"]
        parents = {int(k) for k, v in known.items() if int(k) in rows and same(v, rows[int(k)])}
        parents.add(child.pid)
        changed = True
        while changed:
            changed = False
            for pid, row in rows.items():
                if (row["ppid"] in parents or row["pgid"] == child.pid) and pid not in parents:
                    parents.add(pid); changed = True
        for pid in parents:
            if pid in rows:
                if str(pid) in known and not same(known[str(pid)], rows[pid]):
                    raise RuntimeError("Read child PID reused; incomplete")
                known[str(pid)] = rows[pid]
        return [row for pid, row in rows.items()
                if (str(pid) in known and same(known[str(pid)], row)) or row["pgid"] == child.pid]

    def clear(self, record, child):
        for sig, grace in ((signal.SIGTERM, 4), (signal.SIGKILL, 3)):
            live = self.observe(record, child)
            if not live:
                record["children_absent"] = True
                return
            # Descendants first; allow their parent to reap them before its signal.
            for row in sorted(live, key=lambda x: x["pid"] == child.pid):
                fresh = self.process_table().get(row["pid"])
                if fresh and same(row, fresh):
                    try: os.kill(row["pid"], sig)
                    except ProcessLookupError: pass
                if row["pid"] != child.pid: time.sleep(.05)
            until = min(self.deadline, clock() + grace)
            while clock() < until:
                if not self.observe(record, child):
                    record["children_absent"] = True
                    return
                time.sleep(.1)
        raise RuntimeError("Read descendants not proven absent")

    def run(self, argv, limit=8, env=None, input_data=None):
        end = min(self.deadline - self.reserve, clock() + limit)
        if end <= clock(): raise TimeoutError("Read command budget exhausted")
        record = {"command": Path(argv[0]).name, "identities": {}, "complete": False,
                  "children_absent": False}
        self.records.append(record)
        child = None
        buffers = {"stdout": bytearray(), "stderr": bytearray()}
        selector = None
        sent = 0
        self._phase_deadline = end
        next_observation = 0
        try:
            # Cancellation must not escape between fork/exec and owning Popen.
            with defer_cancellation():
                child = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                         stdin=subprocess.PIPE if input_data is not None else subprocess.DEVNULL,
                                         env=env, start_new_session=True)
                record["pid"] = child.pid
            selector = selectors.DefaultSelector()
            for name in buffers:
                pipe = getattr(child, name); os.set_blocking(pipe.fileno(), False)
                selector.register(pipe, selectors.EVENT_READ, name)
            if input_data is not None:
                os.set_blocking(child.stdin.fileno(), False)
                selector.register(child.stdin, selectors.EVENT_WRITE, "stdin")
            while selector.get_map() or child.poll() is None:
                # A second ps can appear in the first snapshot as a transient
                # pre-exec Python child on Darwin. Do not observe the observer
                # concurrently. The same bounded exact cleanup still runs below.
                if Path(argv[0]).name != "ps" and clock() >= next_observation:
                    self.observe(record, child)
                    next_observation = clock() + self.observation_interval
                remaining = end - clock()
                if remaining <= 0: raise TimeoutError("Read command timed out")
                for key, _ in selector.select(min(.1, remaining)):
                    if key.data == "stdin":
                        if sent == len(input_data):
                            selector.unregister(key.fileobj); key.fileobj.close()
                        else:
                            sent += os.write(key.fd, input_data[sent:sent + 16384])
                        continue
                    chunk = os.read(key.fd, 16384)
                    if not chunk:
                        selector.unregister(key.fileobj); key.fileobj.close()
                    else:
                        buffers[key.data].extend(chunk)
                        if sum(map(len, buffers.values())) > self.maximum:
                            raise RuntimeError("Read output limit exceeded")
            record["exit"] = child.wait(timeout=max(.01, min(1, self.deadline-clock())))
            return {"exit": record["exit"], **{k: v.decode(errors="replace") for k, v in buffers.items()}}
        finally:
            # Repeated TERM/INT/HUP must not interrupt exact reaping. All loops
            # retain the original monotonic deadline; no extra grace is added.
            with defer_cancellation(deliver=False):
                self._phase_deadline = self.deadline
                if child is not None:
                    try:
                        self.clear(record, child)
                        child.wait(timeout=max(.01, min(1, self.deadline-clock())))
                        record["complete"] = True
                    finally:
                        if selector is not None: selector.close()
                        for pipe in (child.stdin, child.stdout, child.stderr):
                            if pipe is not None: pipe.close()


def global_environment():
    result = dict(os.environ)
    result.pop("DEVELOPER_DIR", None)
    return result
