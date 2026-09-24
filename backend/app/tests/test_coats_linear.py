"""遍数线性升数测例。

固定净面积 NET_M2=46.41 ㎡、涂布率 COVERAGE=8 ㎡/L（沿用 test_calc.py
客厅口径，全程不改涂布率），断言：

1. 遍数 2 的升数 == 遍数 1 的升数 × 2；遍数 3 == 遍数 1 × 3；
   两侧均取现网引擎 paint_liters 的分升口径 round(_, 2) 后再比较。
2. 遍数 0 或负数必须抛 ValueError 被拒绝（不落库、不对真假字段）。

纯函数 paint_liters / estimate_room 为主路径；另附一条 FastAPI
TestClient 路径（persist=False，只比响应升数），环境缺 httpx 时自动 skip。
"""
import pytest

from app.engines.estimate import estimate_room
from app.engines.paint_volume import paint_liters

# 固定入参：净面积与涂布率在整组测例中不得调整
NET_M2 = 46.41
COVERAGE = 8.0
OPENINGS = [{"w": 0.9, "h": 2.1}, {"w": 1.5, "h": 1.4}]
EXPECTED = {1: 5.8, 2: 11.6, 3: 17.4}  # round(NET_M2*n/COVERAGE, 2)


def _liters(coats: int) -> float:
    return paint_liters(NET_M2, COVERAGE, coats)["liters"]


def _assert_multiple_of_one_coat(n: int) -> None:
    """n 遍升数须等于 1 遍升数乘 n（分升口径）；失败时打印两侧升数与遍数。"""
    one = _liters(1)
    got = _liters(n)
    expected = round(one * n, 2)
    assert got == expected, (
        f"遍数={n} 升数非线性：{n}遍实测升数={got} L，"
        f"1遍实测升数({one} L)×{n}={expected} L；"
        f"净面积={NET_M2} ㎡，涂布率={COVERAGE} ㎡/L，遍数={n}"
    )


@pytest.mark.parametrize("coats", [1, 2, 3])
def test_liters_fixed_baseline(coats):
    """分升绝对锚点：与现网公式 round(净面积*遍数/涂布率, 2) 一致。"""
    got = _liters(coats)
    expected = round(NET_M2 * coats / COVERAGE, 2)
    assert got == expected, (
        f"遍数={coats}：实测升数={got} L，现网公式升数={expected} L"
    )
    assert got == EXPECTED[coats], f"遍数={coats}：实测={got} L，锚点={EXPECTED[coats]} L"


def test_two_coats_is_double_one_coat():
    _assert_multiple_of_one_coat(2)
    assert _liters(2) == 11.6


def test_three_coats_is_triple_one_coat():
    _assert_multiple_of_one_coat(3)
    assert _liters(3) == 17.4


@pytest.mark.parametrize("bad_coats", [0, -1, -3])
def test_nonpositive_coats_rejected(bad_coats):
    """遍数 0 或负数：引擎必须拒绝，不得返回升数。"""
    with pytest.raises(ValueError):
        paint_liters(NET_M2, COVERAGE, bad_coats)


def test_combined_engine_keeps_linearity():
    """组合引擎 estimate_room 走同一套口径，且同样拒绝非正遍数。"""
    one = estimate_room(5, 4, 2.8, OPENINGS, COVERAGE, 1)["liters"]
    assert one == EXPECTED[1]
    for n in (2, 3):
        got = estimate_room(5, 4, 2.8, OPENINGS, COVERAGE, n)["liters"]
        expected = round(one * n, 2)
        assert got == expected, (
            f"组合引擎 遍数={n}：实测升数={got} L，1遍升数({one} L)×{n}={expected} L"
        )
    with pytest.raises(ValueError):
        estimate_room(5, 4, 2.8, OPENINGS, COVERAGE, 0)
    with pytest.raises(ValueError):
        estimate_room(5, 4, 2.8, OPENINGS, COVERAGE, -2)


def test_http_path_coats_linearity(tmp_path, monkeypatch):
    """HTTP 路径（TestClient）：persist=False，只比响应中的 liters，不落库对表。

    需要 httpx（Starlette TestClient 依赖），未安装时整条 skip，
    不影响纯函数测例与原有 test_calc.py。
    """
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient

    # 尽量把 DATA_DIR 也指到临时目录（须在 app.config 首次导入前生效）
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    import app.db as db
    from app.main import app  # 导入即注册 startup 上的 seed.init_db

    # 再兜底把 DB 指到临时文件，startup 的 seed.init_db() 即播种该库
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "coats_linear_http.db")
    with TestClient(app, raise_server_exceptions=False) as client:
        liters = {}
        for n in (1, 2, 3):
            resp = client.post(
                "/api/estimate",
                json={"room_id": 1, "persist": False, "coverage": COVERAGE, "coats": n},
            )
            assert resp.status_code == 200, resp.text
            liters[n] = resp.json()["liters"]

        for n in (2, 3):
            expected = round(liters[1] * n, 2)
            assert liters[n] == expected, (
                f"HTTP 遍数={n}：响应升数={liters[n]} L，"
                f"1遍响应升数({liters[1]} L)×{n}={expected} L"
            )

        # 遍数 0/负数在 HTTP 层同样必须被拒绝（现网为引擎 ValueError -> 非 2xx）
        for bad in (0, -1):
            resp = client.post(
                "/api/estimate",
                json={"room_id": 1, "persist": False, "coverage": COVERAGE, "coats": bad},
            )
            assert resp.status_code >= 400, (
                f"HTTP 遍数={bad} 应被拒绝，实际 status={resp.status_code} body={resp.text}"
            )
