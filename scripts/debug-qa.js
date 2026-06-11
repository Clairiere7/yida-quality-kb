const fs = require('fs');
const path = require('path');

const CN = {'①':1,'②':2,'③':3,'④':4,'⑤':5,'⑥':6,'⑦':7,'⑧':8,'⑨':9,'⑩':10};
const SW = new Set(['的','是','什么','多少','吗','了','在','有','和','与','或','问','请','呢','标准','检验','产品','尺寸','公差']);

function tokenize(text) {
  let s = text
    .replace(/([a-zA-Z0-9]+)([一-鿿]+)/g, '$1 $2')
    .replace(/([一-鿿]+)([a-zA-Z0-9]+)/g, '$1 $2')
    .replace(/[（）《》【】{}，。！？、；：“”‘’\s\-_/\\]/g, ' ')
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

const idx = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'knowledge-base', 'index.json'), 'utf-8'));
const PD = path.join(__dirname, '..', 'knowledge-base', 'products');

for (const query of ['集流管', '集流管④号尺寸', '冷凝器芯体②号尺寸']) {
    const keys = tokenize(query);
    console.log('\nQuery:', query);
    console.log('Keys(>=2):', keys.filter(k => k.length >= 2));

    const hasProductKeyword = keys.some(k => k.length >= 2 && idx.products.some(prod => {
        return prod.productName.includes(k) || (prod.productId||'').includes(k);
    }));
    console.log('hasProductKeyword:', hasProductKeyword);

    let marker = 0;
    for (const [cn, n] of Object.entries(CN)) if (query.includes(cn)) { marker = n; break; }
    const m2 = query.match(/第?\s*(\d+)\s*[号项個]/);
    if (!marker && m2) marker = parseInt(m2[1]);
    console.log('marker:', marker);

    const scored = [];
    for (const prod of idx.products) {
        const fp = path.join(PD, prod.id + '.json');
        if (!fs.existsSync(fp)) { console.log('  MISS:', prod.id); continue; }
        const p = JSON.parse(fs.readFileSync(fp, 'utf-8'));
        const pn = p.productName;
        const ql = query.replace(/\d+号.*/, '').replace(/④/, '').trim();
        let score = 0;
        if (pn === ql) score = 200;
        else if (pn.startsWith(ql) || ql.startsWith(pn)) score = 120;
        else {
            for (const k of keys) { if (k.length>=2 && pn.includes(k)) score += 40; }
        }

        if (marker > 0) {
            for (const it of p.checkItems || []) {
                if (it._dimAnnotation && it._dimAnnotation.markers && it._dimAnnotation.markers.some(m => m.num === marker)) {
                    score += 15;
                }
            }
        }

        const minScore = (marker > 0 || hasProductKeyword) ? 1 : 2;
        console.log(`  ${prod.id}: score=${score} min=${minScore} nameMatch=${pn===ql||pn.startsWith(ql)||ql.startsWith(pn)}`);
        if (score >= minScore) scored.push({ id: prod.id, score, name: pn });
    }
    scored.sort((a,b) => b.score - a.score);
    console.log('Scored:', scored.map(s => s.id + ':' + s.score));
}
