/**
 * 产品检规路由 — /api/products/*
 */
const express = require('express');
const fs = require('fs');
const path = require('path');
const multer = require('multer');
const { authenticate, requirePermission } = require('../middleware/auth');

const router = express.Router();
const KB_DIR = path.resolve(__dirname, '..', '..', 'knowledge-base');
const PRODUCTS_DIR = path.join(KB_DIR, 'products');
const DRAWINGS_DIR = path.join(KB_DIR, 'drawings');
const INDEX_FILE = path.join(KB_DIR, 'index.json');

router.use(authenticate);
router.use(requirePermission('products:read'));

// ── 图纸上传 multer ──
const drawingUpload = multer({
  storage: multer.diskStorage({
    destination: (req, file, cb) => {
      const dir = path.join(DRAWINGS_DIR, req.params.id);
      if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
      cb(null, dir);
    },
    filename: (req, file, cb) => {
      cb(null, Buffer.from(file.originalname, 'latin1').toString('utf8'));
    }
  }),
  limits: { fileSize: 50 * 1024 * 1024 },
  fileFilter: (req, file, cb) => {
    const ok = ['.png','.jpg','.jpeg','.gif','.bmp','.svg','.pdf'].includes(path.extname(file.originalname).toLowerCase());
    cb(ok ? null : new Error('仅支持图片/PDF'), ok);
  }
});

// ── 辅助：重建索引 ──
function rebuildIndex() {
  try {
    const files = fs.readdirSync(PRODUCTS_DIR).filter(f => f.endsWith('.json'));
    const products = [];
    let totalCheckItems = 0;
    for (const f of files) {
      const p = JSON.parse(fs.readFileSync(path.join(PRODUCTS_DIR, f), 'utf-8'));
      const id = f.replace('.json', '');
      products.push({
        id, productId: p.productId, productName: p.productName,
        importanceLevel: p.importanceLevel, inspectionType: p.inspectionType,
        totalCheckItems: p.totalCheckItems || (p.checkItems || []).length,
      });
      totalCheckItems += p.totalCheckItems || (p.checkItems || []).length;
    }
    products.sort((a, b) => a.productId.localeCompare(b.productId));
    fs.writeFileSync(INDEX_FILE, JSON.stringify({
      totalProducts: products.length, totalCheckItems,
      generatedAt: new Date().toISOString(),
      products
    }, null, 2));
    return products;
  } catch (e) { console.error('Index rebuild error:', e); return []; }
}

/** 产品列表 */
router.get('/', (req, res) => {
  try {
    const ip = path.join(KB_DIR, 'index.json');
    if (!fs.existsSync(ip)) return res.json({ products: [], total: 0 });
    const idx = JSON.parse(fs.readFileSync(ip, 'utf-8'));
    res.json({ total: idx.totalProducts, totalCheckItems: idx.totalCheckItems, generatedAt: idx.generatedAt, products: idx.products });
  } catch (e) { res.status(500).json({ error: e.message }); }
});

/** 搜索 — 关键词拆分匹配（修复中文查询） */
router.get('/search/all', (req, res) => {
  const raw = (req.query.q || '').trim();
  if (!raw) return res.json({ query: '', results: [], total: 0 });
  // Split into keywords
  const q = raw.toLowerCase();
  const keys = [];
  // Keep full query (always match the complete string first)
  keys.push(q);
  // Split on spaces/punctuation and keep meaningful chunks
  const chunks = q.split(/[\s,，。、；：±+\-0-9０-９]+/).filter(k => k.length > 0);
  keys.push(...chunks.filter(k => k.length >= 2)); // skip single-char noise
  // Also split Chinese+number boundaries: "芯体2号" → ["芯体","号"]
  for (const chunk of [...chunks]) {
    const splitCN = chunk.split(/(?<=[一-鿿])(?=\d)|(?<=\d)(?=[一-鿿])/);
    if (splitCN.length > 1) keys.push(...splitCN.filter(k => k.length >= 2));
  }
  // Chinese bigrams for partial matching
  for (const chunk of chunks) {
    const cnPart = chunk.replace(/[^一-鿿]/g, '');
    for (let i = 0; i + 1 < cnPart.length; i++) {
      keys.push(cnPart.substring(i, i + 2));
    }
  }
  const keywords = [...new Set(keys.filter(k => k.length >= 2))];

  try {
    const ip = path.join(KB_DIR, 'index.json');
    if (!fs.existsSync(ip)) return res.json({ query: raw, results: [], total: 0 });
    const idx = JSON.parse(fs.readFileSync(ip, 'utf-8'));
    const results = [];
    for (const p of idx.products) {
      const fp = path.join(PRODUCTS_DIR, `${p.id}.json`);
      if (!fs.existsSync(fp)) continue;
      const prod = JSON.parse(fs.readFileSync(fp, 'utf-8'));
      const metaPool = [prod.productId, prod.productName, prod.project, prod.importanceLevel, prod.inspectionType, prod.company, prod.preparedBy, prod.documentNumber].join(' ').toLowerCase();
      let metaScore = 0;
      for (const k of keywords) { if (metaPool.includes(k)) metaScore++; }

      const matchedItems = [];
      for (const item of prod.checkItems) {
        const itemPool = [item.category, item.standard, item.tool, item.controlMethod, item.reactionPlan].join(' ').toLowerCase();
        let is = 0;
        for (const k of keywords) { if (itemPool.includes(k)) is++; }
        if (is > 0) matchedItems.push(item);
      }

      if (metaScore > 0 || matchedItems.length > 0) {
        results.push({
          id: p.id, productId: prod.productId, productName: prod.productName,
          importanceLevel: prod.importanceLevel, inspectionType: prod.inspectionType,
          totalCheckItems: prod.totalCheckItems, metaMatch: metaScore > 0,
          matchedItemsCount: matchedItems.length,
          matchedItems: matchedItems.slice(0, 10).map(i => ({ seq: i.seq, category: i.category, standard: i.standard, tool: i.tool, frequency: i.frequency })),
        });
      }
    }
    results.sort((a, b) => (b.metaMatch ? 1 : 0) - (a.metaMatch ? 1 : 0) || b.matchedItemsCount - a.matchedItemsCount);
    res.json({ query: raw, results, total: results.length });
  } catch (e) { res.status(500).json({ error: e.message }); }
});

/** 图纸列表 — 必须在 :id 之前 */

/** 新增产品 — admin only */
router.post('/', requirePermission('*'), (req, res) => {
  try {
    const { productId, productName, importanceLevel, inspectionType, version, preparedBy, preparedDate, company, documentNumber, checkItems } = req.body;
    if (!productId || !productName) return res.status(400).json({ error: '产品编号和名称为必填' });

    const fp = path.join(PRODUCTS_DIR, `${productId}.json`);
    if (fs.existsSync(fp)) return res.status(409).json({ error: '产品编号已存在' });

    const itemList = (checkItems || []).map((it, i) => ({
      seq: it.seq || (i + 1),
      category: it.category || '',
      standard: it.standard || '',
      tool: it.tool || '',
      sampleSize: it.sampleSize || '1件',
      frequency: it.frequency || '',
      controlMethod: it.controlMethod || '',
      reactionPlan: it.reactionPlan || '',
      _imageRefs: [],
      _dimAnnotation: it.standard && /^\d/.test(it.standard) ? {
        markers: [{ symbol: String(it.standard.match(/^(\d+)/)?.[1] || ''), num: parseInt(it.standard.match(/^(\d+)/)?.[1]) || 0 }],
        values: [it.standard.replace(/^\d+\s*/, '')],
        tolerations: [],
        fullText: it.standard,
        partDesc: ''
      } : { markers: [], values: [], tolerations: [] },
    }));

    const product = {
      productId, productName,
      project: project || '',
      importanceLevel: importanceLevel || '一般部件',
      version: version || 'A/0',
      preparedBy: preparedBy || '',
      preparedDate: preparedDate || '',
      company: company || '仪达智能热管理科技（马鞍山）有限公司',
      documentNumber: documentNumber || '',
      inspectionType: inspectionType || '制程检验',
      totalCheckItems: itemList.length,
      checkItems: itemList,
      _allImages: []
    };

    fs.writeFileSync(fp, JSON.stringify(product, null, 2));
    rebuildIndex();
    res.status(201).json({ message: '产品已创建', productId });
  } catch (e) { res.status(500).json({ error: e.message }); }
});

/** 图纸上传 — 所有登录用户可传 */
router.post('/:id/drawings', drawingUpload.array('files', 10), (req, res) => {
  try {
    if (!req.files || req.files.length === 0) return res.status(400).json({ error: '请选择文件' });
    // Update product JSON _allImages
    const pid = req.params.id;
    const fp = path.join(PRODUCTS_DIR, `${pid}.json`);
    if (fs.existsSync(fp)) {
      const p = JSON.parse(fs.readFileSync(fp, 'utf-8'));
      const existing = new Set((p._allImages || []).map(i => i.name));
      req.files.forEach(f => {
        if (!existing.has(f.filename)) {
          p._allImages.push({ name: f.filename, url: `/drawings/${pid}/${encodeURIComponent(f.filename)}`, num: 99 });
        }
      });
      fs.writeFileSync(fp, JSON.stringify(p, null, 2));
    }
    res.json({ message: `已上传 ${req.files.length} 个文件`, files: req.files.map(f => f.filename) });
  } catch (e) { res.status(500).json({ error: e.message }); }
});

/** 图纸删除 — 所有登录用户可删 */
router.delete('/:id/drawings/:filename', (req, res) => {
  try {
    const pid = req.params.id;
    const fname = decodeURIComponent(req.params.filename);
    const fp = path.join(DRAWINGS_DIR, pid, fname);
    if (!fs.existsSync(fp)) return res.status(404).json({ error: '文件不存在' });
    fs.unlinkSync(fp);
    // Update product JSON
    const pfp = path.join(PRODUCTS_DIR, `${pid}.json`);
    if (fs.existsSync(pfp)) {
      const p = JSON.parse(fs.readFileSync(pfp, 'utf-8'));
      p._allImages = (p._allImages || []).filter(i => i.name !== fname);
      (p.checkItems || []).forEach(it => {
        it._imageRefs = (it._imageRefs || []).filter(r => r.name !== fname);
      });
      fs.writeFileSync(pfp, JSON.stringify(p, null, 2));
    }
    res.json({ message: '已删除', filename: fname });
  } catch (e) { res.status(500).json({ error: e.message }); }
});

router.get('/:id/drawings', (req, res) => {
  try {
    const dd = path.join(KB_DIR, 'drawings', req.params.id);
    if (!fs.existsSync(dd)) return res.json({ productId: req.params.id, drawings: [], total: 0 });
    // Read product JSON to get drawing metadata (label, type, markers)
    let dwgMeta = {};
    try {
      const pp = path.join(PRODUCTS_DIR, `${req.params.id}.json`);
      if (fs.existsSync(pp)) {
        const prod = JSON.parse(fs.readFileSync(pp, 'utf-8'));
        (prod._allImages || []).forEach(img => {
          dwgMeta[img.name] = { label: img.label, type: img.type, markers: img.markers };
        });
      }
    } catch (_) {}
    const files = fs.readdirSync(dd)
      .filter(f => /\.(jpg|jpeg|png|gif|pdf|bmp|svg)$/i.test(f))
      .map(f => ({
        name: f,
        url: `/drawings/${req.params.id}/${encodeURIComponent(f)}`,
        isImage: /\.(jpg|jpeg|png|gif|bmp|svg)$/i.test(f),
        annotated: f.includes('_annotated'),
        isTechReq: f.startsWith('tech_req'),
        ...(dwgMeta[f] || {}),
      }));
    // Sort: annotated first, then by numeric order
    files.sort((a, b) => {
      if (a.annotated !== b.annotated) return a.annotated ? -1 : 1;
      const na = parseInt((a.name.match(/\d+/g) || ['0'])[0]) || 0;
      const nb = parseInt((b.name.match(/\d+/g) || ['0'])[0]) || 0;
      return na - nb;
    });
    res.json({ productId: req.params.id, drawings: files, total: files.length });
  } catch (e) { res.status(500).json({ error: e.message }); }
});

/** 产品详情 (最后兜底) */
router.get('/:id', (req, res) => {
  try {
    const fp = path.join(PRODUCTS_DIR, `${req.params.id}.json`);
    if (!fs.existsSync(fp)) return res.status(404).json({ error: '产品不存在', id: req.params.id });
    res.json(JSON.parse(fs.readFileSync(fp, 'utf-8')));
  } catch (e) { res.status(500).json({ error: e.message }); }
});

module.exports = router;
