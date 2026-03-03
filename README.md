# Amazon Sales Report Analyzer

亚马逊销售报告分析工具

## 功能

- 自动检测报告目录和文件类型
- 智能识别报告周期（年/月/季度）
- 生成可视化 HTML 报告
- 支持筛选和排序 SKU 明细

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

# 查看帮助
python amazon_report_analyzer.py --help
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

- 核心数据：销售额、订单、客单价、转化率
- 广告数据：广告费、ROI、CTR、ACOS（如果有）
- SKU 明细：支持筛选和排序
- 退货分析：退货产品和原因统计

## 依赖

仅需 Python 3.x 标准库，无需额外安装。
