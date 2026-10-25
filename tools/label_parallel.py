"""Label a whole deck with a cloud model, many batches at once (the add-on's own job, core/llm.py, goes a batch at a
time with a daily cap, for a local model). The same prompts, schemas and parsing; every batch's labels are stored as
they come back (labels.jsonl in --files), so a stopped run loses nothing and the next one does only what is left.

    python3 tools/label_parallel.py COLLECTION.anki2 --files DIR [--model gpt-5.6-terra] [--base-url URL]
                                    [--key-env OPENAI_API_KEY] [--effort low] [--threads 12] [--batch 25]
                                    [--max-tokens 2000000] [--config cfg.json]

The key is read from the environment variable --key-env (never printed); a .env file can be given with --env."""
import argparse
import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from guesswithanki.core import llm, run  # noqa: E402
from guesswithanki.core.remote import chat  # noqa: E402


def load_env(path):
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("collection")
    ap.add_argument("--files", required=True)
    ap.add_argument("--config")
    ap.add_argument("--model", default="gpt-5.6-terra")
    ap.add_argument("--base-url", default="https://api.openai.com/v1")
    ap.add_argument("--key-env", default="OPENAI_API_KEY")
    ap.add_argument("--env")
    ap.add_argument("--effort", default="low")
    ap.add_argument("--threads", type=int, default=12)
    ap.add_argument("--batch", type=int, default=25)
    ap.add_argument("--max-tokens", type=int, default=2_000_000)
    ap.add_argument("--limit", type=int)
    a = ap.parse_args()
    if a.env:
        load_env(a.env)
    key = os.environ.get(a.key_env, "")
    if not key:
        sys.exit("no key in %s" % a.key_env)
    from anki.collection import Collection
    cfg = run.merged(json.loads(Path(a.config).read_text(encoding="utf-8")) if a.config else {})
    files = Path(a.files)
    files.mkdir(parents=True, exist_ok=True)
    col = Collection(a.collection)
    try:
        an = run.analyse(col, cfg, files, use_server=False)
    finally:
        col.close()
    lcfg = {"base_url": a.base_url, "model": a.model, "api_key": key, "reasoning_effort": a.effort, "json_schema": True,
            "temperature": False}
    order = an.new + an.started
    queue = llm.todo(order, an.store, a.model)[:a.limit]
    batches = [queue[i:i + a.batch] for i in range(0, len(queue), a.batch)]
    from guesswithanki.core.model import profile
    print("%s: profile %s, %d words to label in %d batches (%d threads)" % (a.collection, profile().name, len(queue),
                                                                         len(batches), a.threads), flush=True)
    lock = threading.Lock()
    tot = {"in": 0, "out": 0, "done": 0, "bad": 0, "calls": 0}
    stop = threading.Event()

    def one(batch):
        if stop.is_set():
            return
        prompt = llm.prompt_for(batch)
        for attempt in range(4):
            try:
                text, usage = chat(lcfg, prompt, schema=llm.schema_for(batch))
                break
            except Exception as e:                           # noqa: BLE001  (rate limits, timeouts: back off)
                if attempt == 3:
                    with lock:
                        tot["bad"] += len(batch)
                    print("  batch failed: %s" % str(e)[:160], flush=True)
                    return
                time.sleep(5 * (attempt + 1))
        recs = llm.parse(text, batch, a.model)
        with lock:
            an.store.add(recs)
            tot["in"] += usage.get("prompt_tokens", 0)
            tot["out"] += usage.get("completion_tokens", 0)
            tot["done"] += len(recs)
            tot["bad"] += len(batch) - len(recs)
            tot["calls"] += 1
            if tot["in"] + tot["out"] >= a.max_tokens:
                stop.set()
            if tot["calls"] % 10 == 0:
                print("  %d/%d words, %d tokens" % (tot["done"], len(queue), tot["in"] + tot["out"]), flush=True)

    t0 = time.time()
    with ThreadPoolExecutor(a.threads) as ex:
        for f in as_completed([ex.submit(one, b) for b in batches]):
            f.result()
    print(json.dumps(dict(tot, seconds=round(time.time() - t0), stopped_at_cap=stop.is_set(), model=a.model)), flush=True)


if __name__ == "__main__":
    main()
