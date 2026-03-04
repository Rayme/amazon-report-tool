# Amazon Sales Report Analyzer

亚马逊销售报告分析工具

## 功能

- 自动检测报告目录和文件类型
- 智能识别报告周期（年/月/季度）
- 生成可视化 HTML 报告
- 支持筛选和排序 SKU 明细
- **配置外部化**：通过 `config.json` 配置文件自定义国家、汇率、报告参数
- **详细日志**：支持控制台和文件日志输出
- **数据验证**：自动检查 CSV 文件完整性和数据质量
- **图表展示**：集成 ECharts，可视化销售数据、退货原因等

## 目录结构

将报告目录放入脚本同目录的 `amazon` 文件夹：

```
amazon_report_tool/
├── run.py                      # 双击运行
├── run_analyzer.bat            # Windows菜单运行
├── amazon_report_analyzer.py   # 主程序
├── README.md                   # 说明文档
└── amazon/                    # 报告数据目录
    ├── 2026JanReports/        # 2026年1月报告
    ├── 2026FebReports/        # 2026年2月报告
    ├── 2025Q4Reports/         # 2025年Q4报告
    └── ...
```

## 使用方法

### 方式一：双击运行 (Windows)

双击 `run_analyzer.bat` 或 `run.py`

### 方式二：命令行运行

```bash
# 自动检测并生成报告
python run.py

# 指定目录
python amazon_report_analyzer.py --dir amazon/2026FebReports

# 指定周期名称
python amazon_report_analyzer.py --dir amazon/2026FebReports --period "2026年2月"

# 指定输出文件名
python amazon_report_analyzer.py -d amazon/2026FebReports -o my_report.html

# 指定国家（可选）
python amazon_report_analyzer.py -d amazon -c DE FR

# 查看帮助
python amazon_report_analyzer.py --help
```

### 配置文件

程序支持通过 `config.json` 配置文件自定义设置：

```json
{
  "countries": {
    "DE": {"name": "德国", "currency": "EUR", "symbol": "€"}
  },
  "exchange_rates": {
    "EUR_USD": 1.08,
    "GBP_USD": 1.27
  },
  "report": {
    "sku_top_n": 50,
    "returns_top_n": 20
  }
}
```

### 日志输出

程序会自动输出日志，可重定向到文件：

```bash
python amazon_report_analyzer.py -d amazon 2>&1 | tee analyzer.log
```

## 支持的报告类型

| 类型 | 文件名关键词 |
|------|-------------|
| Business Report | BusinessReport |
| Transaction Report | Transaction |
| Returns Report | return, 退货 |
| 广告 Report | campaign, 广告 |

## 智能周期检测

工具会自动从目录名或文件名检测报告周期：
- `2026JanReports` → 2026年1月
- `2026FebReports` → 2026年2月
- `2025Q4Reports` → 2025年Q4
- `2025reports` → 2025年
- `2025NovDE` → 2025年11月

## 报告内容

- **汇总卡片**：总销售额、总订单、退货数量、广告花费
- **核心数据**：销售额、订单、客单价、转化率
- **图表展示**：
  - 各国家销售额分布（饼图）
  - Top 10 SKU 销售额（柱状图）
  - 退货原因分布（饼图）
  - 各国家订单分布（饼图）
- **广告数据**：广告费、ROI、CTR、ACOS（如果有）
- **SKU 明细**：支持筛选和排序
- **退货分析**：退货产品和原因统计

## 依赖

仅需 Python 3.x 标准库，无需额外安装。

报告中的图表使用 ECharts（通过 CDN 加载，需要联网）。
