"""场景回放：读 scenarios 下的 JSON 剧本，逐条配对并输出 JSON 报告。"""

import argparse
import json
import os
import sys

from .engine import Engine

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def build_parser():
    parser = argparse.ArgumentParser(prog="match-antijoin", description="匹配防连坐回放")
    parser.add_argument("--scenario", default=os.path.join(HERE, "scenarios", "cooldown.json"))
    parser.add_argument("--sample", default=None, help="work")
    return parser


def replay(path):
    with open(path, encoding="utf-8") as handle:
        script = json.load(handle)
    engine = Engine(script["cooldown_ms"])
    allowed = 0
    blocked = 0
    for match_id, a, b, at_ms in script["pairs"]:
        if engine.pair(match_id, a, b, at_ms):
            allowed += 1
        else:
            blocked += 1
    return {"allowed": allowed, "blocked": blocked, "work": engine.work_count(), "matches": len(engine.history)}


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.sample == "work":
        engine = Engine(1000)
        for index in range(3000):
            engine.pair("m-%d" % index, "p-%d" % index, "q-%d" % index, index)
        report = {"allowed": 3000, "blocked": 0, "work": engine.work_count(), "matches": len(engine.history)}
    elif args.sample is None:
        report = replay(args.scenario)
    else:
        raise SystemExit("需要 --scenario <文件> 或 --sample work")
    sys.stdout.write(json.dumps(report, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
