/**
 * 合同路由 — 列表/预览/上传/删除
 */
const express = require('express');
const fs = require('fs');
const path = require('path');
const multer = require('multer');
const { authenticate, requirePermission } = require('../middleware/auth');
const router = express.Router();
const KB_DIR = path.resolve(__dirname, '../../knowledge-base');

router.use(authenticate);

function makeUpload(type) {
  return multer({
    storage: multer.diskStorage({
      destination: (req, file, cb) => {
        const dir = path.join(KB_DIR, 'contracts', type);
        if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
        cb(null, dir);
      },
      filename: (req, file, cb) => {
        cb(null, Buffer.from(file.originalname, 'latin1').toString('utf8'));
      }
    }),
    limits: { fileSize: 50*1024*1024 },
    fileFilter: (req,file,cb) => {
      const ok = ['.pdf','.doc','.docx','.xlsx','.xls','.jpg','.jpeg','.png','.json','.txt','.bmp','.svg'].includes(path.extname(file.originalname).toLowerCase());
      cb(ok ? null : new Error('不支持的类型'), ok);
    }
  });
}
const uploadPurchase = makeUpload('purchase');
const uploadSales = makeUpload('sales');

function list(type, res) {
  const dir = path.join(KB_DIR, 'contracts', type);
  if (!fs.existsSync(dir)) return res.json({ contracts: [], total: 0, note: '暂无合同，拖拽文件上传' });
  const files = fs.readdirSync(dir).filter(f => !f.startsWith('.'))
    .map(f => ({ name: f, url: `/api/contracts/${type}/files/${encodeURIComponent(f)}`, type: path.extname(f).toLowerCase(), size: fs.statSync(path.join(dir, f)).size }));
  res.json({ contracts: files, total: files.length, note: files.length===0?'暂无合同，拖拽文件上传':'' });
}

// List
router.get('/purchase', requirePermission('contracts:purchase:read'), (req,res) => list('purchase',res));
router.get('/sales', requirePermission('contracts:sales:read'), (req,res) => list('sales',res));

// Upload
router.post('/purchase/upload', requirePermission('contracts:purchase:read'), uploadPurchase.array('files',10), (req,res) => {
  res.json({ uploaded: (req.files||[]).map(f=>({name:f.filename,type:path.extname(f.filename),size:f.size})), total: (req.files||[]).length });
});
router.post('/sales/upload', requirePermission('contracts:sales:read'), uploadSales.array('files',10), (req,res) => {
  res.json({ uploaded: (req.files||[]).map(f=>({name:f.filename,type:path.extname(f.filename),size:f.size})), total: (req.files||[]).length });
});

// View/Download
router.get('/purchase/files/:filename', requirePermission('contracts:purchase:read'), (req,res) => {
  const fp = path.join(KB_DIR, 'contracts', 'purchase', decodeURIComponent(req.params.filename));
  if (!fs.existsSync(fp)) return res.status(404).json({error:'文件不存在'});
  res.sendFile(fp);
});
router.get('/sales/files/:filename', requirePermission('contracts:sales:read'), (req,res) => {
  const fp = path.join(KB_DIR, 'contracts', 'sales', decodeURIComponent(req.params.filename));
  if (!fs.existsSync(fp)) return res.status(404).json({error:'文件不存在'});
  res.sendFile(fp);
});

// Delete - separate per type to avoid path param confusion
router.delete('/purchase/files/:filename', requirePermission('contracts:purchase:read'), (req,res) => {
  const fp = path.join(KB_DIR, 'contracts', 'purchase', decodeURIComponent(req.params.filename));
  if (!fs.existsSync(fp)) return res.status(404).json({error:'文件不存在'});
  fs.unlinkSync(fp);
  res.json({message:'已删除',filename:req.params.filename});
});
router.delete('/sales/files/:filename', requirePermission('contracts:sales:read'), (req,res) => {
  const fp = path.join(KB_DIR, 'contracts', 'sales', decodeURIComponent(req.params.filename));
  if (!fs.existsSync(fp)) return res.status(404).json({error:'文件不存在'});
  fs.unlinkSync(fp);
  res.json({message:'已删除',filename:req.params.filename});
});

module.exports = router;
