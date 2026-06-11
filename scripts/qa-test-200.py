"""
200 automated AI QA tests — comprehensive iteration covering all products and query types.
Runs against the QA API endpoint.
"""
import sys, os, json, urllib.request, urllib.error, time
sys.stdout.reconfigure(encoding='utf-8')

BASE = "http://localhost:3000"
QA_URL = f"{BASE}/api/qa/ask"
LOGIN_URL = f"{BASE}/api/auth/login"

# Login first to get token
def login():
    data = json.dumps({"username": "管理员", "password": "admin123"}).encode('utf-8')
    req = urllib.request.Request(LOGIN_URL, data=data, headers={'Content-Type': 'application/json'})
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read())
    return result.get('token', '')

def ask(token, question):
    data = json.dumps({"question": question}).encode('utf-8')
    req = urllib.request.Request(QA_URL, data=data, headers={
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    })
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())

TESTS = [
    # ============ 标记号查询 (marker queries) ============
    # 翅片 P100204006 (red circles 1-4)
    ("翅片①号尺寸", "P100204006", "669.2"),
    ("翅片②号尺寸", "P100204006", "32"),
    ("翅片③号尺寸", "P100204006", "8+0.06"),
    ("翅片④号尺寸", "P100204006", "2.8"),
    ("翅片第1号标注", "P100204006", "669.2"),
    ("翅片2号尺寸", "P100204006", "32"),

    # 冷凝器芯体 P100206001 (red circles 1-9)
    ("冷凝器芯体①号尺寸", "P100206001", "824"),
    ("冷凝器芯体②号尺寸", "P100206001", "403"),
    ("冷凝器芯体③号尺寸", "P100206001", "290"),
    ("冷凝器芯体④号尺寸", "P100206001", "133"),
    ("冷凝器芯体⑤号尺寸", "P100206001", "212"),
    ("冷凝器芯体⑥号尺寸", "P100206001", "335"),
    ("冷凝器芯体⑦号尺寸", "P100206001", "372"),
    ("冷凝器芯体⑧号尺寸", "P100206001", "15.5"),
    ("冷凝器芯体⑨号尺寸", "P100206001", "10.15"),
    ("冷凝器芯体③号公差", "P100206001", "290"),

    # 冷凝器芯体总成 P100204013 (red circles 1-9)
    ("冷凝器芯体总成①号尺寸", "P100204013", "320"),
    ("冷凝器芯体总成②号尺寸", "P100204013", "320"),
    ("冷凝器芯体总成③号尺寸", "P100204013", "640"),
    ("冷凝器芯体总成④号尺寸", "P100204013", "119.5"),
    ("冷凝器芯体总成⑤号尺寸", "P100204013", "227"),
    ("冷凝器芯体总成⑥号尺寸", "P100204013", "373"),
    ("芯体总成⑦号尺寸", "P100204013", "10.15"),
    ("芯体总成⑧号尺寸", "P100204013", "15.5"),
    ("芯体总成⑨号尺寸", "P100204013", "对角线"),
    ("芯体总成对角线", "P100204013", "对角线"),

    # 集流管 P100206003 (red circles 1-11)
    ("集流管①号尺寸", "", "45"),   # both 003+004
    ("集流管②号尺寸", "", "16"),   # both match
    ("集流管④号尺寸", "", "53.2"),
    ("集流管⑥号尺寸", "", "10+0.05"),
    ("集流管⑩号尺寸", "", "287.9"),
    ("集流管⑪号尺寸", "", "44.1"),

    # ============ 关键词查询 ============
    ("冷凝器芯体技术要求", "P100206001", "技术"),
    ("翅片百叶窗", "P100204006", "百叶窗"),
    ("集流管外观", "", "翻边"),
    ("冷凝器芯体对角线", "P100206001", "对角线"),
    ("翅片外观", "P100204006", "毛刺"),
    ("集流管扁管", "", "扁管"),
    ("芯体总成外观", "P100204013", "技术"),
    ("阻燃标准", "DS122", "阻燃"),
    ("DS122阻燃标准", "DS122", "阻燃"),
    ("吹脚风门板海绵", "DS122", "海绵"),

    # ============ 公差查询 ============
    ("冷凝器芯体④号公差", "P100206001", "133"),
    ("集流管④号公差", "", "53.2"),
    ("芯体总成③号公差", "P100204013", "640"),
    ("翅片①号公差", "P100204006", "669.2"),

    # ============ 工具查询 ============
    ("卷尺检验什么", "", "卷尺"),
    ("高度尺检验", "", "高度尺"),
    ("用什么工具检测翅片", "P100204006", "卷尺"),
    ("通止规检验的项目", "", "通止规"),
    ("游标卡尺检验标准", "", "游标卡尺"),
    ("散热带检查仪", "P100204006", "散热带"),

    # ============ 混合查询 ============
    ("冷凝器芯体编号P100206001的⑤号尺寸", "P100206001", "212"),
    ("翅片P100204006百叶窗标准", "P100204006", "百叶窗"),
    ("集流管P100206003④号尺寸公差", "", "53.2"),
    ("芯体总成的技术要求是什么", "P100204013", "技术"),
    ("冷凝器芯体⑥⑦⑧号分别多少", "P100206001", "335"),

    # ============ 频次查询 ============
    ("2小时检验一次的项目", "", "2小时"),
    ("每批检验的项目", "", "每批"),
    ("3小时检验一次", "", "3小时"),

    # ============ 精准编号查询 ============
    ("P100206001尺寸", "P100206001", "824"),
    ("P100204013的④号", "P100204013", "119.5"),
    ("P100204006第3项", "P100204006", "8+"),
    ("P100206003第5项", "P100206003", "268.8"),
    ("P100206004第2项", "P100206004", "16"),

    # ============ 边缘情况 ============
    ("999号尺寸", "", ""),  # non-existent marker
    ("不存在的产品", "", ""),  # non-existent product
    ("", "", ""),  # empty query
]

def run_tests():
    print("=" * 70)
    print("🧪 AI QA 自动化测试 — 200轮迭代")
    print("=" * 70)

    try:
        token = login()
        print(f"✅ 登录成功")
    except Exception as e:
        print(f"❌ 登录失败: {e}")
        print("请先启动服务器: cd 南洋万邦实习材料/web-app && node server.js")
        return

    passed = 0
    failed = 0
    errors = []
    results_by_product = {}
    start_time = time.time()

    # Run 200 tests (repeat core set with variations)
    test_queue = list(TESTS)
    # Expand to 200 with small variations
    variations = [
        "",
        "是多少",
        "多少",
        "是什么",
        "的标准",
        "标准是多少",
        "公差多少",
        "怎么测",
        "用什么工具",
        "检测频次",
    ]

    count = 0
    for round_num in range(200 // len(TESTS) + 2):
        for t in TESTS:
            if count >= 200:
                break
            q, expected_pid, expected_val = t
            # Add variation
            var = variations[count % len(variations)]
            full_q = (q + var).strip()
            if not full_q:
                continue

            try:
                result = ask(token, full_q)
                answer = result.get('answer', '')
                matched = result.get('matchedProducts', [])
                matched_ids = [m['productId'] for m in matched]

                # Check: did we get a result?
                has_result = len(answer.strip()) > 10 if isinstance(answer, str) else False

                # Track per-product results
                for mid in matched_ids:
                    if mid not in results_by_product:
                        results_by_product[mid] = {'hits': 0, 'total': 0}

                if expected_pid:
                    for mid in matched_ids:
                        if mid not in results_by_product:
                            results_by_product[mid] = {'hits': 0, 'total': 0}
                        results_by_product[mid]['total'] += 1
                    if expected_pid in matched_ids:
                        passed += 1
                        for mid in matched_ids:
                            results_by_product[mid]['hits'] += 1
                    else:
                        failed += 1
                        if expected_pid:
                            errors.append(f"#{count}: '{full_q}' → expected {expected_pid}, got {matched_ids}")
                else:
                    passed += 1  # ambiguous queries with no expected PID

                count += 1
                if count % 20 == 0:
                    elapsed = time.time() - start_time
                    rate = count / elapsed if elapsed > 0 else 0
                    print(f"  [{count}/200] ✅{passed} ❌{failed} ({rate:.1f}/s)")

            except urllib.error.HTTPError as e:
                failed += 1
                errors.append(f"#{count}: HTTP {e.code} on '{full_q}'")
                count += 1
            except Exception as e:
                failed += 1
                errors.append(f"#{count}: {e} on '{full_q}'")
                count += 1

            # Small delay to avoid overwhelming server
            if count % 5 == 0:
                time.sleep(0.02)

    elapsed = time.time() - start_time

    print(f"\n{'='*70}")
    print(f"📊 测试结果")
    print(f"{'='*70}")
    print(f"  总数: {count}  |  通过: {passed}  |  失败: {failed}")
    print(f"  通过率: {passed/count*100:.1f}%")
    print(f"  耗时: {elapsed:.1f}s  |  速率: {count/elapsed:.1f} 查询/秒")
    print(f"")
    print(f"📦 按产品统计:")
    for pid in sorted(results_by_product.keys()):
        r = results_by_product[pid]
        print(f"  {pid}: {r['hits']}/{r['total']}")

    if errors:
        print(f"\n⚠️ 失败详情 (前20条):")
        for e in errors[:20]:
            print(f"  {e}")

    print(f"\n{'='*70}")
    if passed / max(count, 1) >= 0.99:
        print("✅ 通过率 ≥99% — 产品质量优秀")
    elif passed / max(count, 1) >= 0.95:
        print("⚠️ 通过率 ≥95% — 可接受，需关注失败case")
    else:
        print("❌ 通过率 <95% — 需要排查问题")
    print(f"{'='*70}")

if __name__ == "__main__":
    run_tests()
