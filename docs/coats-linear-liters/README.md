# 遍数线性升数测例 · 说明文档

> 目录名 `coats-linear-liters/`，与开洞单调测例目录（opening 相关）错开，互不引用。

## 1. 测什么

固定**净面积** `NET_M2 = 46.41 ㎡`（客厅 5×4×2.8，扣门 0.9×2.1 与窗 1.5×1.4）与
**涂布率** `COVERAGE = 8 ㎡/L`（与现网设置、`test_calc.py` 一致，全程不改），断言：

| 遍数 | 现网分升结果 `round(净面积×遍数/涂布率, 2)` |
| --- | --- |
| 1 | 5.80 L |
| 2 | 11.60 L（= 5.80 × 2） |
| 3 | 17.40 L（= 5.80 × 3） |

- 遍数为 **2** 的升数必须等于遍数为 **1** 的升数 ×2；
- 遍数为 **3** 的升数必须等于遍数为 **1** 的升数 ×3；
- 两侧统一走**分升（保留 2 位小数）口径**后再比较，与现网引擎
  `app/engines/paint_volume.py` 的 `round(need, 2)` 完全一致，不引入第二种取整规则。
- 遍数为 **0 或负数**：引擎必须抛 `ValueError` 拒绝（覆盖 `0 / -1 / -3`）。

## 2. 文件与触发方式

- 测例文件：`backend/app/tests/test_coats_linear.py`（新增，**未改动**原有
  `backend/app/tests/test_calc.py` 的任何数字测例）。
- 主路径为**纯函数**：直接调 `app.engines.paint_volume.paint_liters` 与
  `app.engines.estimate.estimate_room`，不建表、不落库。
- 另有一条 **TestClient（HTTP）路径** `test_http_path_coats_linearity`：
  `POST /api/estimate` 且 `persist=false`，只比较响应里的 `liters`，DB 指到
  pytest 临时目录。该用例需要 `httpx`（Starlette TestClient 的依赖）；
  requirements 未包含 httpx，缺失时用 `pytest.importorskip("httpx")` 自动 **skip**，
  不会让整套测试变红。需要时执行 `pip install httpx` 即可启用。

断言是对**引擎返回的升数数值**做比较；不通过、也不允许通过「把结果写成某个
真假布尔字段再对表」的方式判定。

## 3. 运行

```bash
cd backend
python -m pytest app/tests -q
```

预期：原 `test_calc.py` 4 项 + 本文件纯函数 9 项全部通过；未装 httpx 时
HTTP 用例显示 1 个 skipped。

## 4. 失败时输出

线性断言失败会同时打印**两侧升数与遍数**，例如人为把 2 遍结果改成 11.65 时：

```
AssertionError: 遍数=2 升数非线性：2遍实测升数=11.65 L，
1遍实测升数(5.8 L)×2=11.6 L；净面积=46.41 ㎡，涂布率=8.0 ㎡/L，遍数=2
```

HTTP 路径同理打印各遍响应升数。

## 5. 红线（防作弊）

- 不得删除或弱化原有引擎数字测例（`test_calc.py` 原样保留）。
- 不得靠改涂布率（或净面积）把测试凑绿：常量在文件顶部固定，比较的是
  「1 遍实测升数 × n」与「n 遍实测升数」两侧真实输出。
- 分升口径必须与现网引擎一致（`round(_, 2)`），测试里不另造取整函数。
