#!/usr/bin/env python
"""Automate the Conversation Lab front-end flow via HTTP requests.

Example:
    PYTHONPATH=backend pvenv/bin/python backend/scripts/conversation_lab_e2e.py \
        --base-url http://127.0.0.1:5000 \
        --file test.csv \
        --prompt "What do you know about Alice?"
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import requests


def start_session(session: requests.Session, base_url: str) -> dict:
    resp = session.post(f"{base_url}/api/labs/conversation/session")
    data = resp.json()
    if not resp.ok or data.get("error"):
        raise RuntimeError(f"Session init failed: {data.get('error')}")
    return data


def upload_file(
    session: requests.Session,
    base_url: str,
    file_path: Path,
    description: str,
) -> dict:
    with file_path.open("rb") as handle:
        files = {"file": (file_path.name, handle)}
        data = {"description": description}
        resp = session.post(
            f"{base_url}/api/labs/conversation/ingest",
            files=files,
            data=data,
        )
    payload = resp.json()
    if not resp.ok or payload.get("ok") is False:
        raise RuntimeError(payload.get("error") or "Upload failed")
    return payload


def poll_until_ready(session: requests.Session, base_url: str, timeout: int = 180) -> dict:
    end = time.time() + timeout
    while time.time() < end:
        resp = session.get(f"{base_url}/api/labs/conversation/uploads")
        payload = resp.json()
        items = payload.get("items") or []
        if items and items[0].get("status") == "ready":
            return items[0]
        time.sleep(3)
    raise TimeoutError("Upload did not reach ready status within timeout")


def send_prompt(session: requests.Session, base_url: str, prompt: str) -> str:
    resp = session.post(
        f"{base_url}/api/labs/conversation/chat",
        json={"message": prompt},
    )
    payload = resp.json()
    if not resp.ok or payload.get("error"):
        raise RuntimeError(payload.get("error") or "Chat failed")
    return payload.get("reply", "")


def main() -> None:
    parser = argparse.ArgumentParser(description="Automate Conversation Lab upload + chat")
    parser.add_argument("--base-url", default="http://127.0.0.1:5000", help="Flask server base URL")
    parser.add_argument("--file", required=True, help="Path to file to upload")
    parser.add_argument("--description", default="Automated upload", help="File description")
    parser.add_argument("--prompt", default="What do you know about Alice?", help="Chat prompt to send")
    parser.add_argument("--timeout", type=int, default=180, help="Seconds to wait for processing")
    args = parser.parse_args()

    file_path = Path(args.file)
    if not file_path.exists():
        raise SystemExit(f"File not found: {file_path}")

    session = requests.Session()

    try:
        session_info = start_session(session, args.base_url)
        print(f"Session started: {session_info.get('sessionId')}")
        upload_payload = upload_file(session, args.base_url, file_path, args.description)
        print(f"Upload accepted: {upload_payload.get('count')} items")
        ready_job = poll_until_ready(session, args.base_url, args.timeout)
        print(f"Job ready: {ready_job.get('filename')} -> {ready_job.get('status')}" )
        reply = send_prompt(session, args.base_url, args.prompt)
        print("\nModel reply:\n" + reply)
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
