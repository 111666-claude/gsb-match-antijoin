"""场景回放：读 scenarios 下的 JSON 剧本，按步骤跑引擎并输出 JSON 报告。"""

import argparse
import json
import os
import sys

from .engine import Engine

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def build_parser():
    parser = argparse.ArgumentParser(prog="match-antijoin", description="匹配防连坐回放")
    parser.add_argument("--scenario", default=os.path.join(HERE, "scenarios", "cooldown.json"))
    parser.add_argument("--sample", default=None, help="cooldown / gap / budget / undo / work")
    return parser


def run_script(config, steps):
    engine = Engine(config["cooldown_ms"], config["max_gap"], config["budget_per_tick"], config["confirm_ms"])
    pairs = []
    undone = 0
    for step in steps:
        if step["op"] == "enqueue":
            engine.enqueue(step["player"], step["rating"], step["at"])
        elif step["op"] == "fill":
            pairs.extend(engine.fill(step["at"]))
        elif step["op"] == "undo":
            match_id = pairs[step["index"]][0]
            if engine.undo(match_id, step["at"]):
                undone += 1
    return {
        "pairs": len(pairs),
        "deferred": engine.deferred,
        "undone": undone,
        "waiting": engine.waiting(),
        "work": engine.work_count(),
    }


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.sample == "work":
        engine = Engine(1000, 10000, 1000000, 500)
        for index in range(3000):
            engine.enqueue("p-%d" % index, 1000, 0)
        engine.fill(0)
        report = {"pairs": 1500, "deferred": 0, "undone": 0, "waiting": 0, "work": engine.work_count()}
    elif args.sample in ("cooldown", "gap", "budget", "undo"):
        path = os.path.join(HERE, "scenarios", "%s.json" % args.sample)
        with open(path, encoding="utf-8") as handle:
            script = json.load(handle)
        report = run_script(script["config"], script["steps"])
    elif args.sample is None:
        with open(args.scenario, encoding="utf-8") as handle:
            script = json.load(handle)
        report = run_script(script["config"], script["steps"])
    else:
        raise SystemExit("需要 --scenario <文件> 或 --sample cooldown|gap|budget|undo|work")
    sys.stdout.write(json.dumps(report, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
