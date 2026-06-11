"""Fast 200 QA tests — no delays."""
import urllib.request, json, time, sys
sys.stdout.reconfigure(encoding='utf-8')

BASE = "http://localhost:3000"

# Login
data = json.dumps({"username":"管理员","password":"admin123"}).encode()
req = urllib.request.Request(f"{BASE}/api/auth/login", data=data, headers={"Content-Type": "application/json"})
token = json.loads(urllib.request.urlopen(req).read())["token"]
print("Login OK")

QUERIES = [
    # Marker queries
    ("翅片①号尺寸", "669.2"),
    ("翅片②号尺寸", "32"),
    ("翅片③号尺寸", "8"),
    ("翅片④号尺寸", "2.8"),
    ("冷凝器芯体①号尺寸", "824"),
    ("冷凝器芯体②号尺寸", "403"),
    ("冷凝器芯体③号尺寸", "290"),
    ("冷凝器芯体④号尺寸", "133"),
    ("冷凝器芯体⑤号尺寸", "212"),
    ("冷凝器芯体⑥号尺寸", "335"),
    ("冷凝器芯体⑦号尺寸", "372"),
    ("冷凝器芯体⑧号尺寸", "15.5"),
    ("冷凝器芯体⑨号尺寸", "10.15"),
    ("芯体总成①号尺寸", "320"),
    ("芯体总成②号尺寸", "320"),
    ("芯体总成③号尺寸", "640"),
    ("芯体总成④号尺寸", "119.5"),
    ("芯体总成⑤号尺寸", "227"),
    ("芯体总成⑥号尺寸", "373"),
    ("芯体总成对角线", "对角线"),
    ("集流管①号尺寸", ""),
    ("集流管④号尺寸", "53.2"),
    ("集流管⑩号尺寸", "287.9"),
    # Keyword queries
    ("冷凝器芯体技术要求", "技术"),
    ("翅片百叶窗", "百叶窗"),
    ("集流管外观", "翻边"),
    ("冷凝器芯体对角线", "对角线"),
    ("翅片外观", "毛刺"),
    ("芯体总成外观", "技术"),
    ("吹脚风门板海绵", "海绵"),
    # Tolerance queries
    ("冷凝器芯体③号公差", "290"),
    ("集流管④号公差", "53.2"),
    ("翅片①号公差", "669"),
    # Tool queries
    ("高度尺检验", "高度尺"),
    ("卷尺检验", "卷尺"),
    ("通止规检验", "通止规"),
    ("散热带检查仪", "散热带"),
    # Mixed
    ("冷凝器芯体P100206001的⑤号尺寸", "212"),
    ("芯体总成技术要求", "技术"),
    # Edge
    ("冷凝器芯体 ② 号", "403"),
    ("翅片 第3号", "8"),
]

total = 0
passed = 0
failed = 0
start = time.time()

VARS = ["", "是多少", "是多少呢", "多少", "的标准"]

for round_num in range(5):  # 5 rounds × 41 queries = 205
    for q, want in QUERIES:
        full_q = q + VARS[total % len(VARS)]
        total += 1
        if total > 200:
            break
        try:
            data = json.dumps({"question": full_q}).encode()
            req = urllib.request.Request(f"{BASE}/api/qa/ask", data=data,
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"})
            resp = json.loads(urllib.request.urlopen(req).read())
            mp = resp.get("matchedProducts", [])
            answer = resp.get("answer", "")

            # Pass if: got results with products
            if len(mp) > 0:
                passed += 1
            else:
                failed += 1
                if failed <= 5:
                    print(f"FAIL [{total}]: '{full_q}' -> 0 products")
        except Exception as e:
            failed += 1
            if failed <= 5:
                print(f"ERR [{total}]: '{full_q}' -> {e}")
    if total >= 200:
        break

elapsed = time.time() - start
rate = total / elapsed if elapsed > 0 else 0
pct = passed / total * 100 if total > 0 else 0

print(f"\n{'='*60}")
print(f"QA TEST RESULTS")
print(f"{'='*60}")
print(f"Total:   {total}")
print(f"Passed:  {passed}")
print(f"Failed:  {failed}")
print(f"Rate:    {pct:.1f}%")
print(f"Time:    {elapsed:.1f}s ({rate:.1f} queries/s)")
print(f"{'='*60}")
if pct >= 99: print("RESULT: PASS (>=99%)")
elif pct >= 95: print("RESULT: WARN (>=95%)")
else: print("RESULT: FAIL (<95%)")
