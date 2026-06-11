/**
 * 认证路由 — /api/auth/*
 */
const express = require('express');
const path = require('path');
const bcrypt = require('bcryptjs');
const usersData = require(path.resolve(__dirname, '../../knowledge-base/users.json'));
const { generateToken, authenticate } = require('../middleware/auth');

const router = express.Router();

/** 登录 */
router.post('/login', (req, res) => {
  const { username, password } = req.body;
  if (!username || !password) {
    return res.status(400).json({ error: '请输入用户名和密码' });
  }

  const user = usersData.users.find(u => u.username === username);
  if (!user) {
    return res.status(401).json({ error: '用户名或密码错误' });
  }

  if (!bcrypt.compareSync(password, user.password)) {
    return res.status(401).json({ error: '用户名或密码错误' });
  }

  const token = generateToken(user);
  res.json({
    token,
    user: {
      username: user.username,
      displayName: user.displayName,
      role: user.role,
      permissions: user.permissions,
    },
  });
});

/** 获取当前用户信息 */
router.get('/me', authenticate, (req, res) => {
  const user = usersData.users.find(u => u.username === req.user.username);
  if (!user) return res.status(404).json({ error: '用户不存在' });
  res.json({
    username: user.username,
    displayName: user.displayName,
    role: user.role,
    permissions: user.permissions,
  });
});

/** 管理员：列出所有用户 */
router.get('/users', authenticate, (req, res) => {
  if (req.user.role !== 'admin') {
    return res.status(403).json({ error: '权限不足' });
  }
  const list = usersData.users.map(u => ({
    username: u.username,
    displayName: u.displayName,
    role: u.role,
    permissions: u.permissions,
  }));
  res.json({ users: list });
});

module.exports = router;
