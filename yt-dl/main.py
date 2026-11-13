import signal
import subprocess
import time
import threading
from pathlib import Path

STREAMER_LIST_FILE = "streamers.txt"
RETRY_INTERVAL = 600  # seconds between retries after failure
POLL_INTERVAL = 5     # seconds between streamers.txt checks

active_monitors = {}  # url -> {"thread": Thread, "stop_event": Event, "proc": Popen|None}
lock = threading.Lock()


def remux_for_davinci(source_path):
    source = Path(source_path)
    output = source.with_name(f"{source.stem}.davinci.mp4")
    print(f"[convert] Creating {output}...")
    result = subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i", str(source),
            "-map", "0:v:0",
            "-map", "0:a:0?",
            "-c", "copy",
            "-movflags", "+faststart",
            str(output),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode == 0:
        print(f"[convert] Ready for DaVinci: {output}")
    else:
        print(f"[convert] Failed for {source}: {result.stderr.strip()}")


def read_streamer_list(filepath):
    try:
        with open(filepath, 'r') as f:
            return {line.strip() for line in f if line.strip()}
    except FileNotFoundError:
        return set()


def monitor_stream(url, stop_event):
    while not stop_event.is_set():
        print(f"[{url}] Attempting to download...")
        try:
            proc = subprocess.Popen(
                [
                    "./yt-dlp",
                    "--hls-use-mpegts",
                    "--no-part",
                    "--print", "after_move:filepath",
                    url,
                ],
                stdout=subprocess.PIPE,
                text=True,
                stderr=subprocess.DEVNULL,
            )
            with lock:
                if url in active_monitors:
                    active_monitors[url]["proc"] = proc
            proc.wait()

            if proc.returncode == 0:
                print(f"[{url}] Download finished.")
                output_path = proc.stdout.read().strip() if proc.stdout else ""
                if output_path:
                    remux_for_davinci(output_path)
                continue
            else:
                print(f"[{url}] Download failed. Retrying in {RETRY_INTERVAL}s...")
        except Exception as e:
            print(f"[{url}] Error: {e}")

        if stop_event.is_set():
            return

        for _ in range(RETRY_INTERVAL):
            if stop_event.is_set():
                return
            time.sleep(1)


def start_monitor(url):
    stop_event = threading.Event()
    t = threading.Thread(target=monitor_stream, args=(url, stop_event), daemon=True)
    with lock:
        active_monitors[url] = {"thread": t, "stop_event": stop_event, "proc": None}
    t.start()
    print(f"[+] Started monitoring: {url}")


def stop_monitor(url):
    with lock:
        monitor = active_monitors.pop(url, None)
    if monitor:
        monitor["stop_event"].set()
        proc = monitor["proc"]
        if proc and proc.poll() is None:
            print(f"[*] Sending SIGINT to yt-dlp for {url}...")
            proc.send_signal(signal.SIGINT)
            try:
                proc.wait(timeout=30)
            except subprocess.TimeoutExpired:
                print(f"[!] Force killing {url} after timeout.")
                proc.kill()
        print(f"[-] Stopped monitoring: {url}")


def watch_file():
    last_mtime = None
    current_urls = set()

    while True:
        path = Path(STREAMER_LIST_FILE)
        try:
            mtime = path.stat().st_mtime
        except FileNotFoundError:
            time.sleep(POLL_INTERVAL)
            continue

        if mtime != last_mtime:
            last_mtime = mtime
            new_urls = read_streamer_list(STREAMER_LIST_FILE)

            added = new_urls - current_urls
            removed = current_urls - new_urls

            for url in removed:
                stop_monitor(url)
            for url in added:
                start_monitor(url)

            current_urls = new_urls
            if added or removed:
                print(f"[config] Reloaded: +{len(added)} added, -{len(removed)} removed. Active: {len(current_urls)}")

        time.sleep(POLL_INTERVAL)


def main():
    print(f"Watching {STREAMER_LIST_FILE} for changes (polling every {POLL_INTERVAL}s)...")

    watcher = threading.Thread(target=watch_file, daemon=True)
    watcher.start()

    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print("\nStopping all monitors...")
        with lock:
            urls = list(active_monitors.keys())
        for url in urls:
            stop_monitor(url)


if __name__ == "__main__":
    main()
