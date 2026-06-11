/**
 * 技术要求路由 — /api/tech-specs/:productId
 */
const express = require('express');
const fs = require('fs');
const path = require('path');
const { authenticate, requirePermission } = require('../middleware/auth');

const router = express.Router();
const TS_DIR = path.resolve(__dirname, '..', '..', 'knowledge-base', 'tech_specs');

router.use(authenticate);
router.use(requirePermission('products:read'));

/** 获取产品技术要求 */
router.get('/:productId', (req, res) => {
  try {
    const fp = path.join(TS_DIR, `${req.params.productId}.json`);
    if (!fs.existsSync(fp)) return res.json({ productId: req.params.productId, sections: [], available: false });
    const data = JSON.parse(fs.readFileSync(fp, 'utf-8'));
    res.json({ ...data, available: true });
  } catch (e) { res.status(500).json({ error: e.message }); }
});

module.exports = router;
