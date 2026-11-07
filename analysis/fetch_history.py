#!/usr/bin/env python3
"""Download and check NO LIMIT '26 hand histories. GET requests only, standard library only.

  python3 fetch_history.py list                      rounds, status, our tables and points
  python3 fetch_history.py selftest                  auth, listing, hands route, build machine
  python3 fetch_history.py download [ROUND] [--wait] [--copy-to-build]
  python3 fetch_history.py validate FILE             stream a file through the kit reader logic

ROUND: new (default: newest completed round not yet in --out-dir), latest (newest completed),
R<n> or <n> (n-th round in creation order, any kind), T<n> (n-th scored round), or a
tournament id or id prefix. Downloads never overwrite: each goes to a new file.
The API key is read from ~/.config/no-limit-2026/api-key and only sent to the site's host.
"""

import argparse
import datetime as dt
import gzip
import http.client
import json
import os
import re
import shlex
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zlib
from pathlib import Path

DEFAULT_API = "https://pokerbot.sequoiacap.com/tournament/api"
DEFAULT_KEY_FILE = Path.home() / ".config" / "no-limit-2026" / "api-key"
DEFAULT_OUT_DIR = Path(__file__).resolve().parent / "hand-histories"
HANDS_ROUTE = "/teams/{team}/tournaments/{tournament}/hands"
BUILD_HOST = "no-limit-2026-build"
BUILD_DIR = "work/analysis/hand-histories"
BUILD_KIT_PYTHON = "work/starter-kit/.venv/bin/python"
BUILD_KIT_READER = "work/starter-kit/hand-history/read.py"
SSH_OPTIONS = ["-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=accept-new", "-o", "ConnectTimeout=15"]
ZERO_UUID = "00000000-0000-0000-0000-000000000000"
UNKNOWN_ROUTE_MESSAGE = "The request cannot be served."
NOT_READY_STATUSES = {404, 409, 423, 425, 503}
REDIRECT_STATUSES = {301, 302, 303, 307, 308}
CHUNK_BYTES = 1 << 20
JSON_LINK_LIMIT_BYTES = 5 << 20
DOWNLOAD_ACCEPT = "application/gzip, application/x-gzip, application/x-ndjson, application/octet-stream, application/json;q=0.5, */*;q=0.1"

EXIT_FAILURE, EXIT_CONFIG, EXIT_NOT_READY, EXIT_INVALID, EXIT_UNEXPECTED = 1, 2, 3, 4, 5


class ApiError(Exception):
    def __init__(self, status, code, message, url):
        super().__init__(f"HTTP {status} {code}: {message}")
        self.status, self.code, self.message, self.url = status, code, message, url


class NotReady(Exception):
    pass


class UnexpectedResponse(Exception):
    pass


class Fatal(Exception):
    def __init__(self, message, exit_code=EXIT_FAILURE):
        super().__init__(message)
        self.exit_code = exit_code


class Transient(Fatal):
    pass


class RefuseRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


OPENER = urllib.request.build_opener(RefuseRedirects)


def say(message=""):
    print(message, flush=True)


def note(message):
    print(message, file=sys.stderr, flush=True)


class Api:
    def __init__(self, base, key):
        self.base = base.rstrip("/")
        self.key = key
        split = urllib.parse.urlsplit(self.base)
        self.origin = (split.scheme, split.netloc)

    def open(self, url, accept="application/json", timeout=60):
        for _ in range(6):
            split = urllib.parse.urlsplit(url)
            headers = {"Accept": accept, "User-Agent": "no-limit-fetch-history/1"}
            if (split.scheme, split.netloc) == self.origin:
                headers["Authorization"] = f"Bearer {self.key}"
            request = urllib.request.Request(url, headers=headers, method="GET")
            try:
                return OPENER.open(request, timeout=timeout)
            except urllib.error.HTTPError as error:
                location = error.headers.get("Location")
                if error.code in REDIRECT_STATUSES and location:
                    error.close()
                    url = urllib.parse.urljoin(url, location)
                    continue
                raise api_error(error, url) from None
            except urllib.error.URLError as error:
                raise Transient(f"Cannot reach {split.netloc}: {error.reason}") from None
            except (OSError, http.client.HTTPException) as error:
                raise Transient(f"Connection to {split.netloc} failed: {error}") from None
        raise Fatal(f"Too many redirects starting from {url}")

    def get_json(self, path):
        with self.open(self.base + path) as response:
            try:
                body = response.read()
            except (OSError, http.client.HTTPException) as error:
                raise Transient(f"Reading {path} failed: {error}") from None
        return json.loads(body.decode("utf-8"))


def api_error(error, url):
    try:
        body = error.read(65536).decode("utf-8", "replace")
    finally:
        error.close()
    code, message = "http_error", body.strip()[:300] or error.reason
    try:
        parsed = json.loads(body)
        code, message = parsed.get("code", code), parsed.get("message", message)
    except (ValueError, AttributeError):
        pass
    return ApiError(error.code, code, message, url)


def read_key(path):
    try:
        key = path.read_text().strip().splitlines()[0].strip()
    except FileNotFoundError:
        raise Fatal(f"No API key at {path}. The key lives on the Mac; run downloads there "
                    f"(validate works anywhere).", EXIT_CONFIG) from None
    except IndexError:
        raise Fatal(f"API key file {path} is empty.", EXIT_CONFIG) from None
    return key


def team_context(api, wanted):
    try:
        info = api.get_json("/auth/api-key")
    except ApiError as error:
        if error.status == 401:
            raise Fatal("The API key was rejected (401). Make a new one at "
                        "https://pokerbot.sequoiacap.com/tournament#settings/api-keys", EXIT_CONFIG) from None
        raise
    teams = info.get("teams") or []
    if wanted:
        teams = [t for t in teams if wanted in (t.get("team_id"), t.get("team_name"))]
    if not teams:
        raise Fatal("This API key belongs to no matching team.", EXIT_CONFIG)
    if len(teams) > 1:
        names = ", ".join(f"{t.get('team_name')} ({t.get('team_id')})" for t in teams)
        raise Fatal(f"Several teams; pick one with --team: {names}", EXIT_CONFIG)
    return teams[0]


def fetch_rounds(api, competition_id):
    items = api.get_json(f"/competitions/{competition_id}/tournaments").get("items", [])
    items.sort(key=lambda r: (r.get("created_at") or "", r.get("id") or ""))
    scored = practice = 0
    for row, item in enumerate(items, 1):
        item["_row"] = row
        if item.get("kind") == "scored":
            scored += 1
            item["_label"] = f"R{row}/T{scored}"
            item["_scored_number"] = scored
        else:
            practice += 1
            item["_label"] = f"R{row}/practice{practice}"
    return items


def round_status(item):
    if item.get("cancelled_at"):
        return "cancelled"
    if item.get("completed_at"):
        return "completed"
    return "running"


def round_progress(item):
    jobs = item.get("jobs") or 0
    return f"{item.get('jobs_done', 0)}/{jobs} blocks" if jobs else "not started"


def fetch_our_result(api, tournament_id, team_id):
    for suffix in ("?public=true", ""):
        try:
            results = api.get_json(f"/tournaments/{tournament_id}/results{suffix}")
        except ApiError:
            continue
        mine = next((r for r in results.get("items", []) if r.get("team_id") == team_id), None)
        return results.get("status"), mine
    return None, None


def local_time(stamp):
    if not stamp:
        return "-"
    moment = dt.datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    return moment.astimezone().strftime("%H:%M:%S")


def file_tag(item):
    kind = "T%d" % item["_scored_number"] if item.get("kind") == "scored" else item.get("kind", "round")
    return f"R{item['_row']}-{kind}-w{item.get('weight', 0)}"


def existing_downloads(out_dir, tournament_id):
    if not out_dir.is_dir():
        return []
    return sorted(p for p in out_dir.iterdir()
                  if tournament_id in p.name and p.name.endswith((".jsonl.gz", ".jsonl")))


def pick_round(items, selector, out_dir):
    completed = [r for r in items if round_status(r) == "completed"]
    selector = (selector or "new").strip()
    lowered = selector.lower()
    if lowered == "new":
        fresh = [r for r in completed if not existing_downloads(out_dir, r["id"])]
        return fresh[-1] if fresh else None
    if lowered == "latest":
        return completed[-1] if completed else None
    match = re.fullmatch(r"(?:r|#)?(\d+)", lowered)
    if match:
        row = int(match.group(1))
        return next((r for r in items if r["_row"] == row), None)
    match = re.fullmatch(r"t(\d+)", lowered)
    if match:
        number = int(match.group(1))
        return next((r for r in items if r.get("_scored_number") == number), None)
    if re.fullmatch(r"[0-9a-f-]{4,36}", lowered):
        found = [r for r in items if r["id"].startswith(lowered)]
        if len(found) > 1:
            raise Fatal(f"Id prefix {selector} matches several rounds.", EXIT_CONFIG)
        return found[0] if found else None
    raise Fatal(f"Unknown round selector {selector!r}. Use new, latest, R<n>, T<n> or an id.", EXIT_CONFIG)


def cmd_list(api, args):
    team = team_context(api, args.team)
    competition_id, team_id = team["competition_id"], team["team_id"]
    say(f"Team {team.get('team_name')} ({team_id}), competition {team.get('competition_name')} ({competition_id})")
    try:
        clock = (api.get_json(f"/competitions/{competition_id}/redzone") or {}).get("clock") or {}
        if clock:
            say(f"Clock: {clock.get('label')} ({clock.get('state')}), ends {local_time(clock.get('ends_at'))} local")
    except (ApiError, ValueError):
        pass
    items = fetch_rounds(api, competition_id)
    if not items:
        say("No rounds yet: the competition lists no tournaments.")
        return 0
    say(f"{'round':<16} {'status':<10} {'progress':<16} {'created':>8} {'completed':>9} "
        f"{'results':<10} {'our tables':>10} {'our avg pts':>11}  {'downloaded':<10} id")
    for item in items:
        results_status, mine = fetch_our_result(api, item["id"], team_id)
        tables = mine.get("tables") if mine else None
        points = mine.get("average_points") if mine else None
        have = "yes" if existing_downloads(args.out_dir, item["id"]) else "no"
        say(f"{item['_label']:<16} {round_status(item):<10} {round_progress(item):<16} "
            f"{local_time(item.get('created_at')):>8} {local_time(item.get('completed_at')):>9} "
            f"{results_status or '-':<10} {'-' if tables is None else tables:>10} "
            f"{'-' if points is None else round(points, 3):>11}  {have:<10} {item['id']}")
    return 0


def cmd_selftest(api, args):
    team = team_context(api, args.team)
    say(f"OK   auth: key accepted for team {team.get('team_name')} ({team['team_id']})")
    items = fetch_rounds(api, team["competition_id"])
    states = ", ".join(f"{r['_label']} {round_status(r)}" for r in items) or "none yet"
    say(f"OK   listing: {len(items)} round(s): {states}")
    probe = api.base + HANDS_ROUTE.format(team=team["team_id"], tournament=ZERO_UUID)
    try:
        api.open(probe).close()
        say("??   hands route answered 200 for a dummy round; unexpected but the route exists")
    except ApiError as error:
        if error.message == UNKNOWN_ROUTE_MESSAGE:
            say(f"FAIL hands route: the API no longer knows {HANDS_ROUTE}; use the browser download")
            return EXIT_UNEXPECTED
        if error.status == 404:
            say(f"OK   hands route exists: GET {HANDS_ROUTE} -> 404 '{error.message}' for a dummy round")
        else:
            say(f"??   hands route: HTTP {error.status} {error.code}: {error.message}")
    mode = args.key_file.stat().st_mode & 0o777
    if mode & 0o077:
        say(f"WARN key file {args.key_file} is mode {oct(mode)}; chmod 600 recommended")
    if args.check_build:
        command = f"test -x {BUILD_KIT_PYTHON} && test -f {BUILD_KIT_READER} && echo kit-reader-ok"
        result = subprocess.run(["ssh", *SSH_OPTIONS, BUILD_HOST, command], capture_output=True, text=True)
        if "kit-reader-ok" in result.stdout:
            say(f"OK   build machine reachable, kit reader at ~/{BUILD_KIT_READER}")
        else:
            say(f"WARN build machine check failed: {(result.stderr or result.stdout).strip()[:200]}")
    return 0


def find_link(data):
    if isinstance(data, str) and data.startswith(("http://", "https://", "/")):
        return data
    if isinstance(data, dict):
        for key in ("url", "download_url", "download", "href", "link", "hands", "history"):
            value = data.get(key)
            if isinstance(value, str) and value.startswith(("http://", "https://", "/")):
                return value
        for key in ("links", "data", "file"):
            found = find_link(data.get(key))
            if found:
                return found
    return None


def stream_to_part(response, part_path):
    expected = response.headers.get("Content-Length")
    expected = int(expected) if expected and expected.isdigit() else None
    received, last_report = 0, time.monotonic()
    descriptor = os.open(part_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(descriptor, "wb") as sink:
        while True:
            chunk = response.read(CHUNK_BYTES)
            if not chunk:
                break
            sink.write(chunk)
            received += len(chunk)
            if time.monotonic() - last_report > 5:
                total = f" of {expected / 1e6:.1f}" if expected else ""
                note(f"  ... {received / 1e6:.1f}{total} MB")
                last_report = time.monotonic()
    if expected is not None and received != expected:
        raise Transient(f"Download truncated: got {received} of {expected} bytes")
    return received


def stream_or_discard(response, part_path):
    try:
        return stream_to_part(response, part_path)
    except (OSError, http.client.HTTPException, Transient) as error:
        part_path.unlink(missing_ok=True)
        if isinstance(error, Transient):
            raise
        raise Transient(f"Download interrupted: {error}") from None


def file_starts_with_gzip(path):
    with open(path, "rb") as source:
        return source.read(2) == b"\x1f\x8b"


def claim_final_name(part_path, out_dir, stem, suffix):
    for attempt in range(1, 1000):
        candidate = out_dir / (f"{stem}{suffix}" if attempt == 1 else f"{stem}-{attempt}{suffix}")
        try:
            os.link(part_path, candidate)
        except FileExistsError:
            continue
        os.unlink(part_path)
        return candidate
    raise Fatal(f"Could not find a free file name for {stem} in {out_dir}")


def download_hands(api, team_id, item, out_dir):
    url = api.base + HANDS_ROUTE.format(team=team_id, tournament=item["id"])
    try:
        response = api.open(url, accept=DOWNLOAD_ACCEPT, timeout=120)
    except ApiError as error:
        if error.message == UNKNOWN_ROUTE_MESSAGE:
            raise Fatal(f"The API does not know {HANDS_ROUTE} (route changed?). Fallback: download it from "
                        f"the team page in the browser, then run: validate FILE", EXIT_UNEXPECTED) from None
        if error.status in NOT_READY_STATUSES:
            raise NotReady(f"no hand history yet (HTTP {error.status} {error.code}: {error.message})") from None
        if error.status in (401, 403):
            raise Fatal(f"Not allowed to download: HTTP {error.status} {error.code}: {error.message}", EXIT_CONFIG) from None
        raise
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"hands-{file_tag(item)}-{item['id']}"
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    part_path = out_dir / f".{stem}.{stamp}.{os.getpid()}.part"
    with response:
        content_type = response.headers.get_content_type()
        content_encoding = response.headers.get("Content-Encoding", "-")
        note(f"  GET {response.geturl()} -> {response.status} {content_type} (encoding {content_encoding})")
        received = stream_or_discard(response, part_path)
    if content_type == "application/json" and not file_starts_with_gzip(part_path):
        link = None
        if received <= JSON_LINK_LIMIT_BYTES:
            try:
                link = find_link(json.loads(part_path.read_text(encoding="utf-8")))
            except ValueError:
                link = None
        if not link:
            saved = claim_final_name(part_path, out_dir, stem + "-response", ".json")
            raise UnexpectedResponse(f"The hands route returned JSON, not a hand-history file. Saved it to {saved}")
        os.unlink(part_path)
        note(f"  The API answered with a link; following {urllib.parse.urlsplit(link).path}")
        with api.open(urllib.parse.urljoin(url, link), accept=DOWNLOAD_ACCEPT, timeout=120) as linked:
            note(f"  GET {linked.geturl()} -> {linked.status} {linked.headers.get_content_type()}")
            received = stream_or_discard(linked, part_path)
    suffix = ".jsonl.gz" if file_starts_with_gzip(part_path) else ".jsonl"
    final = claim_final_name(part_path, out_dir, stem, suffix)
    say(f"Saved {received / 1e6:.2f} MB to {final}")
    return final


def cmd_download(api, args):
    team = team_context(api, args.team)
    team_id, competition_id = team["team_id"], team["competition_id"]
    deadline = time.monotonic() + args.timeout * 60
    reported_waiting = None
    item = None
    while True:
        try:
            item, waiting_reason, final = attempt_download(api, args, team_id, competition_id)
        except (Transient, ApiError) as error:
            if not args.wait or (isinstance(error, ApiError) and error.status < 500 and error.status != 429):
                raise
            waiting_reason, final = f"temporary error, will retry: {error}", None
        if final is not None:
            break
        if not args.wait:
            raise Fatal(f"Not ready: {waiting_reason}. Rerun later, or add --wait to poll.", EXIT_NOT_READY)
        if time.monotonic() > deadline:
            raise Fatal(f"Gave up after {args.timeout} min: {waiting_reason}. Fallback: download it from the "
                        f"team page in the browser.", EXIT_NOT_READY)
        if waiting_reason != reported_waiting:
            note(f"[{dt.datetime.now():%H:%M:%S}] waiting: {waiting_reason}")
            reported_waiting = waiting_reason
        else:
            note(f"[{dt.datetime.now():%H:%M:%S}] still waiting ({round_progress(item) if item else 'no round'})")
        time.sleep(args.poll)
    _, mine = fetch_our_result(api, item["id"], team_id)
    expected_tables = mine.get("tables") if mine else None
    code = report_validation(final, item["id"], expected_tables)
    if args.copy_to_build:
        copy_to_build(final)
    return code


def attempt_download(api, args, team_id, competition_id):
    """Return (round, reason it is not ready or None, downloaded path or None)."""
    items = fetch_rounds(api, competition_id)
    item = pick_round(items, args.round, args.out_dir)
    if item is None:
        running = [r for r in items if round_status(r) == "running"]
        if args.round.lower() == "new" and items and not running and not args.wait:
            raise Fatal(f"Every completed round is already downloaded in {args.out_dir}; nothing new.", 0)
        wanted = "completed round" if args.round.lower() in ("new", "latest") else "round"
        running_text = ", ".join(f"{r['_label']} {round_progress(r)}" for r in running)
        return None, f"no {wanted} matches {args.round!r} yet ({'running: ' + running_text if running else 'no round running'})", None
    status = round_status(item)
    if status == "cancelled":
        raise Fatal(f"{item['_label']} ({item['id']}) was cancelled; it has no hand history.", EXIT_NOT_READY)
    if status != "completed" and not args.force:
        return item, f"{item['_label']} ({item['id']}) is still running: {round_progress(item)}", None
    if status != "completed":
        note(f"--force: trying {item['_label']} although it is {status}")
    try:
        return item, None, download_hands(api, team_id, item, args.out_dir)
    except NotReady as reason:
        return item, f"{item['_label']} is {status} but has {reason}", None


def open_history(path):
    if file_starts_with_gzip(path):
        return gzip.open(path, "rt", encoding="utf-8")
    return open(path, "rt", encoding="utf-8")


def read_header(path):
    with open_history(path) as source:
        first = source.readline()
    if not first:
        raise ValueError("Missing hand-history header.")
    return json.loads(first)


def read_history(path):
    """The starter kit's hand-history/read.py logic, choosing gzip by content instead of suffix."""
    with open_history(path) as source:
        lines = iter(source)
        try:
            header = json.loads(next(lines))
        except StopIteration as error:
            raise ValueError("Missing hand-history header.") from error
        if (
            not isinstance(header, dict)
            or not isinstance(header.get("tournament_id"), str)
            or not isinstance(header.get("you"), str)
            or not isinstance(header.get("entries"), list)
        ):
            raise ValueError("Invalid hand-history header.")
        if any(
            not isinstance(entry, dict)
            or not isinstance(entry.get("entry_id"), str)
            or not isinstance(entry.get("team_name"), str)
            for entry in header["entries"]
        ):
            raise ValueError("Invalid entry in hand-history header.")
        entries = {entry["entry_id"] for entry in header["entries"]}
        if header["you"] not in entries:
            raise ValueError("Your entry is missing from the header.")
        for line in lines:
            table = json.loads(line)
            try:
                own = json.loads(next(lines))["you"]
            except StopIteration as error:
                raise ValueError("Missing private line after public table.") from error
            if (own["iteration"], own["table"]) != (table["iteration"], table["table"]):
                raise ValueError("Public and private lines describe different tables.")
            seat = own["seat"]
            if (
                type(seat) is not int
                or not 0 <= seat < len(table["seats"])
                or table["seats"][seat] != header["you"]
            ):
                raise ValueError("Private seat does not match your entry.")
            if (
                not isinstance(table["fillers"], list)
                or len(table["fillers"]) != len(table["seats"])
                or any(type(filler) is not bool for filler in table["fillers"])
                or any(entry not in entries for entry in table["seats"])
            ):
                raise ValueError("Invalid table seats or filler flags.")
            if (
                not isinstance(own["cards"], list)
                or len(own["cards"]) != len(table["hands"])
                or any(
                    not isinstance(cards, list) or any(not isinstance(c, str) for c in cards)
                    for cards in own["cards"]
                )
            ):
                raise ValueError("Own cards do not align with the table's hands.")
            hands = {hand["hand"]: hand for hand in table["hands"]}
            if len(hands) != len(table["hands"]):
                raise ValueError("Duplicate hand number in table.")
            if not isinstance(own["automatic"], list):
                raise ValueError("Invalid automatic action references.")
            for reference in own["automatic"]:
                if (
                    not isinstance(reference, list)
                    or len(reference) != 2
                    or any(type(index) is not int for index in reference)
                ):
                    raise ValueError("Invalid automatic action reference.")
                hand_number, index = reference
                hand = hands.get(hand_number)
                if (
                    hand is None
                    or not 0 <= index < len(hand["events"])
                    or hand["events"][index].get("seat") != seat
                ):
                    raise ValueError("Automatic action does not refer to your seat's event.")
            yield header, table, own


def count_gzip_members(path):
    members, decompressor, pending = 0, None, b""
    with open(path, "rb") as source:
        while True:
            chunk = pending or source.read(CHUNK_BYTES)
            pending = b""
            if not chunk:
                break
            if decompressor is None:
                if not chunk.strip(b"\x00"):
                    continue
                decompressor = zlib.decompressobj(16 + zlib.MAX_WBITS)
                members += 1
            decompressor.decompress(chunk)
            if decompressor.eof:
                pending, decompressor = decompressor.unused_data, None
    if decompressor is not None:
        raise ValueError(f"gzip member {members} is unfinished (file truncated)")
    return members


def summarize(path):
    header = read_header(path)
    stats = {
        "first_line_keys": sorted(header) if isinstance(header, dict) else None,
        "tournament_id": header.get("tournament_id") if isinstance(header, dict) else None,
        "you": header.get("you") if isinstance(header, dict) else None,
        "entries": len(header.get("entries", [])) if isinstance(header, dict) else None,
        "tables": 0, "hands": 0, "tables_as_filler": 0, "automatic_actions": 0,
        "private_events": 0, "iterations": set(), "variants": set(),
    }
    for _, table, own in read_history(path):
        stats["tables"] += 1
        stats["hands"] += len(table["hands"])
        stats["tables_as_filler"] += bool(table["fillers"][own["seat"]])
        stats["automatic_actions"] += len(own["automatic"])
        stats["private_events"] += len(own.get("private_events") or [])
        stats["iterations"].add(table["iteration"])
        if table.get("variant"):
            stats["variants"].add(table["variant"])
    return stats


def report_validation(path, expected_tournament=None, expected_tables=None):
    path = Path(path)
    say(f"Validating {path} ({path.stat().st_size / 1e6:.2f} MB)")
    try:
        if file_starts_with_gzip(path):
            say(f"  gzip members: {count_gzip_members(path)} (concatenated members are read as one stream)")
        else:
            say("  not gzip-compressed: reading as plain JSON lines")
        stats = summarize(path)
    except (ValueError, KeyError, TypeError, OSError, EOFError, zlib.error) as error:
        say(f"INVALID: {type(error).__name__}: {error}")
        return EXIT_INVALID
    say(f"  first line keys: {', '.join(stats['first_line_keys'])}")
    say(f"  tournament_id {stats['tournament_id']}, you {stats['you']}, {stats['entries']} entries")
    iterations = stats["iterations"]
    span = f"{min(iterations)}..{max(iterations)}" if iterations else "-"
    say(f"  tables {stats['tables']} (iterations {span}), hands {stats['hands']}, "
        f"tables where our seat is a filler {stats['tables_as_filler']}")
    say(f"  our automatic (failed-decision) actions {stats['automatic_actions']}, "
        f"private events {stats['private_events']}, variants {', '.join(sorted(stats['variants'])) or '-'}")
    problems = []
    if expected_tournament and stats["tournament_id"] != expected_tournament:
        problems.append(f"header tournament_id {stats['tournament_id']} differs from requested {expected_tournament}")
    if expected_tables is not None:
        verdict = "matches" if expected_tables == stats["tables"] else "DIFFERS from"
        say(f"  table count {verdict} the results page ({expected_tables} tables for our team)")
        if expected_tables != stats["tables"]:
            problems.append("table count differs from results; the file may be truncated or results count differently")
    if stats["tables"] == 0:
        problems.append("the file has a header but no tables")
    for problem in problems:
        say(f"WARNING: {problem}")
    say("VALID: header and every public/private pair passed the kit reader checks")
    return 0


def copy_to_build(local):
    remote = f"{BUILD_DIR}/{local.name}"
    quoted = shlex.quote(remote)
    prepare = f"mkdir -p {shlex.quote(BUILD_DIR)} && test ! -e {quoted} && test ! -e {quoted}.part"
    if subprocess.run(["ssh", *SSH_OPTIONS, BUILD_HOST, prepare]).returncode != 0:
        say(f"Not copied: ~/{remote} already exists on the build machine (or ssh failed).")
        return
    if subprocess.run(["scp", "-q", *SSH_OPTIONS, str(local), f"{BUILD_HOST}:{remote}.part"]).returncode != 0:
        say("Copy to the build machine failed.")
        return
    check = (f"mv -n {quoted}.part {quoted} && test ! -e {quoted}.part && "
             f"bash -o pipefail -c {shlex.quote(f'{BUILD_KIT_PYTHON} -I {BUILD_KIT_READER} {remote} | wc -l')}")
    result = subprocess.run(["ssh", *SSH_OPTIONS, BUILD_HOST, check], capture_output=True, text=True)
    if result.returncode == 0:
        say(f"Copied to {BUILD_HOST}:~/{remote}; the kit's read.py there read {result.stdout.strip()} tables")
    else:
        say(f"Copied to {BUILD_HOST}:~/{remote}, but the kit reader failed: {result.stderr.strip()[-400:]}")


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--key-file", type=Path, default=DEFAULT_KEY_FILE)
    parser.add_argument("--team", help="team id or name, only needed if the key has several teams")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR, help=f"default {DEFAULT_OUT_DIR}")
    parser.add_argument("--api", default=DEFAULT_API, help=argparse.SUPPRESS)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list", help="list rounds with status, our tables and points")
    selftest = commands.add_parser("selftest", help="check auth, listing and the hands route")
    selftest.add_argument("--check-build", action="store_true", help="also check ssh and the kit reader")
    download = commands.add_parser("download", help="download one round's hand history")
    download.add_argument("round", nargs="?", default="new")
    download.add_argument("--wait", action="store_true", help="poll until the round finishes and the file exists")
    download.add_argument("--poll", type=float, default=30, help="seconds between polls (default 30)")
    download.add_argument("--timeout", type=float, default=120, help="minutes to keep waiting (default 120)")
    download.add_argument("--force", action="store_true", help="try the download even if the round is not completed")
    download.add_argument("--copy-to-build", action="store_true",
                          help=f"scp to {BUILD_HOST}:~/{BUILD_DIR}/ and run the kit's read.py there")
    validate = commands.add_parser("validate", help="validate a downloaded file")
    validate.add_argument("path", type=Path)
    validate.add_argument("--expect-tournament")
    validate.add_argument("--expect-tables", type=int)
    return parser


def main():
    args = build_parser().parse_args()
    try:
        if args.command == "validate":
            return report_validation(args.path, args.expect_tournament, args.expect_tables)
        api = Api(args.api, read_key(args.key_file))
        handlers = {"list": cmd_list, "selftest": cmd_selftest, "download": cmd_download}
        return handlers[args.command](api, args)
    except Fatal as error:
        say(f"{'ERROR: ' if error.exit_code else ''}{error}")
        return error.exit_code
    except UnexpectedResponse as error:
        say(f"ERROR: {error}")
        return EXIT_UNEXPECTED
    except ApiError as error:
        say(f"ERROR: {error} ({urllib.parse.urlsplit(error.url).path})")
        return EXIT_FAILURE
    except KeyboardInterrupt:
        say("Stopped.")
        return 130


if __name__ == "__main__":
    sys.exit(main())
