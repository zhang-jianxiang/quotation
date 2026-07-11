# Genset Price Calculator — 发电机组价格计算工具

本地离线 HTML 价格计算工具，支持从 Excel 价格表提取数据并生成可搜索、可筛选的价格目录。

---

## 目录结构

```
D:/kc/code/quotation/
├── genset_price_tool.py              # 数据提取与工具生成脚本
├── genset_price_calculator.html      # 生成的价格计算器（直接双击打开）
├── genset_price_catalog.csv          # 整机价格目录（CSV）
├── genset_price_catalog.json         # 整机价格目录（JSON）
│   (symlink/copy → web/ + scf_deploy/index.js)
├── genset_alternator_price_catalog.csv  # 电机价格目录
├── genset_alternator_price_catalog.json
├── canopy_price_catalog.csv          # 静音箱价格目录
├── canopy_price_catalog.json
├── price_list_genset.xlsx            # 源数据：发电机组整机价格表
├── price_list_alternator.xlsx        # 源数据：发电机/电机价格表
├── LOGO.webp                         # 计算器网页 logo
│
├── scf_deploy/                       # 腾讯云 SCF 部署
│   ├── serverless.yaml               # Serverless Framework 配置
│   ├── index.js                      # SCF 函数入口（含加密数据）
│   ├── deploy_shanghai.js            # 腾讯云 SCF 直接部署脚本
│   └── build_scf.py                  # 构建 SCF 包（加密数据注入）
│
├── web/                              # 静态网页版（需要 Web 服务器）
│   ├── index.html                    # 网页入口
│   └── *.json                        # 价格数据文件
│
├── web_worker/                       # Cloudflare Workers 部署
│   ├── index.js                      # Worker 入口
│   ├── wrangler.toml                 # Wrangler 配置（需 API Token）
│   └── data/                         # 加密数据 blob
│
├── build_worker.py                   # 构建 Cloudflare Worker 数据包
├── build_scf.py                      # 构建腾讯云 SCF 数据包
├── DEPLOY_WORKFLOW_GENSET_CALCULATOR.md  # 完整部署工作流文档
└── regenerate_price_tool_prompt.md   # 重新生成工具的提示词模板
```

---

## 价格层级说明

整机价格分为四个层级：

| 层级 | 说明 | 计算公式 |
|------|------|---------|
| 成本核算 | 组件合计 + 管理费 | `组件合计 × 1.05` |
| 工厂底价 | 出厂参考价 | `成本核算 × 1.10` |
| 销售底价 | 销售最低价 | `成本核算 × 1.15` |
| 客户价 | 加上利润后的报价 | `工厂底价 × (1 + 利润率%)` |

### 组件明细（`5/6节距全铜` 方案）

| 组件 | 说明 |
|------|------|
| 柴油机 | 发动机 |
| 发电机 | 通常为 5/6 节距全铜电机 |
| 水箱 | 散热冷却 |
| 组装成套 | 装配工时 |
| 电气成套 | 电气控制系统 |
| 电瓶 | 启动电源 |
| 油箱 | 燃油存储 |
| 消音器 | 噪音控制 |
| 调试费 | 出厂调试 |

---

## 选配逻辑

### 1. 电机选配

整机默认搭配的电机记录在 Excel `5/6节距全铜` 列。

当用户为整机指定了 `Alternator Brand` 时，价格自动重算：

```
新成本 = 原成本 - 默认电机价 + 选中电机价
新工厂价 = 新成本 × 1.10
新销售价 = 新成本 × 1.15
客户价 = 新工厂价 × (1 + 利润率%)
```

**匹配规则：** 按所选电机品牌的功率列表，自动选取与整机发电机功率最接近的电机型号。

### 2. 静音箱 / 集装箱选配

当用户选择了箱体类型时，价格计算如下：

| 选配类型 | 说明 | 计算公式 |
|------|------|---------|
| 固定式静音箱（减成套费） | 标准静音箱体 | `最终成本 = 原成本 - 组装成套 - 消音器 + 箱体价格` |
| 移动式静音箱（底座油箱）（减成套费） | 移动式，含底座油箱 | `最终成本 = 原成本 - 组装成套 - 消音器 + 箱体价格` |
| 固定式防雨罩（底座油箱）（减成套费） | 防雨罩型 | `最终成本 = 原成本 - 组装成套 - 消音器 + 箱体价格` |
| 固定式静音集装箱（不减成套费） | 集装箱型，不扣组件 | `最终成本 = 原成本 + 箱体价格` |
| 移动拖车（挂式油箱）（不减成套费） | 挂式油箱拖车，不扣组件 | `最终成本 = 原成本 + 箱体价格` |
| 移动底盘（不含防雨罩静音箱） | 仅底盘，不含安装 | `最终成本 = 原成本 + 箱体价格` |
| 高速移动底盘（60-80码 不含防雨罩静音箱） | 高速底盘，不含安装 | `最终成本 = 原成本 + 箱体价格` |

静音箱 / 集装箱按功率范围匹配最优规格。

---

## 使用方法

### 首次使用 / 更新价格

价格表更新后，在项目目录下运行：

```powershell
python genset_price_tool.py
```

脚本会从 Excel 重新提取数据，自动生成：

- `genset_price_catalog.csv` / `.json` — 整机价格
- `alternator_price_catalog.csv` / `.json` — 电机价格
- `canopy_price_catalog.csv` / `.json` — 静音箱价格
- `genset_price_calculator.html` — 价格计算器网页

### 使用计算器

直接双击 `genset_price_calculator.html`，在浏览器中打开。

#### 上方面板 — 整机价格计算器

| 控件 | 说明 |
|------|------|
| Brand | 按品牌筛选，不选 = 全部品牌 |
| Power kW | 发电机功率（kW） |
| Tolerance kW | 功率容差，默认 0 |
| Alternator Brand | 选配电机品牌，默认使用整机标配电机 |
| Silent Canopy | 选配静音箱或静音集装箱 |
| Search | 搜索型号或分类 |
| Profit % | 利润率 %（影响客户价列） |

点击 **Copy prices** 复制当前筛选结果为 Tab 分隔格式，可直接粘贴到 Excel / WPS。

#### 下方面板 — 电机价格计算器

| 控件 | 说明 |
|------|------|
| Alternator Brand | 电机品牌筛选 |
| Power kW | 电机功率（kW） |
| Tolerance kW | 功率容差，默认 0 |
| Search | 搜索电机型号 |
| Profit % | 利润率 % |

点击 **Copy alternator prices** 复制电机筛选结果。

---

## 在线访问

### 腾讯云 SCF（推荐）
**亚太-上海:** https://service-1304419828-8e4a83fe-4b17-4bfa-bc8f-9a5dfa61f3d6.gz.ap-guangzhou.tencentcs.com

> API Gateway 已停售，当前使用 SCF 内置 HTTP 触发器，无需额外配置网关。

### Cloudflare Workers
**全球 CDN 加速:** （需部署时配置 `CLOUDFLARE_API_TOKEN`）

```bash
cd web_worker
npx wrangler deploy
```

Cloudflare 版本需要独立的 API Token。详见 `DEPLOY_WORKFLOW_GENSET_CALCULATOR.md`。

---

## 数据来源

### 整机价格表 `price_list_genset.xlsx`

每个 Sheet 对应一个品牌，字段包括：

- 主推型号、柴油机功率、发电机功率
- 各组件成本：柴油机、发电机（5/6节距全铜）、水箱、组装成套、电气成套、电瓶、油箱、消音器、调试费
- 成本核算、工厂底价、销售底价

### 电机价格表 `price_list_alternator.xlsx`

Sheet 名称为电机品牌，每个 Sheet 内可能有多个横向并排的价格表，提取字段：

- 电机型号、功率（kW）、价格（元）

### 静音箱价格 `price_list_genset.xlsx` — 箱体 Sheet

从箱体 Sheet 提取全部 7 类箱体数据：

- **固定式静音箱（减成套费）**：扣减组装/消音器费用
- **移动式静音箱（底座油箱）（减成套费）**：扣减组装/消音器费用
- **固定式防雨罩（底座油箱）（减成套费）**：扣减组装/消音器费用
- **固定式静音集装箱（不减成套费）**：不减组装/消音器费用
- **移动拖车（挂式油箱）（不减成套费）**：不减组装/消音器费用
- **移动底盘（不含防雨罩静音箱）**：不减
- **高速移动底盘（60-80码 不含防雨罩静音箱）**：不减

提取固定式静音箱功率范围、规格、尺寸、重量、油箱容量、备注等。

---

## 品牌排序

整机品牌下拉列表中，`重康` 始终排在 `东康` 之后，其他品牌按字母顺序排序。

---

## 技术实现

- **零第三方依赖**：仅使用 Python 标准库（`zipfile`、`xml.etree.ElementTree`、`re`、`csv`、`json`）
- **直接解析 XLSX**：读取 Excel 内部 XML 和公式缓存值，无需安装 Excel 或 openpyxl
- **完全离线**：生成的 HTML 文件不依赖任何网络资源，可完全离线使用
- **纯前端计算**：所有价格计算均在浏览器 JavaScript 中完成，无服务端依赖

---

## 故障排除

### 运行脚本报错

1. 确认 Python 版本 >= 3.10
2. 确认 `price_list_genset.xlsx` 和 `price_list_alternator.xlsx` 与脚本在同一目录
3. 确认 Excel 文件未以独占方式打开

### 计算器页面空白或报错

重新运行 `python genset_price_tool.py`，确保 JSON 数据文件是最新的。

### 找不到某品牌或型号

检查 Excel 原文件中该品牌是否有完整的"主推型号"、"发电机功率"、"成本核算"列标题。

---

## 提示词模板（重新生成工具时使用）

如需调整工具功能，参考 `regenerate_price_tool_prompt.md` 中的提示词模板，可发送给 AI 模型重新生成脚本。
