/**
 * 主应用逻辑
 */
const App = {
  user: null,
  currentView: 'products',
  products: [],

  /** 初始化 */
  async init() {
    if (!Auth.isLoggedIn()) {
      window.location.href = '/';
      return;
    }
    this.user = Auth.getUser();
    this.renderLayout();
    this.showProducts();
  },

  /** 渲染整体布局 */
  renderLayout() {
    const roleClass = `role-${this.user.role}`;
    const roleNames = { admin: '管理员', inspector: '质检员', purchaser: '采购', sales: '销售' };
    const roleName = roleNames[this.user.role] || this.user.role;

    const navItems = [];
    if (this.user.permissions.includes('products:read') || this.user.permissions.includes('*')) {
      navItems.push({ id: 'products', label: '📋 产品检规', badge: '' });
      navItems.push({ id: 'search', label: '🔍 搜索', badge: '' });
    }
    if (this.user.permissions.includes('qa:ask') || this.user.permissions.includes('*')) {
      navItems.push({ id: 'qa', label: '❓ AI 问答', badge: '' });
    }
    if (this.user.permissions.includes('contracts:purchase:read') || this.user.permissions.includes('*')) {
      navItems.push({ id: 'purchase', label: '📦 采购合同', badge: '' });
    }
    if (this.user.permissions.includes('contracts:sales:read') || this.user.permissions.includes('*')) {
      navItems.push({ id: 'sales', label: '💰 销售合同', badge: '' });
    }

    document.getElementById('app').innerHTML = `
      <div class="app-layout">
        <aside class="sidebar">
          <div class="sidebar-header">
            <h2>🔬 仪达质检知识库</h2>
            <small>智能热管理科技</small>
          </div>
          <nav class="sidebar-nav" id="sidebarNav">
            ${navItems.map(item => `
              <button class="nav-item ${item.id === 'products' ? 'active' : ''}"
                      onclick="App.switchView('${item.id}')">
                ${item.label}
                <span class="nav-badge" id="badge-${item.id}"></span>
              </button>
            `).join('')}
          </nav>
          <div class="sidebar-user">
            <div>👤 ${this.user.displayName}</div>
            <div class="role-badge ${roleClass}">${roleName}</div>
            <button style="display:block;margin-top:12px;background:none;border:1px solid rgba(255,255,255,0.3);color:white;padding:6px 12px;border-radius:6px;cursor:pointer;font-size:12px;"
                    onclick="Auth.logout()">退出登录</button>
          </div>
        </aside>
        <main class="main-content" id="mainContent"></main>
      </div>
    `;
  },

  /** 切换导航视图 */
  switchView(view) {
    this.currentView = view;
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    const activeBtn = document.querySelector(`.nav-item[onclick="App.switchView('${view}')"]`);
    if (activeBtn) activeBtn.classList.add('active');

    switch (view) {
      case 'products': this.showProducts(); break;
      case 'search': this.showSearch(); break;
      case 'qa': this.showQA(); break;
      case 'purchase': this.showContracts('purchase'); break;
      case 'sales': this.showContracts('sales'); break;
    }
  },

  /** 产品列表视图 */
  async showProducts() {
    try {
      const data = await Auth.fetch('/api/products');
      this.products = data.products || [];

      const html = `
        <div class="detail-header">
          <h2>产品检规列表</h2>
          <div class="meta-line">共 ${data.total || 0} 个产品，${data.totalCheckItems || 0} 条检验项目</div>
          ${data.generatedAt ? `<div class="meta-line">数据更新: ${new Date(data.generatedAt).toLocaleString('zh-CN')}</div>` : ''}
        </div>
        <div class="product-grid">
          ${this.products.length === 0
            ? '<div class="placeholder"><div class="icon">📭</div><p>暂无产品数据</p></div>'
            : this.products.map(p => `
              <div class="product-card" onclick="App.showProductDetail('${p.id}')">
                <h3>${p.productName}</h3>
                <div class="pid">${p.productId} | ${p.project || '-'}</div>
                <div class="meta">
                  <span class="tag ${p.importanceLevel === '安全部件' ? 'tag-safety' : p.importanceLevel === '重要部件' ? 'tag-important' : 'tag-general'}">
                    ${p.importanceLevel || '-'}
                  </span>
                  <span class="tag ${p.inspectionType === '进料检验' ? 'tag-incoming' : 'tag-process'}">
                    ${p.inspectionType || '-'}
                  </span>
                  <span class="tag" style="background:#f1f5f9;color:#64748b;">${p.totalCheckItems} 项</span>
                </div>
              </div>
            `).join('')}
        </div>
      `;

      document.getElementById('mainContent').innerHTML = html;
    } catch (err) {
      this.showError(err.message);
    }
  },

  /** 产品详情 */
  async showProductDetail(productId) {
    try {
      const product = await Auth.fetch(`/api/products/${productId}`);

      const html = `
        <button class="back-btn" onclick="App.showProducts()">← 返回列表</button>
        <div class="detail-header">
          <h2>${product.productName}</h2>
          <div class="meta-line">
            编号: ${product.productId} | 项目: ${product.project || '-'} | 等级: ${product.importanceLevel}
            | 类型: ${product.inspectionType} | 版本: ${product.version}
          </div>
          <div class="meta-line">
            编制: ${product.preparedBy || '-'} | 日期: ${product.preparedDate || '-'} | 文件: ${product.documentNumber || '-'}
          </div>
          <div class="meta-line">公司: ${product.company}</div>
        </div>
        <div class="checkitem-table">
          <table>
            <thead>
              <tr>
                <th>序号</th>
                <th>检验项目</th>
                <th>检验标准</th>
                <th>工具</th>
                <th>频次</th>
                <th>容量</th>
                <th>控制方法</th>
                <th>异常处理</th>
              </tr>
            </thead>
            <tbody>
              ${product.checkItems.map(item => `
                <tr>
                  <td class="seq-cell">${item.seq}</td>
                  <td class="cat-cell">${item.category}</td>
                  <td>${(item.standard || '').replace(/\n/g, '<br>')}${(()=>{const imgs=(item._imageRefs||[]).filter(r=>!r.isTechReq); return imgs.length?'<br>'+imgs.map(r=>`<img src="${r.url}" style="max-width:160px;max-height:100px;cursor:pointer;border:1px solid #e2e8f0;border-radius:4px;margin-top:4px;vertical-align:top" onclick="event.stopPropagation();App.lightbox(\'${r.url}\')" title="红圈${r.num}">`).join(' '):''})()}</td>
                  <td>${item.tool}</td>
                  <td>${item.frequency}</td>
                  <td>${item.sampleSize}</td>
                  <td>${item.controlMethod}</td>
                  <td>${item.reactionPlan}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
        ${product._allImages&&product._allImages.some(r=>r.isTechReq)?`<div style="margin-top:24px;background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:20px"><h3 style="margin-bottom:12px">📐 技术要求图纸</h3><div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px">${product._allImages.filter(r=>r.isTechReq).map(r=>`<div style="border:1px solid #e2e8f0;border-radius:8px;overflow:hidden;cursor:pointer" onclick="App.lightbox('${r.url}')"><img src="${r.url}" style="width:100%;height:160px;object-fit:contain;background:#f8fafc"><div style="font-size:10px;color:#64748b;padding:4px 8px;text-align:center">${r.name}</div></div>`).join('')}</div></div>`:''}
      `;

      document.getElementById('mainContent').innerHTML = html;
    } catch (err) {
      this.showError(err.message);
    }
  },

  /** 搜索视图 */
  async showSearch() {
    const html = `
      <div class="detail-header">
        <h2>🔍 搜索检规</h2>
        <div class="meta-line">搜索产品名称、编号、尺寸值、材料、工具等</div>
      </div>
      <div class="search-bar">
        <input type="text" id="searchInput" placeholder="例如: 824±1.5, 冷凝器, PU, GB 8410..."
               onkeydown="if(event.key==='Enter')App.doSearch()">
        <button onclick="App.doSearch()">搜索</button>
      </div>
      <div id="searchResults"></div>
    `;

    document.getElementById('mainContent').innerHTML = html;
  },

  /** 执行搜索 */
  async doSearch() {
    const q = document.getElementById('searchInput').value.trim();
    if (!q) return;

    try {
      const data = await Auth.fetch(`/api/products/search/all?q=${encodeURIComponent(q)}`);
      const resultsDiv = document.getElementById('searchResults');

      if (data.total === 0) {
        resultsDiv.innerHTML = `<div class="placeholder"><div class="icon">🔎</div><p>未找到 "${q}" 的相关结果</p></div>`;
        return;
      }

      resultsDiv.innerHTML = `
        <div style="margin-bottom:12px;color:var(--text-muted);">找到 ${data.total} 个相关产品</div>
        ${data.results.map(r => `
          <div class="product-card" onclick="App.showProductDetail('${r.id}')" style="margin-bottom:12px;">
            <h3>${r.productName} <span style="color:var(--primary);font-size:14px;">${r.metaMatch ? '⭐ 匹配' : ''}</span></h3>
            <div class="pid">${r.productId} | ${r.inspectionType} | ${r.importanceLevel}</div>
            ${r.matchedItems.length > 0 ? `
              <div style="margin-top:10px;border-top:1px solid var(--border);padding-top:10px;">
                ${r.matchedItems.map(item => `
                  <div style="padding:4px 0;font-size:13px;">
                    <b>#${item.seq} ${item.category}:</b>
                    ${item.standard.replace(new RegExp('(${q})', 'gi'), '<mark>$1</mark>')}
                    <span style="color:var(--text-muted);"> — ${item.tool}, ${item.frequency}</span>
                  </div>
                `).join('')}
              </div>
            ` : ''}
          </div>
        `).join('')}
      `;
    } catch (err) {
      this.showError(err.message);
    }
  },

  /** AI 问答视图 */
  async showQA() {
    const html = `
      <div class="detail-header">
        <h2>❓ AI 质检问答</h2>
        <div class="meta-line">基于知识库的智能问答 — 问产品标准、尺寸公差、材料规格等</div>
      </div>
      <div class="qa-panel">
        <h3>输入你的问题</h3>
        <div class="qa-input">
          <textarea id="qaQuestion" placeholder="例如: DS122的阻燃性标准是什么？冷凝器芯体的尺寸公差是多少？"></textarea>
          <button onclick="App.askQA()" id="qaAskBtn">提问</button>
        </div>
        <div id="qaAnswer" style="display:none;" class="qa-answer"></div>
      </div>
    `;

    document.getElementById('mainContent').innerHTML = html;
  },

  /** 执行问答 */
  async askQA() {
    const question = document.getElementById('qaQuestion').value.trim();
    if (!question) return;

    const btn = document.getElementById('qaAskBtn');
    const answerDiv = document.getElementById('qaAnswer');
    btn.disabled = true;
    btn.textContent = '思考中...';
    answerDiv.style.display = 'block';
    answerDiv.innerHTML = '⏳ 正在查询知识库...';

    try {
      const data = await Auth.fetch('/api/qa/ask', {
        method: 'POST',
        body: JSON.stringify({ question }),
      });

      answerDiv.innerHTML = `
        <span class="mode-tag ${data.mode === 'ai' ? 'mode-ai' : 'mode-offline'}">
          ${data.mode === 'ai' ? 'AI 回答' : '离线模式'}
        </span>
        <div style="white-space:pre-wrap">${data.answer}</div>
        ${(data.matchedProducts||[]).length > 0 ? `
        <div style="margin-top:16px;border-top:1px solid #e2e8f0;padding-top:12px">
          <strong>📐 关联图纸</strong>
          ${data.matchedProducts.map(mp => `
            <div style="margin:8px 0;padding:8px;background:#f8fafc;border-radius:6px">
              <div style="font-size:13px;font-weight:600;margin-bottom:4px;color:#1e293b">${mp.productName} <span style="color:#3b7dd8;font-family:monospace">${mp.productId}</span></div>
              <div style="display:flex;gap:8px;flex-wrap:wrap">
                ${(mp.drawings||[]).filter(d=>d.isImage&&!d.isTechReq).length === 0 ? '<span style="color:#94a3b8;font-size:12px">无标注图纸</span>' :
                  (mp.drawings||[]).filter(d=>d.isImage&&!d.isTechReq).map(d => `
                    <div style="cursor:pointer;text-align:center;width:140px" onclick="App.lightbox('${d.url}')">
                      <img src="${d.url}" style="width:140px;height:90px;object-fit:contain;background:#fff;border:1px solid #e2e8f0;border-radius:4px">
                      <div style="font-size:10px;color:#64748b">${d.name}</div>
                    </div>
                  `).join('')}
              </div>
            </div>
          `).join('')}
        </div>` : ''}
      `;
    } catch (err) {
      answerDiv.innerHTML = `<span class="mode-tag mode-offline">错误</span> ${err.message}`;
    } finally {
      btn.disabled = false;
      btn.textContent = '提问';
    }
  },

  /** 合同视图（预留） */
  async showContracts(type) {
    const label = type === 'purchase' ? '采购合同' : '销售合同';
    try {
      const data = await Auth.fetch(`/api/contracts/${type}`);
      const html = `
        <div class="detail-header">
          <h2>${label}</h2>
          <div class="meta-line">${data.note || `共 ${data.total} 份合同`}</div>
        </div>
        <div class="placeholder">
          <div class="icon">📂</div>
          <p>${data.note || '暂无合同数据'}</p>
          <p style="color:var(--text-muted);font-size:13px;">合同模块已预留，将合同文件放入 knowledge-base/contracts/ 目录即可生效</p>
        </div>
      `;
      document.getElementById('mainContent').innerHTML = html;
    } catch (err) {
      this.showError(err.message);
    }
  },

  /** 图片灯箱 */
  lightbox(url) {
    const div = document.createElement('div');
    div.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.92);z-index:9999;display:flex;align-items:center;justify-content:center;cursor:pointer';
    div.onclick = () => div.remove();
    const img = document.createElement('img');
    img.src = url;
    img.style.cssText = 'max-width:95vw;max-height:95vh';
    div.appendChild(img);
    document.body.appendChild(div);
  },

  /** 错误提示 */
  showError(msg) {
    const toast = document.createElement('div');
    toast.className = 'toast toast-error';
    toast.textContent = msg;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
  },
};

// 启动
document.addEventListener('DOMContentLoaded', () => App.init());
