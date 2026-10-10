#!/usr/bin/env python3
"""
price_calculator.py —— 麦麦省钱参谋 · 模拟省钱工作流

零外部依赖、无需 Token，用 fixtures 模拟 mcd-mcp 的菜单与券数据，
演示「查券 → 领券（确认闸门） → 选品 → 无券算价 → 带券试算 → 输出对比表」的完整决策链路。

用法：
    python price_calculator.py --fixtures ../fixtures/sample_menu.json --yes

说明：
    --yes 表示自动确认「领券」（演示用）；不带 --yes 会交互询问，
    模拟 Skill 中的确认闸门。
"""

import argparse
import json
import sys
from pathlib import Path


def cent_to_yuan(cent: int) -> str:
    return f"¥{cent / 100:.2f}"


def load_fixture(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def display_coupons(coupons: list[dict]) -> None:
    print("\n当前可领券：")
    for idx, c in enumerate(coupons, 1):
        note = c.get("note", "")
        print(f"  {idx}. {c['name']}  ({note})")


def confirm(prompt_text: str, auto_yes: bool) -> bool:
    if auto_yes:
        print(f"{prompt_text} [Y/n] Y")
        return True
    ans = input(f"{prompt_text} [Y/n] ").strip().lower()
    return ans in ("y", "yes", "")


def calculate_base(cart: list[dict], menu: list[dict]) -> int:
    """无券基准价（分）。"""
    total = 0
    menu_map = {m["productCode"]: m for m in menu}
    for item in cart:
        p = menu_map[item["productCode"]]
        total += p["price_cent"] * item["quantity"]
    return total


def calculate_with_coupon(cart: list[dict], menu: list[dict], coupon: dict) -> tuple[int, str | None]:
    """模拟带券试算，返回 (discount_cent, error_or_none)。"""
    base = calculate_base(cart, menu)

    # 9.9元指定饮品券：必须绑定到指定商品
    if "bindProductCode" in coupon:
        bound = coupon["bindProductCode"]
        bound_items = [i for i in cart if i["productCode"] == bound]
        if not bound_items:
            return 0, f"600012 当前优惠券不可用！（{coupon['name']} 仅适用于指定商品）"
        # 计算节省：原价 - 券面价
        menu_map = {m["productCode"]: m for m in menu}
        bound_price = menu_map[bound]["price_cent"]
        face = coupon["facePrice_cent"]
        discount = max(0, bound_price - face)
        return discount, None

    # 满减券
    if "bindRule" in coupon:
        threshold = int(coupon["bindRule"].replace("total >= ", ""))
        if base >= threshold:
            return coupon["discount_cent"], None
        else:
            return 0, f"未达到满减门槛（需满 {cent_to_yuan(threshold)}）"

    return 0, "未知券类型"


def build_cart(menu: list[dict]) -> list[dict]:
    """交互式选品：默认把示例菜单各买 1 份。"""
    print("\n示例选品（菜单各 1 份）：")
    cart = []
    for m in menu:
        cart.append({"productCode": m["productCode"], "quantity": 1})
        print(f"  - {m['name']} ×1  {cent_to_yuan(m['price_cent'])}")
    return cart


def main() -> int:
    parser = argparse.ArgumentParser(description="麦麦省钱参谋 · 模拟省钱工作流")
    parser.add_argument("--fixtures", "-f", type=Path, default=Path("../fixtures/sample_menu.json"),
                        help="菜单与券 fixtures 路径")
    parser.add_argument("--yes", action="store_true", help="自动确认领券/下单（演示模式）")
    args = parser.parse_args()

    if not args.fixtures.exists():
        print(f"fixtures 不存在：{args.fixtures}", file=sys.stderr)
        return 1

    data = load_fixture(args.fixtures)
    menu = data["menu"]
    coupons = data["available_coupons"]
    store = data["store"]

    print(f"\n=== 麦麦省钱参谋 · 模拟工作流 ===")
    print(f"门店：{store['storeName']} ({store['storeCode']})")

    # 1. 查券
    display_coupons(coupons)

    # 2. 领券（确认闸门）
    if confirm("\n是否一键领取全部可领券？", args.yes):
        print("✅ 领券成功，全部券已加入账户。")
    else:
        print("已取消领券，仅使用无券基准价演示。")
        coupons = []

    # 3. 选品
    cart = build_cart(menu)

    # 4. 无券基准价
    base_cent = calculate_base(cart, menu)
    print(f"\n无券基准价：{cent_to_yuan(base_cent)}")

    # 5. 带券试算
    results = [
        {
            "name": "基准（无券）",
            "coupon": None,
            "discount_cent": 0,
            "pay_cent": base_cent,
            "error": None,
        }
    ]

    for coupon in coupons:
        discount, error = calculate_with_coupon(cart, menu, coupon)
        results.append({
            "name": f"用 {coupon['name']}",
            "coupon": coupon["name"],
            "discount_cent": discount,
            "pay_cent": max(0, base_cent - discount),
            "error": error,
        })

    # 6. 输出对比表
    print("\n对比表：")
    print("─" * 70)
    print(f"{'方案':<22} {'用券':<20} {'到手价':<10} {'状态':<12}")
    print("─" * 70)
    for r in results:
        coupon = r["coupon"] or "—"
        pay = cent_to_yuan(r["pay_cent"])
        status = "可用" if r["error"] is None else r["error"]
        print(f"{r['name']:<22} {coupon:<20} {pay:<10} {status:<12}")
    print("─" * 70)

    valid = [r for r in results if r["error"] is None]
    if valid:
        best = min(valid, key=lambda x: x["pay_cent"])
        save = base_cent - best["pay_cent"]
        print(f"\n推荐：{best['name']}，到手 {cent_to_yuan(best['pay_cent'])}，比基准省 {cent_to_yuan(save)}")

    print("\n注：本脚本为离线模拟，未调用真实 mcd-mcp；真实场景需配置 MCP Token 并由用户确认后下单。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
