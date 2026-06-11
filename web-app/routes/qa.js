/**
 * QA 路由 — 精准匹配 + 简洁回答格式
 * 昨天版本：简单、精准、只回答匹配的内容
 */
const express = require('express');
const fs = require('fs');
const path = require('path');
const { authenticate, requirePermission } = require('../middleware/auth');
const router = express.Router();

const KB = path.resolve(__dirname, '../../knowledge-base');
const PD = path.join(KB, 'products');
const DD = path.join(KB, 'drawings');

router.use(authenticate);
router.use(requirePermission('qa:ask'));

function excelDate(v) {
  if (!v || v === '') return '未填写';
  const n = Number(v);
  if (isNaN(n) || n < 100 || n > 300000) return String(v);
  return new Date(Math.round((n - 25569) * 86400) * 1000).toISOString().slice(0, 10);
}

const CN = {'①':1,'②':2,'③':3,'④':4,'⑤':5,'⑥':6,'⑦':7,'⑧':8,'⑨':9,'⑩':10};
const SW = new Set(['的','是','什么','多少','吗','了','在','有','和','与','或','问','请','呢','标准','检验','产品','尺寸','公差','号']);

function parseMarker(query) {
  for (const [cn, n] of Object.entries(CN)) if (query.includes(cn)) return n;
  // "4号" "第4号" "序号4" → marker 4
  const m = query.match(/第?\s*(\d+)\s*[号项個个]/);
  return m ? parseInt(m[1]) : 0;
}

function tokenize(text) {
  let s = text
    .replace(/([a-zA-Z0-9]+)([一-鿿])/g, '$1 $2')
    .replace(/([一-鿿])([a-zA-Z0-9]+)/g, '$1 $2')
    .replace(/[（）()【】\[\]{}，。！？、；：""''\n\r\-_/\\]/g, ' ')
    .toLowerCase();
  const base = s.split(/\s+/).filter(w => w.length >= 1 && !SW.has(w));
  const extra = [];
  for (const t of base) {
    const cn = t.replace(/[^一-鿿]/g, '');
    for (const ch of cn) extra.push(ch);
    for (let i = 0; i + 1 < cn.length; i++) extra.push(cn.substring(i, i + 2));
  }
  return [...new Set([...base, ...extra])];
}

function getDrawings(productId, markerNum) {
  const dd = path.join(DD, productId);
  if (!fs.existsSync(dd)) return [];
  const pp = path.join(PD, `${productId}.json`);
  let imageNames = new Set();
  if (fs.existsSync(pp)) {
    try {
      const prod = JSON.parse(fs.readFileSync(pp, 'utf-8'));
      if (markerNum > 0) {
        for (const item of prod.checkItems || []) {
          if (item._dimAnnotation && item._dimAnnotation.markers && item._dimAnnotation.markers.some(m => m.num === markerNum)) {
            (item._imageRefs || []).forEach(r => imageNames.add(r.name));
          }
        }
      }
    } catch (_) {}
  }
  let files = fs.readdirSync(dd)
    .filter(f => /\.(jpg|jpeg|png|gif|pdf|bmp|svg)$/i.test(f) && !f.startsWith('.'))
    .map(f => ({
      name: f, url: `/drawings/${productId}/${encodeURIComponent(f)}`,
      isImage: true, annotated: f.includes('_annotated'), isTechReq: f.startsWith('tech_req')
    }));
  if (markerNum > 0 && imageNames.size > 0) {
    const matched = files.filter(f => imageNames.has(f.name));
    if (matched.length > 0) return matched;
  }
  if (markerNum <= 0) return files.filter(f => f.isTechReq);
  return [];
}

function buildContext(query) {
  const keys = tokenize(query);
  const idx_data = JSON.parse(fs.readFileSync(path.join(KB, 'index.json'), 'utf-8'));
  const marker = parseMarker(query);

  // Detect product ID mention: "003", "004", "P100206003", etc.
  const pidMention = query.match(/P?(\d{6,})\d{3}/i);
  const targetPid = pidMention ? pidMention[0].toUpperCase() : null;

  const scored = [];

  for (const prod of idx_data.products) {
    const fp = path.join(PD, prod.id + '.json');
    if (!fs.existsSync(fp)) continue;
    const p = JSON.parse(fs.readFileSync(fp, 'utf-8'));
    let score = 0;
    const matched = [];

    const pn = p.productName.toLowerCase();
    const pid = p.productId.toLowerCase();
    const pool = [pn, pid].join(' ');

    let nameScore = 0;
    const cleanQ = query.toLowerCase().replace(/[^a-z0-9一-鿿]/g, '');
    const cleanPid = pid.replace(/[^a-z0-9]/g, '');

    // Exact product ID match (e.g. "003", "P100206003")
    if (targetPid && pid.toUpperCase() === targetPid) nameScore = 300;
    else if (cleanQ.includes(cleanPid.slice(-6)) || cleanQ.includes(cleanPid)) nameScore = 250;
    // Exact name match
    else if (pn === cleanQ) nameScore = 200;
    // Prefix match
    else if (pn.startsWith(cleanQ) || cleanQ.startsWith(pn)) nameScore = 120;
    // Keyword match
    else for (const k of keys) { if (k.length >= 2 && pool.includes(k)) nameScore += 40; }

    score += nameScore;

    for (const it of p.checkItems) {
      const ip = [it.category, it.standard, it.tool, it.controlMethod, it.reactionPlan].join(' ').toLowerCase();
      let is = 0;
      for (const k of keys) { if (k.length >= 2 && ip.includes(k)) is++; }
      if (marker > 0 && nameScore > 0) {
        if (it._dimAnnotation && it._dimAnnotation.markers && it._dimAnnotation.markers.some(m => m.num === marker)) is += 15;
        else if (it.seq === marker) is += 5;
      }
      if (is > 0) { score += is; matched.push({ ...it, _score: is }); }
    }

    if (score > 0) scored.push({ product: p, id: prod.id, score, matched });
  }

  scored.sort((a, b) => b.score - a.score);

  // Pick top: if specific PID mentioned, use that; otherwise top 1
  let top;
  if (targetPid) {
    top = scored.filter(s => s.id.toUpperCase() === targetPid || s.product.productId.toUpperCase() === targetPid);
    if (top.length === 0) top = scored.slice(0, 1);
  } else {
    top = scored.slice(0, 1);
  }

  if (top.length === 0 || top[0].score < 1) {
    const mp = [];
    let ctx = '未找到匹配。\n\n';
    for (const prod of idx_data.products) {
      const p = JSON.parse(fs.readFileSync(path.join(PD, prod.id + '.json'), 'utf-8'));
      ctx += '◆ ' + p.productName + ' (' + p.productId + ') — ' + p.totalCheckItems + '项\n';
    }
    return { ctx, mp: [] };
  }

  const mp = [];
  let ctx = '';

  for (const { product, matched } of top.slice(0, 1)) {
    const dwg = getDrawings(product.productId, marker);
    mp.push({ productId: product.productId, productName: product.productName, drawings: dwg, markerNum: marker });

    if (marker > 0) {
      const exact = product.checkItems.filter(it => {
        if (it._dimAnnotation && it._dimAnnotation.markers) return it._dimAnnotation.markers.some(m => m.num === marker);
        return it.seq === marker;
      });
      if (exact.length > 0) {
        for (const it of exact) {
          const desc = (it._dimAnnotation && it._dimAnnotation.partDesc) || '';
          ctx += '■ ' + product.productName + ' (' + product.productId + ') — 第' + marker + '号' + (desc ? ' ' + desc : '') + '\n';
          ctx += '📏 标准: ' + it.standard + '\n';
          ctx += '🔧 工具: ' + it.tool + '    ⏱ 频次: ' + it.frequency + '    📦 容量: ' + it.sampleSize + '\n';
          const refs = it._imageRefs || [];
          if (refs.length > 0) ctx += '📐 图纸: ' + refs.map(r => r.name).join(', ') + '\n';
        }
      } else {
        ctx += '■ ' + product.productName + ' (' + product.productId + ')\n⚠ 未找到第' + marker + '号标注\n';
      }
    } else {
      ctx += '■ ' + product.productName + ' (' + product.productId + ')\n';
      ctx += '  ' + product.importanceLevel + ' | ' + product.inspectionType + '\n';
      const show = matched.filter(it => {
        const t = (it.category + ' ' + it.standard + ' ' + it.tool).toLowerCase();
        return keys.some(k => k.length >= 2 && t.includes(k));
      });
      const final = show.length > 0 ? show : matched;
      ctx += '\n  ═══ 匹配结果 (' + final.length + '条) ═══\n';
      for (const it of final.slice(0, 8)) {
        const desc = (it._dimAnnotation && it._dimAnnotation.partDesc) || '';
        ctx += '  [' + it.seq + '] ' + it.category + (desc ? ' — ' + desc : '') + '\n';
        ctx += '  📏 标准: ' + it.standard + '\n';
        ctx += '  🔧 工具: ' + it.tool + ' | ⏱ 频次: ' + it.frequency + '\n\n';
      }
      if (final.length > 8) ctx += '  ... 共' + final.length + '条\n';
    }

    if (dwg.length > 0) {
      ctx += '\n📐 关联图纸: ' + dwg.map(d => d.name).join(', ') + '\n';
    }
  }

  return { ctx, mp };
}

router.post('/ask', async (req, res) => {
  const { question } = req.body;
  if (!question) return res.status(400).json({ error: '请输入问题' });
  try {
    const { ctx, mp } = buildContext(question);
    const apiKey = process.env.ANTHROPIC_API_KEY;
    if (!apiKey) return res.json({ question, mode: 'offline', answer: ctx, matchedProducts: mp });
    const resp = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST', headers: { 'Content-Type': 'application/json', 'x-api-key': apiKey, 'anthropic-version': '2023-06-01' },
      body: JSON.stringify({
        model: 'claude-haiku-4-5', max_tokens: 2000,
        system: '你是仪达质检专家。只回答检规中有的内容，精确引用条目号和参数。回答格式：先列出产品名和编号，再给出具体标准。\n' + ctx,
        messages: [{ role: 'user', content: question }]
      }),
    });
    if (!resp.ok) return res.status(502).json({ error: 'AI 暂不可用' });
    const d = await resp.json();
    res.json({ question, mode: 'ai', answer: d.content[0]?.text || '', matchedProducts: mp });
  } catch (e) { res.status(500).json({ error: e.message }); }
});

module.exports = router;
