/**
 * 认证逻辑 — token 管理 + 登录/登出
 */
const API_BASE = '';

const Auth = {
  /** 获取存储的 token */
  getToken() {
    return localStorage.getItem('kb_token');
  },

  /** 获取用户信息 */
  getUser() {
    try {
      return JSON.parse(localStorage.getItem('kb_user') || 'null');
    } catch { return null; }
  },

  /** 检查是否已登录 */
  isLoggedIn() {
    return !!this.getToken();
  },

  /** 登录 */
  async login(username, password) {
    const res = await fetch(`${API_BASE}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || '登录失败');
    localStorage.setItem('kb_token', data.token);
    localStorage.setItem('kb_user', JSON.stringify(data.user));
    return data.user;
  },

  /** 登出 */
  logout() {
    localStorage.removeItem('kb_token');
    localStorage.removeItem('kb_user');
    window.location.href = '/';
  },

  /** 带认证的 fetch */
  async fetch(url, opts = {}) {
    const token = this.getToken();
    if (!token) {
      this.logout();
      throw new Error('未登录');
    }
    const headers = {
      ...opts.headers,
      'Authorization': `Bearer ${token}`,
    };
    if (opts.body && typeof opts.body === 'string') {
      headers['Content-Type'] = 'application/json';
    }
    const res = await fetch(`${API_BASE}${url}`, { ...opts, headers });
    if (res.status === 401) {
      this.logout();
      throw new Error('登录已过期');
    }
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || '请求失败');
    return data;
  },
};
