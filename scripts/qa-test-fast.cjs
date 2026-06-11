// Fast 200 QA tests in Node.js - no encoding issues
const http = require('http');

const BASE = 'http://localhost:3000';
const QUERIES = [
    ["翅片①号尺寸", "669.2"], ["翅片②号尺寸", "32"], ["翅片③号尺寸", "8"], ["翅片④号尺寸", "2.8"],
    ["冷凝器芯体①号尺寸", "824"], ["冷凝器芯体②号尺寸", "403"], ["冷凝器芯体③号尺寸", "290"],
    ["冷凝器芯体④号尺寸", "133"], ["冷凝器芯体⑤号尺寸", "212"], ["冷凝器芯体⑥号尺寸", "335"],
    ["冷凝器芯体⑦号尺寸", "372"], ["冷凝器芯体⑧号尺寸", "15.5"], ["冷凝器芯体⑨号尺寸", "10.15"],
    ["芯体总成①号尺寸", "320"], ["芯体总成②号尺寸", "320"], ["芯体总成③号尺寸", "640"],
    ["芯体总成④号尺寸", "119.5"], ["芯体总成⑤号尺寸", "227"], ["芯体总成⑥号尺寸", "373"],
    ["芯体总成对角线", "对角线"], ["集流管①号尺寸", ""], ["集流管②号尺寸", ""],
    ["集流管④号尺寸", "53.2"], ["集流管⑩号尺寸", "287.9"], ["集流管⑪号尺寸", "44.1"],
    ["冷凝器芯体技术要求", "技术"], ["翅片百叶窗", "百叶窗"], ["集流管外观", "翻边"],
    ["冷凝器芯体对角线", "对角线"], ["翅片外观", "毛刺"], ["芯体总成外观", "技术"],
    ["吹脚风门板海绵", "海绵"], ["冷凝器芯体③号公差", "290"], ["集流管④号公差", "53.2"],
    ["翅片①号公差", "669"], ["高度尺检验", "高度尺"], ["卷尺检验", "卷尺"],
    ["通止规检验", "通止规"], ["散热带检查仪", "散热带"],
];

function post(path, body, token) {
    return new Promise((resolve, reject) => {
        const url = new URL(path, BASE);
        const data = JSON.stringify(body);
        const opts = {
            hostname: url.hostname, port: url.port, path: url.pathname,
            method: 'POST', headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data) }
        };
        if (token) opts.headers['Authorization'] = 'Bearer ' + token;
        const req = http.request(opts, (res) => {
            let buf = '';
            res.on('data', c => buf += c);
            res.on('end', () => { try { resolve(JSON.parse(buf)); } catch(e) { resolve({}); } });
        });
        req.on('error', reject);
        req.write(data);
        req.end();
    });
}

async function main() {
    // Login
    const login = await post('/api/auth/login', { username: '管理员', password: 'admin123' });
    const token = login.token;
    console.log('Login OK');

    let total = 0, passed = 0, failed = 0;
    const start = Date.now();
    const CONCURRENCY = 5;

    const questions = [];
    for (let r = 0; r < 5 && total < 200; r++) {
        for (const [q, want] of QUERIES) {
            if (total >= 200) break;
            questions.push({ q: q + ['','是多少','多少','的标准','是什么'][total % 5], want, n: total });
            total++;
        }
    }

    // Process in batches
    for (let i = 0; i < questions.length; i += CONCURRENCY) {
        const batch = questions.slice(i, i + CONCURRENCY);
        const results = await Promise.all(batch.map(async (t) => {
            try {
                const resp = await post('/api/qa/ask', { question: t.q }, token);
                const mp = resp.matchedProducts || [];
                const answer = resp.answer || '';
                return { n: t.n, ok: mp.length > 0 && answer.length > 10 };
            } catch (e) {
                return { n: t.n, ok: false, err: e.message };
            }
        }));
        for (const r of results) {
            if (r.ok) passed++; else failed++;
            if (!r.ok && failed <= 5) console.log(`FAIL #${r.n}: ${r.err || 'no match'}`);
        }
        if ((i / CONCURRENCY) % 10 === 0) {
            console.log(`  ${Math.min(i + CONCURRENCY, questions.length)}/${questions.length} ...`);
        }
    }

    const elapsed = (Date.now() - start) / 1000;
    const pct = total > 0 ? (passed / total * 100) : 0;

    console.log('\n' + '='.repeat(60));
    console.log(`QA TEST RESULTS (Node.js)`.padStart(45));
    console.log('='.repeat(60));
    console.log(`Total:   ${total}`);
    console.log(`Passed:  ${passed}`);
    console.log(`Failed:  ${failed}`);
    console.log(`Rate:    ${pct.toFixed(1)}%`);
    console.log(`Time:    ${elapsed.toFixed(1)}s (${(total/elapsed).toFixed(1)} q/s)`);
    console.log('='.repeat(60));
    console.log(pct >= 99 ? 'PASS (>=99%)' : pct >= 95 ? 'WARN (>=95%)' : 'FAIL (<95%)');
}

main().catch(e => { console.error(e); process.exit(1); });
