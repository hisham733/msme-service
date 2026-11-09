"""run.py — the one CLI entry that chains the stages (the joiner, reply 3 §3.6).

    python -m pipeline.run  scan | draft | validate | build | run  [--folder NAME | --folders a,b | --all]

`run` = draft -> validate (fail: re-prompt the LLM with the failure list, max retry_limit) ->
build. Every step stamps run.json in the release folder.
"""
import argparse
import json
import time

from . import build_site, llm_step, manifest, scan, usage, validate
from .config import load_config


def draft_one(cfg, item, call=None) -> dict:
    folder = item["path"]
    llm_step.draft_release(cfg, folder, call=call)
    return validate.validate_folder(folder)


def validate_with_loop(cfg, folder, call=None, max_extra=None):
    """draft -> validate; on failure re-prompt the LLM with the failure list (bounded), then HOLD."""
    retries = max_extra if max_extra is not None else cfg["llm"].get("retry_limit", 2)
    result = validate.validate_folder(folder)
    tries = 0
    while not result["ok"] and tries < retries:
        tries += 1
        failures = [f"{r['code']}: {r['detail']}" for r in result["results"]
                    if not r["ok"] and r["level"] == "fail"]
        llm_step.draft_release(cfg, folder, call=call, feedback=failures)
        result = validate.validate_folder(folder)
        manifest.write(folder, retries_used=tries)
    status = ("validated" if result["ok"]
              else "HOLD" if tries >= retries else "validate-failed")
    manifest.write(folder, status=status, validator={"ok": result["ok"], "results": result["results"]})
    return result, status


def run_one(cfg, item, call=None):
    folder = item["path"]
    usage.reset()
    manifest.write(folder, status="drafting", model=cfg["llm"]["model"])
    llm_step.draft_release(cfg, folder, call=call)
    result, status = validate_with_loop(cfg, folder, call=call)
    build_site.build_all(cfg)  # regenerate the index from every validated folder
    manifest.write(folder, usage=usage.get())
    return result, status


def main(argv=None):
    ap = argparse.ArgumentParser(description="AI_News pipeline: scan -> draft -> validate -> build")
    ap.add_argument("step", choices=["scan", "draft", "validate", "build", "run", "check"])
    ap.add_argument("--folder"); ap.add_argument("--folders"); ap.add_argument("--all", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    cfg = load_config()

    if a.step == "check":
        t0 = time.time()
        reply = llm_step.call_llm([{"role": "user", "content": "Reply with the single word OK."}], cfg)
        print(f"model={cfg['llm']['model']} version={cfg['llm'].get('model_version', '?')}")
        print(f"reply={reply.strip()[:40]!r} latency={time.time() - t0:.1f}s")
        return 0

    queue = scan.select_queue(cfg, a.folder, a.folders, a.all)

    if a.step == "scan":
        out = queue
    elif a.step == "build":
        out = [build_site.build_all(cfg)]
    else:
        out = []
        for item in queue:
            folder = item["path"]
            if a.step == "draft":
                llm_step.draft_release(cfg, folder)
                out.append(validate.validate_folder(folder))
            elif a.step == "validate":
                result = validate.validate_folder(folder)
                manifest.write(folder, validator={"ok": result["ok"], "results": result["results"]},
                               status="validated" if result["ok"] else "validate-failed")
                out.append(result)
            elif a.step == "run":
                result, status = run_one(cfg, item)
                out.append({"folder": item["folder"], "status": status,
                            "ok": result["ok"], "results": result["results"]})
    if a.json:
        print(json.dumps(out, indent=2, ensure_ascii=False, default=str))
    else:
        for i in out:
            if isinstance(i, dict) and "results" in i:
                name = i.get("folder", i.get("draft", {}).get("title", "?") if isinstance(i.get("draft"), dict) else "?")
                print(f"\n== {name}: {'PASS' if i['ok'] else 'FAIL'}")
                for r in i["results"]:
                    print(f"  [{'x' if r['ok'] else ' '}] {r['code']:28} {r['detail'][:70]}")
            else:
                print(json.dumps(i, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
