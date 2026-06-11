/**
 * extract-kb.js — 将 Excel 检规文件抽取为结构化 JSON 知识库
 *
 * 输入: DS122 11615检规1.xlsx + P100204013检规(1).xlsx
 * 输出: knowledge-base/products/*.json + knowledge-base/index.json
 */

const XLSX = require('xlsx');
const fs = require('fs');
const path = require('path');

const DATA_DIR = path.resolve(__dirname, '..');
const KB_DIR = path.join(DATA_DIR, 'knowledge-base');
const PRODUCTS_DIR = path.join(KB_DIR, 'products');

// ── 工具函数 ──────────────────────────────────────────

/** 从 raw 行数组中找第一个非空单元格的值 */
function cellValue(row, colIndex) {
  if (colIndex >= row.length) return '';
  const v = row[colIndex];
  return v != null ? String(v).trim() : '';
}

/** 找真正的检验项目表头行（同时包含"序号"和"检验"的才算） */
function findHeaderRow(data) {
  for (let i = 0; i < Math.min(30, data.length); i++) {
    const row = data[i];
    if (!row) continue;
    const joined = row.map(c => String(c || '')).join('');
    // 必须同时有"序号"和"检验"，排除纯元数据行
    if ((joined.includes('序') || joined.includes('序号')) &&
        (joined.includes('检验项目') || joined.includes('检验标准'))) {
      return i;
    }
  }
  return -1;
}

/** 从一个可能有合并单元格的行中提取元数据字段 */
function extractMeta(data) {
  const meta = {
    project: '',
    productName: '',
    productId: '',
    documentNumber: '',
    version: 'A/0',
    importanceLevel: '',
    inspectionType: '',
    preparedBy: '',
    preparedDate: '',
    company: '',
  };

  // 扫描前几行找元数据
  for (let i = 0; i < Math.min(6, data.length); i++) {
    const row = data[i];
    if (!row) continue;
    const full = row.map(c => String(c || '').trim());

    for (let j = 0; j < full.length; j++) {
      const cell = full[j];
      if (cell === '项目' && j + 1 < full.length) meta.project = full[j + 1] || '';
      if ((cell === '产品名称' || cell.includes('产品名称')) && j + 1 < full.length)
        meta.productName = full.slice(j + 1).find(c => c && c !== '') || '';
      if (cell === '产品型号' && j + 1 < full.length) {
        // 产品型号 优先于 产品编号（DS122 用的是"产品型号"）
        const val = full.slice(j + 1, j + 5).find(c => c && c !== '' && !c.match(/^[A-Z]\/\d$/));
        if (val) meta.productId = val;
      }
      if ((cell === '产品编号' || cell.includes('产品编号')) && j + 1 < full.length) {
        const val = full.slice(j + 1, j + 5).find(c => c && c !== '' && !c.match(/^[A-Z]\/\d$/) && c !== '文本');
        if (val && !meta.productId) meta.productId = val;
      }
      if ((cell === '文本编号' || cell.includes('文本编号')) && j + 1 < full.length)
        meta.documentNumber = full.slice(j + 1).find(c => c && c !== '' && c !== 'A/0') || '';
      if ((cell === '版本' || cell.includes('版本')) && j + 1 < full.length) {
        const ver = full.slice(j + 1).find(c => c && c.match(/^[A-Z]\/\d$/));
        if (ver) meta.version = ver;
      }
      if (cell.includes('安全部件') || cell.includes('重要部件') || cell.includes('一般部件')) {
        if (full.join(' ').includes('■ 安全部件')) meta.importanceLevel = '安全部件';
        else if (full.join(' ').includes('■ 重要部件')) meta.importanceLevel = '重要部件';
        else if (full.join(' ').includes('■ 一般部件')) meta.importanceLevel = '一般部件';
      }
      if (cell === '产品型号') {
        const val = full.slice(j + 1).find(c => c && c !== '');
        if (val) meta.productId = val;
      }
    }
  }

  // 扫描后面找公司名和编制人
  for (let i = Math.max(5, data.length - 5); i < data.length; i++) {
    const row = data[i];
    if (!row) continue;
    const full = row.map(c => String(c || '').trim());
    const joined = full.join(' ');

    if (joined.includes('仪达') || joined.includes('马鞍山')) {
      meta.company = full.find(c => c.includes('仪达') || c.includes('马鞍山')) || meta.company;
    }
    if (joined.includes('首次检验规范') || joined.includes('编制检规')) {
      // 前一行有 A/0 日期 编制理由 签名
      meta.preparedDate = full[1] || '';
      meta.preparedBy = full[7] || full[8] || '';
    }
  }

  // 查进料检验 vs 制程检验（扫描全部行，因为 P100204013 的数据从很后面才开始）
  for (let i = 0; i < data.length; i++) {
    const row = data[i];
    if (!row) continue;
    const joined = row.map(c => String(c || '')).join('');
    if (joined.includes('进料检验')) { meta.inspectionType = '进料检验'; break; }
    if (joined.includes('制程检验')) { meta.inspectionType = '制程检验'; break; }
  }

  return meta;
}

/** 解析检验项目行 */
function extractCheckItems(data, headerRow) {
  const items = [];
  const headers = data[headerRow].map(c => String(c || '').trim());

  // 找到列索引：分级, 序号, 检验项目, 检验标准, 特殊特性, 检验工具, 检验容量, 检验频率, 控制方法, 反应计划
  const colMap = {};
  for (let i = 0; i < headers.length; i++) {
    const h = headers[i];
    if (h.replace(/\s/g, '').includes('分级')) colMap.level = i;
    if (h.replace(/\s/g, '').includes('序号')) colMap.seq = i;
    if (h.replace(/\s/g, '').includes('检验项目')) colMap.category = i;
    if (h.replace(/\s/g, '').includes('检验标准')) colMap.standard = i;
    if (h.replace(/\s/g, '').includes('特殊特性')) colMap.specialChar = i;
    if (h.replace(/\s/g, '').includes('检验工具')) colMap.tool = i;
    if (h.replace(/\s/g, '').includes('检验容量') || h.replace(/\s/g, '').includes('容量')) colMap.sampleSize = i;
    if (h.replace(/\s/g, '').includes('检验频率') || h.replace(/\s/g, '').includes('频率')) colMap.frequency = i;
    if (h.replace(/\s/g, '').includes('控制方法')) colMap.controlMethod = i;
    if (h.replace(/\s/g, '').includes('反应计划')) colMap.reactionPlan = i;
  }

  let currentCategory = '';
  let seq = 0;

  for (let i = headerRow + 1; i < data.length; i++) {
    const row = data[i];
    if (!row || row.length === 0) continue;

    const level = cellValue(row, colMap.level);
    const seqRaw = cellValue(row, colMap.seq);
    const category = cellValue(row, colMap.category);
    const standard = cellValue(row, colMap.standard);
    const tool = cellValue(row, colMap.tool);
    const sampleSize = cellValue(row, colMap.sampleSize);
    const frequency = cellValue(row, colMap.frequency);
    const controlMethod = cellValue(row, colMap.controlMethod);
    const reactionPlan = cellValue(row, colMap.reactionPlan);

    // 跳过空行 / 签名行 / 版本行
    if (!level && !seqRaw && !standard && !tool) {
      // 可能是后续标准行（没有序号的多行标准）
      if (standard || tool) {
        items.push({
          seq,
          category: currentCategory,
          standard,
          tool,
          sampleSize,
          frequency,
          controlMethod: controlMethod || '',
          reactionPlan: reactionPlan || '',
        });
      }
      continue;
    }

    // 有检验项目名称 → 更新当前类别
    if (category && !seqRaw && !standard && !tool) {
      // 可能是分组标签
      continue;
    }

    // 有序号的新条目
    if (seqRaw && !isNaN(parseInt(seqRaw))) {
      seq = parseInt(seqRaw);
      if (category) currentCategory = category;
    }

    // 有检验标准就创建条目
    if (standard || tool) {
      items.push({
        seq,
        category: category || currentCategory,
        standard,
        tool,
        sampleSize,
        frequency,
        controlMethod: controlMethod || '',
        reactionPlan: reactionPlan || '',
      });
    }

    // 终止条件：遇到编制签名行
    const full = row.map(c => String(c || ''));
    if (full.join('').includes('编制') && full.join('').includes('审核')) break;
  }

  return items;
}

// ── 主流程 ────────────────────────────────────────────

function parseExcel(filePath, fileName) {
  console.log(`\n📄 解析: ${fileName}`);
  const wb = XLSX.readFile(filePath);
  const products = [];

  for (const sheetName of wb.SheetNames) {
    const ws = wb.Sheets[sheetName];
    const data = XLSX.utils.sheet_to_json(ws, { header: 1, defval: '' });
    if (data.length < 5) {
      console.log(`  ⏭ 跳过空 sheet: ${sheetName}`);
      continue;
    }

    console.log(`  📋 Sheet: ${sheetName} (${data.length} 行)`);

    // 提取元数据
    const meta = extractMeta(data);

    // 找表头行（必须同时有"序号"和"检验"）
    const headerRow = findHeaderRow(data);
    if (headerRow === -1) {
      console.log(`  ⚠ 找不到检验项目表头，跳过`);
      continue;
    }

    // 如果表头下面一行包含同样的表头关键词（合并单元格导致的重复），使用下面那行
    // 实际表头在确认位置
    console.log(`  📌 表头行: ${headerRow}`);

    // 提取检验项目
    const checkItems = extractCheckItems(data, headerRow);
    console.log(`  ✅ 提取 ${checkItems.length} 条检验项目`);

    if (checkItems.length === 0) continue;

    // 补全元数据
    if (!meta.productName && sheetName.includes('集流管')) meta.productName = '集流管';
    if (!meta.productName && sheetName.includes('翅片')) meta.productName = '翅片';
    if (!meta.productId && sheetName.includes('206003')) meta.productId = 'P100206003';
    if (!meta.productId && sheetName.includes('206004')) meta.productId = 'P100206004';
    if (!meta.productId && sheetName.includes('204006')) meta.productId = 'P100204006';

    const productId = meta.productId || sheetName.replace(/[()\s]/g, '');
    const safeId = productId.replace(/[^a-zA-Z0-9_-]/g, '-');

    const product = {
      productId,
      project: meta.project,
      productName: meta.productName,
      importanceLevel: meta.importanceLevel,
      version: meta.version,
      preparedBy: meta.preparedBy,
      preparedDate: meta.preparedDate,
      company: meta.company || '仪达智能热管理科技（马鞍山）有限公司',
      documentNumber: meta.documentNumber,
      inspectionType: meta.inspectionType,
      sourceFile: fileName,
      sourceSheet: sheetName,
      totalCheckItems: checkItems.length,
      checkItems,
    };

    products.push({ id: safeId, product });
  }

  return products;
}

// ── 执行 ──────────────────────────────────────────────

function main() {
  console.log('🔧 南洋万邦质检知识库 — 数据抽取');
  console.log('═'.repeat(50));

  // 确保目录存在
  [KB_DIR, PRODUCTS_DIR].forEach(d => {
    if (!fs.existsSync(d)) fs.mkdirSync(d, { recursive: true });
  });

  const allProducts = [];

  // 文件 1: DS122
  const ds122Path = path.join(DATA_DIR, 'DS122 11615检规1.xlsx');
  if (fs.existsSync(ds122Path)) {
    const products = parseExcel(ds122Path, 'DS122 11615检规1.xlsx');
    allProducts.push(...products);
  } else {
    console.log('⚠ DS122 检规文件未找到');
  }

  // 文件 2: P100204013
  const p100Path = path.join(DATA_DIR, 'P100204013检规(1).xlsx');
  if (fs.existsSync(p100Path)) {
    const products = parseExcel(p100Path, 'P100204013检规(1).xlsx');
    allProducts.push(...products);
  } else {
    console.log('⚠ P100204013 检规文件未找到');
  }

  // 写入各产品 JSON
  console.log(`\n📝 写入产品 JSON...`);
  for (const { id, product } of allProducts) {
    const filePath = path.join(PRODUCTS_DIR, `${id}.json`);
    fs.writeFileSync(filePath, JSON.stringify(product, null, 2), 'utf-8');
    console.log(`  ✅ ${id}.json (${product.totalCheckItems} 条)`);
  }

  // 写入全局索引
  const index = {
    generatedAt: new Date().toISOString(),
    totalProducts: allProducts.length,
    totalCheckItems: allProducts.reduce((s, p) => s + p.product.totalCheckItems, 0),
    products: allProducts.map(({ id, product }) => ({
      id,
      productId: product.productId,
      project: product.project,
      productName: product.productName,
      importanceLevel: product.importanceLevel,
      inspectionType: product.inspectionType,
      company: product.company,
      totalCheckItems: product.totalCheckItems,
    })),
  };

  fs.writeFileSync(
    path.join(KB_DIR, 'index.json'),
    JSON.stringify(index, null, 2),
    'utf-8'
  );
  console.log(`\n📊 索引: ${index.totalProducts} 产品, ${index.totalCheckItems} 条检验项`);
  console.log('═'.repeat(50));
  console.log('✅ 知识库抽取完成!');
}

main();
