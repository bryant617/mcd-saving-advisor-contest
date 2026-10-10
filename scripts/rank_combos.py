#!/usr/bin/env python3
"""
rank_combos.py —— 麦麦省钱参谋 · 本地候选方案排序器

零外部依赖，可离线演示「多方案比价」核心逻辑。
读取候选方案 JSON，按到手价从低到高排序，输出对比表。

用法：
    python rank_combos.py --input ../fixtures/sample_candidates.json --top 3
"""

import argparse
import json
import sys
from pathlib import Path


def cent_to_yuan(cent: int) -> str:
    """分 → 元，保留两位小数。"""
    return f"¥{cent / 100:.2f}"


def load_candidates(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("输入文件应为候选方案数组")
    return data


def rank(candidates: list[dict], top: int | None = None) -> list[dict]:
    """按到手价（total_cent - discount_cent）升序排列。"""
    scored = []
    for c in candidates:
        total = int(c.get("total_cent", 0))
        discount = int(c.get("discount_cent", 0))
        pay = max(0, total - discount)
        scored.append({
            **c,
            "pay_cent": pay,
            "save_cent": discount,
        })
    scored.sort(key=lambda x: x["pay_cent"])
    return scored if top is None else scored[:top]


def render(candidates: list[dict]) -> str:
    lines = []
    lines.append("方案                用券              到手价    比基准省    说明")
    lines.append("─" * 72)
    for c in candidates:
        name = c.get("name", "未命名")
        coupon = c.get("coupon") or "—"
        pay = cent_to_yuan(c["pay_cent"])
        save = cent_to_yuan(c["save_cent"]) if c["save_cent"] else "—"
        note = c.get("note", "")
        lines.append(f"{name:<18} {coupon:<18} {pay:<10} {save:<12} {note}")
    lines.append("─" * 72)
    if candidates:
        best = candidates[0]
        lines.append(f"推荐：{best['name']}，到手 {cent_to_yuan(best['pay_cent'])}，省 {cent_to_yuan(best['save_cent'])}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="麦麦省钱参谋 · 候选方案排序")
    parser.add_argument("--input", "-i", type=Path, required=True, help="候选方案 JSON 路径")
    parser.add_argument("--top", "-n", type=int, default=None, help="仅展示前 N 个方案")
    args = parser.parse_args()

    if not args.input.exists():
        print(f"文件不存在：{args.input}", file=sys.stderr)
        return 1

    candidates = load_candidates(args.input)
    ranked = rank(candidates, top=args.top)
    print(render(ranked))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
