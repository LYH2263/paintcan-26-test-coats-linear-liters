# 遍数线性升数测例 · 说明文档

## 目的

在**固定净面积**与**固定涂布率**下，验证现网引擎 `paint_liters` 的升数随遍数线性：

- 遍数 2 的升数 == 遍数 1 的升数 × 2
- 遍数 3 的升数 == 遍数 1 的升数 × 3
- 遍数为 0 或负数时，引擎须抛 `ValueError` 拒绝

## 目录

```
backend/app/tests/
├── test_calc.py                 # 既有引擎数字测例（保留，未改动）
└── coat_linearity/              # 本测例目录（遍数/coats 方向）
    ├── test_coats_linear.py
    └── README.md                # 本文档
```

目录名 `coat_linearity` 刻意取**遍数**语义，与开洞（openings）单调方向的测例目录错开，
两者并列于 `backend/app/tests/` 下、互不重名、互不引用。

## 运行方式

pytest（装了依赖的环境）：

```bash
cd backend
pytest app/tests/coat_linearity/test_coats_linear.py -v
```

本仓库环境若无 pip/pytest，亦可纯 Python 直跑（文件内置独立入口）：

```bash
cd backend
python3 app/tests/coat_linearity/test_coats_linear.py
```

## 固定口径

| 参数 | 取值 | 说明 |
| --- | --- | --- |
| 净面积 `net_m2` | `46.41` m² | 与既有 `test_calc.py` 同源的固定净面积 |
| 涂布率 `coverage_m2_per_l` | `8.0` m²/L | **全程固定，禁止改涂布率凑绿** |
| 取整 | `round(x, 2)` | 分升四舍五入，与现网引擎 `paint_volume.paint_liters` 的 `round(need, 2)` 完全一致 |

## 断言内容

触发方式为**纯函数** `app.engines.paint_volume.paint_liters(net_m2, coverage, coats)`，
不经过 API、不读写数据库，**不存在“真假落库字段对表”式断言**。

1. `test_coats1_baseline`：遍数 1 基准，46.41 / 8 = 5.80125 → `5.8`（绝对值锚点）。
2. `test_coats2_equals_double_coats1`：
   - 线性断言：`round(L1 × 2, 2)` == 引擎遍数 2 升数；
   - 绝对值锚点：46.41 × 2 / 8 = 11.6025 → `11.6`。
3. `test_coats3_equals_triple_coats1`：
   - 线性断言：`round(L1 × 3, 2)` == 引擎遍数 3 升数；
   - 绝对值锚点：46.41 × 3 / 8 = 17.40375 → `17.4`。
4. `test_zero_or_negative_coats_rejected`：遍数 `0 / -1 / -3` 均须抛 `ValueError`。

线性两侧在比较前统一走引擎同口径取整（`round(..., 2)`），避免拿未取整值与引擎输出直接比。

## 失败输出

线性断言失败时，先打印**两侧升数与遍数**，再抛 `AssertionError`，例如对“遍数不参与计算”的变异引擎：

```
[coat-linearity] 两侧升数不一致: 遍数=3 引擎侧升数=5.8 线性侧升数=17.4 (遍数=1 基准升数=5.8, 净面积=46.41, 涂布率=8.0)
```

非法遍数未被拒绝时打印：

```
[coat-linearity] 非法遍数未被拒绝: 遍数=<值> 净面积=46.41 涂布率=8.0
```

## 边界与约束

- 未删除、未修改任何原有引擎数字测例（`test_calc.py` 原样保留，且仍全部通过）。
- 不通过修改涂布率使测试变绿；涂布率 8.0 为固定常量。
- 引擎行为本身已满足口径（`paint_liters` 已拒绝 `coats <= 0`），本次仅新增测例与文档，无引擎代码改动。
