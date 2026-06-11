/**
 * JWT 认证中间件
 */

const jwt = require('jsonwebtoken');

const JWT_SECRET = process.env.JWT_SECRET || 'yida-quality-kb-secret-2026';
const JWT_EXPIRES_IN = '8h';

function generateToken(user) {
  return jwt.sign(
    { username: user.username, role: user.role, permissions: user.permissions },
    JWT_SECRET,
    { expiresIn: JWT_EXPIRES_IN }
  );
}

/** 验证 JWT token */
function authenticate(req, res, next) {
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ error: '未登录，请先登录' });
  }

  const token = authHeader.split(' ')[1];
  try {
    const decoded = jwt.verify(token, JWT_SECRET);
    req.user = decoded;
    next();
  } catch (err) {
    return res.status(401).json({ error: '登录已过期，请重新登录' });
  }
}

/** 检查特定权限 */
function requirePermission(permission) {
  return (req, res, next) => {
    if (!req.user) {
      return res.status(401).json({ error: '未登录' });
    }
    if (req.user.permissions.includes('*')) return next(); // admin
    if (req.user.permissions.includes(permission)) return next();
    return res.status(403).json({ error: '权限不足', required: permission });
  };
}

module.exports = { JWT_SECRET, generateToken, authenticate, requirePermission };
