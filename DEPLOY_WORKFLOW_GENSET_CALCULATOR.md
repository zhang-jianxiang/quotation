# Genset Price Calculator — Deploy Workflow

## Overview

Diesel generator set (发电机组) price calculator. When the source Excel price file is updated,
all outputs (catalog JSON/CSV + HTML calculator + Tencent Cloud SCF) must be regenerated and deployed.

**Project location:** `d:\kc\code\quotation`

---

## Step 1 — Replace Source Excel

1. **Backup old file:**
   ```powershell
   copy price_list_genset.xlsx price_list_genset_backup.xlsx
   ```

2. **Copy new file to replace:**
   ```powershell
   copy "path\to\new\genset_prices.xlsx" price_list_genset.xlsx
   ```

New file requirements:
- Same sheet names (= engine brands)
- Same column layout
- Contains a `箱体` (canopy) sheet
- Contains `成本核算`, `工厂底价`, `销售底价` columns

---

## Step 2 — Extract Data

```powershell
cd d:\kc\code\quotation
py -3 genset_price_tool.py
```

Reads `price_list_genset.xlsx` directly (no Excel needed). Produces:
- `genset_price_catalog.csv` + `.json`
- `genset_alternator_price_catalog.json`
- `canopy_price_catalog.csv` + `.json`
- `genset_price_calculator.html`

---

## Step 3 — Fix Calculator Column (if needed)

The HTML table columns map as follows:

| Column | Data |
|---|---|
| Brand | row.brand |
| Section | row.section |
| Model | row.model |
| Engine Power | row.engine_power |
| Genset Power | row.genset_kw |
| Default Alternator | row.default_alternator_price |
| Selected Alternator | selected alternator brand + model |
| Alternator Price | selected alternator price |
| Silent Canopy | canopy type + size |
| Box Price | canopy price |
| Deduct | assembly + silencer (if deduct=True) |
| Freight | user-entered freight |
| **Cost** | **Excel `成本核算` (`row.cost_book`)** ← original unit cost |
| Sales | `成本核算 × (1 + profit%)` |
| USD | Sales ÷ exchange rate |
| Source | sheet!row |

If the Cost column shows wrong values, check `genset_price_tool.py` — `cost_book`
is read from the `成本核算` column. All 1449 records should match Excel.

---

## Step 4 — Deploy to Tencent Cloud SCF

**Recommended.** Uses SCF built-in HTTP trigger (no API Gateway needed).

### Prerequisites
- Tencent Cloud CAM credentials in `scf_deploy/.env`:
  ```
  TENCENT_SECRET_ID=your_secret_id
  TENCENT_SECRET_KEY=your_secret_key
  ```

### Build + Deploy
```powershell
cd d:\kc\code\quotation

# 1. Build SCF package (encrypts data into index.js)
py -3 build_scf.py

# 2. Deploy to Tencent SCF (Shanghai region — has HTTP trigger)
cd scf_deploy
node deploy_shanghai.js
```

The script:
1. Zips `index.js` + `package.json`
2. Calls Tencent Cloud SDK `UpdateFunctionCode` on `genset-price-calculator-v2` in `ap-shanghai`
3. Lists triggers to confirm HTTP endpoint

**Live URL (Shanghai):**
```
http://1304419828-bmp0dava4a.ap-shanghai.tencentscf.com
https://service-1304419828-8e4a83fe-4b17-4bfa-bc8f-9a5dfa61f3d6.gz.ap-guangzhou.tencentcs.com
```

### If HTTP trigger is missing
```powershell
# Create HTTP trigger on the function
node -e "
const tencentcloud = require('./node_modules/tencentcloud-sdk-nodejs');
const ScfClient = tencentcloud.scf.v20180416.Client;
const client = new ScfClient({ credential: { secretId: '...', secretKey: '...' }, region: 'ap-shanghai' });
client.CreateTrigger({
  FunctionName: 'genset-price-calculator-v2',
  TriggerName: 'genset-http',
  Type: 'http',
  TriggerDesc: '{}',
}).then(console.log).catch(console.error);
"
```

### Region Notes
- **ap-guangzhou**: function exists, but no HTTP trigger (API Gateway discontinued)
- **ap-shanghai**: function exists with active HTTP trigger — use this for deploy

---

## Step 5 — Deploy to Cloudflare Workers (optional)

Cloudflare provides global CDN distribution. Requires `CLOUDFLARE_API_TOKEN`.

```powershell
cd d:\kc\code\quotation
py -3 build_worker.py

cd web_worker
npx wrangler deploy
```

KV namespace `DATA_KV` (id: `fb57c480b01d49ef90e2c0e76ea7a34d`) is pre-configured in `wrangler.toml`.

If `CLOUDFLARE_API_TOKEN` error:
```powershell
$env:CLOUDFLARE_API_TOKEN = "your-token-here"
cd web_worker
npx wrangler deploy
```

Get token: https://dash.cloudflare.com/profile/api-tokens
Template: **Edit Cloudflare Workers**

---

## File Summary

| File | Purpose |
|---|---|
| `price_list_genset.xlsx` | **Source** — genset prices per brand sheet |
| `genset_price_tool.py` | **Extractor** — XLSX → JSON/CSV/HTML |
| `genset_price_catalog.json` | **Data** — genset prices |
| `genset_alternator_price_catalog.json` | **Data** — alternator prices |
| `canopy_price_catalog.json` | **Data** — canopy prices |
| `genset_price_calculator.html` | **Output** — standalone calculator |
| `build_scf.py` | Encrypts JSON → `scf_deploy/index.js` |
| `scf_deploy/` | Tencent Cloud SCF deployment |
| `scf_deploy/deploy_shanghai.js` | Tencent SCF deploy script |
| `web/` | Static web version (needs web server) |
| `web_worker/` | Cloudflare Workers deployment |
| `DEPLOY_WORKFLOW_GENSET_CALCULATOR.md` | This file |

---

## Brand → Sheet Mapping

Sheets in `price_list_genset.xlsx` (= engine brands):
`上柴`, `玉柴`, `东风康明斯`, `潍柴`, `重康`, `奔驰`, `斗山`, `重庆`, `通柴`, `乾能`, `威曼`, `华柴`, `上柴 欧洲`, `玉柴 60HZ`, `斗山60HZ`, `卡特`, `帕金斯`, `大宇`, `沃沃`, `常柴`, `西门子`, `MTU`, `康明斯系统`, `玉柴燃气`, `三菱`, `珀琼斯`, `科勒`, `北柴`, `曼海姆`, `百力通`, `雅玛哈`, `合资品牌`, `进口品牌`, `上海东风发电机组`, `特殊品牌` + portable gensets (5-18KW, 3-24KW, 2-24KW), `箱体` (canopy)

Total: 34 sheets.

---

## Troubleshooting

**Calculator shows wrong cost price**
→ `cost_book` = Excel `成本核算` column. Run `genset_price_tool.py` again to re-extract.
If Excel `成本核算` column exists but extraction is wrong, the header detection may have failed.
Check `find_header()` in `genset_price_tool.py` — looks for ≥4 of: `主推型号`, `柴油机功率`, `发电机功率`, `成本核算`, `工厂底价`, `销售底价`.

**SCF deploy fails with "function not found"**
→ Check region: function `genset-price-calculator-v2` is in `ap-shanghai`. Update `region` in `deploy_shanghai.js`.

**SCF returns HTML but no data**
→ The SCF function serves embedded HTML. The calculator JS reads data from embedded encrypted JSON.
Run `build_scf.py` to re-encrypt the latest `genset_price_catalog.json` into `scf_deploy/index.js`.

**HTML calculator shows old prices after SCF deploy**
→ Run `build_scf.py` BEFORE `deploy_shanghai.js`. The deploy script updates the function code,
not the data — data is embedded inside `index.js` via `build_scf.py`.
