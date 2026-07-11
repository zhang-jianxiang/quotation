# 价格计算工具重新生成提示词

下面这段可以作为下次重新生成工具时的提示词使用：

```text
请分析当前目录下的价格表：

1. price_list_genset.xlsx 是柴油发电机组整机价格表。
2. price_list_alternator.xlsx 是电机/发电机价格表。

请生成一个本地离线 HTML 价格计算工具，并同时导出 CSV/JSON 数据。

要求：

一、整机价格表处理
- 从 price_list_genset.xlsx 提取各品牌 sheet 的整机数据。
- 主要字段包括：
  - 品牌/Sheet
  - 型号
  - 柴油机功率
  - 发电机功率 kW
  - 5/6节距全铜
  - 成本核算
  - 工厂底价
  - 销售底价
  - 来源 sheet 和行号
- 整机默认计算逻辑：
  - 成本核算 = 组件合计 * 1.05
  - 工厂底价 = 成本核算 * 1.10
  - 销售底价 = 成本核算 * 1.15

二、电机价格表处理
- 从 price_list_alternator.xlsx 提取电机价格。
- 因为很多 sheet 里有多个横向并排价格表，需要按局部表格块识别：
  - 电机品牌 = sheet 名
  - 电机型号
  - 功率 kW
  - 价格
  - 来源 sheet、行号、列号
- 需要生成 alternator_price_catalog.csv 和 alternator_price_catalog.json。

三、整机选择电机后的价格替换逻辑
- price_list_genset.xlsx 中的 `5/6节距全铜` 是整机默认电机价格。
- 如果用户在整机计算器里选择了 alternator brand，则整机价格应自动重算：
  - 新成本 = 原成本 - 默认电机价 * 1.05 + 选择电机价 * 1.05
  - 新工厂价 = 新成本 * 1.10
  - 新销售价 = 新成本 * 1.15
  - Custom = 新成本 * (1 + Markup %)
- 电机按整机发电机功率 kW 自动匹配同品牌最接近功率的电机。

四、HTML 页面功能
- 生成 genset_price_calculator.html。
- 页面上方是 Genset Price Calculator：
  - Brand 下拉选择
  - Power kW
  - Tolerance kW，默认值为 0
  - Alternator Brand 下拉选择，默认 Default alternator
  - Search
  - Markup %
  - Copy prices 按钮，复制为 tab 分隔格式，方便粘贴到 Excel/WPS
- 整机表格显示：
  - Brand
  - Section
  - Model
  - Engine Power
  - Genset Power
  - Default Alt
  - Selected Alt
  - Alt Price
  - Cost
  - Factory
  - Sales
  - Custom
  - Source
- 页面下方是 Alternator Price Calculator：
  - Alternator Brand
  - Power kW
  - Tolerance kW，默认值为 0
  - Search
  - Markup %
  - Copy alternator prices
- 电机表格显示：
  - Brand
  - Model
  - Power kW
  - Price
  - Custom
  - Source

五、品牌排序
- 整机品牌下拉列表中，`重康` 必须排在 `东康` 后面。

六、运行方式
- 不依赖 Excel 软件。
- 不依赖 openpyxl、pandas 等第三方库。
- 直接读取 xlsx 内部 XML 和公式缓存值。
- 生成一个 Python 脚本，例如 genset_price_tool.py。
- 运行：
  python genset_price_tool.py
- 输出：
  genset_price_catalog.csv
  genset_price_catalog.json
  alternator_price_catalog.csv
  alternator_price_catalog.json
  genset_price_calculator.html
```

价格表更新后，如果当前脚本还在，可以直接运行：

```powershell
python genset_price_tool.py
```

它会用新的 Excel 价格重新生成全部文件。
