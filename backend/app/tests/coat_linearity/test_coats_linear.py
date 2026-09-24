"""遍数线性升数测例（coat linearity suite）。

固定净面积 46.41 m2、固定涂布率 8 m2/L（与既有引擎数字测例同源，不为凑绿改动），
验证升数随遍数线性：
  coats=2 升数 == coats=1 升数 * 2
  coats=3 升数 == coats=1 升数 * 3
两侧统一采用现网引擎口径 round(x, 2)（分升四舍五入，与 paint_volume.paint_liters 一致）。
遍数为 0 或负数时引擎须以 ValueError 拒绝。

仅经纯函数 paint_liters 触发；不写任何“真假落库字段”、不依赖数据库。
可由 pytest 收集，亦可直接 `python3 test_coats_linear.py` 运行。
"""

import os
import sys

try:
    from app.engines.paint_volume import paint_liters
except ImportError:  # 脱离 pytest 直接运行本文件时，把 backend/ 挂到 sys.path
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
    from app.engines.paint_volume import paint_liters

NET_M2 = 46.41          # 固定净面积（m2）
COVERAGE = 8.0          # 固定涂布率（m2/L），全程不得改动以凑绿
ROUND_DIGITS = 2        # 与现网引擎 paint_liters 的 round(need, 2) 一致


def _engine_round(value):
    """分升四舍五入口径：必须与现网引擎 paint_liters 完全一致（round 到 2 位小数）。"""
    return round(value, ROUND_DIGITS)


def _assert_linear(coats):
    """引擎 coats=n 升数 须等于 coats=1 升数 * n（同口径取整后比较）。"""
    base = paint_liters(NET_M2, COVERAGE, 1)["liters"]
    got = paint_liters(NET_M2, COVERAGE, coats)["liters"]
    expected = _engine_round(base * coats)
    if got != expected:
        # 失败时打印两侧升数与遍数
        print(
            f"[coat-linearity] 两侧升数不一致: 遍数={coats} 引擎侧升数={got} "
            f"线性侧升数={expected} (遍数=1 基准升数={base}, 净面积={NET_M2}, 涂布率={COVERAGE})"
        )
    assert got == expected


def test_coats1_baseline():
    v = paint_liters(NET_M2, COVERAGE, 1)
    # 46.41 / 8 = 5.80125 -> 5.8
    assert v["liters"] == 5.8
    assert v["coats"] == 1
    assert v["coverage"] == COVERAGE


def test_coats2_equals_double_coats1():
    _assert_linear(2)
    # 绝对值锚点：46.41 * 2 / 8 = 11.6025 -> 11.6
    assert paint_liters(NET_M2, COVERAGE, 2)["liters"] == 11.6


def test_coats3_equals_triple_coats1():
    _assert_linear(3)
    # 绝对值锚点：46.41 * 3 / 8 = 17.40375 -> 17.4
    assert paint_liters(NET_M2, COVERAGE, 3)["liters"] == 17.4


def test_zero_or_negative_coats_rejected():
    for bad_coats in (0, -1, -3):
        try:
            paint_liters(NET_M2, COVERAGE, bad_coats)
        except ValueError:
            continue
        print(f"[coat-linearity] 非法遍数未被拒绝: 遍数={bad_coats} 净面积={NET_M2} 涂布率={COVERAGE}")
        raise AssertionError(f"coats={bad_coats} 必须触发 ValueError，实际被接受")


def _run_standalone():
    tests = [
        obj for name, obj in sorted(globals().items())
        if name.startswith("test_") and callable(obj)
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"all {len(tests)} coat-linearity tests passed")


if __name__ == "__main__":
    _run_standalone()
