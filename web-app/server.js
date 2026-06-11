/**
 * 仪达质检知识库 — Web 服务器入口
 *
 * 启动: node server.js
 * 端口: 3000 (默认)
 */

const express = require('express');
const cors = require('cors');
const path = require('path');

const authRoutes = require('./routes/auth');
const productsRoutes = require('./routes/products');
const contractsRoutes = require('./routes/contracts');
const qaRoutes = require('./routes/qa');
const techSpecsRoutes = require('./routes/tech-specs');

const app = express();
const PORT = process.env.PORT || 3000;

// ── 中间件 ────────────────────────────────────────────
app.use(cors());
app.use(express.json());

// 静态文件服务（前端页面）
app.use(express.static(path.join(__dirname, 'public')));

// 图纸文件服务（无需认证，浏览器 img 标签不能带 JWT header）
app.use('/drawings', express.static(path.resolve(__dirname, '..', 'knowledge-base', 'drawings'), {
  setHeaders: (res) => { res.set('Cache-Control', 'public, max-age=3600'); }
}));

// ── API 路由 ──────────────────────────────────────────
app.use('/api/auth', authRoutes);
app.use('/api/products', productsRoutes);
app.use('/api/contracts', contractsRoutes);
app.use('/api/qa', qaRoutes);
app.use('/api/tech-specs', techSpecsRoutes);

// 健康检查
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', service: 'yida-quality-kb', time: new Date().toISOString() });
});

// ── 前端路由 ──────────────────────────────────────────
// 所有页面走同一个 HTML，JS 根据 pathname 判断显示登录还是主界面
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.get('/app', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// ── 404 ──────────────────────────────────────────────
app.use((req, res) => {
  res.status(404).json({ error: 'Not Found', path: req.path });
});

// ── 启动 ──────────────────────────────────────────────
// 显式绑定 0.0.0.0 解决 Windows IPv6 回环导致浏览器连不上的问题
app.listen(PORT, '0.0.0.0', () => {
  console.log('═'.repeat(50));
  console.log(`🔬 仪达质检知识库已启动`);
  console.log(`📍 http://localhost:${PORT}`);
  console.log(`🔑 登录页: http://localhost:${PORT}/`);
  console.log(`📱 主界面: http://localhost:${PORT}/app`);
  console.log(`❤️  健康检查: http://localhost:${PORT}/api/health`);
  console.log('═'.repeat(50));
  console.log('');
  console.log('预置账号:');
  console.log('  质检员小王 / 123456');
  console.log('  采购小李 / 123456');
  console.log('  销售小张 / 123456');
  console.log('  管理员 / admin123');
  console.log('');
});
