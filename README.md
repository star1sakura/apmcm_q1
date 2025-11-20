# 2025 APMCM Problem C - Question 1 Solution

本项目旨在解决 2025 年亚太地区大学生数学建模竞赛（APMCM）C 题的问题一。项目包含数据清洗、基准数据构建、Armington 替代模型建模以及关税政策冲击下的情景预测。

## 项目结构

```
.
├── 2025 APMCM Problems C/      # 原始赛题及附件数据
├── external_data/              # 外部补充数据（WITS 贸易数据）
├── output/                     # 输出结果文件夹
│   ├── cleaned_data/           # 清洗后的数据
│   ├── prediction_results/     # 预测结果
│   └── images/                 # 可视化图表
├── data_preprocessing.py       # 赛题附件数据清洗脚本
├── process_external_data.py    # 外部贸易数据清洗脚本
├── model_q1.py                 # 核心建模与预测脚本
├── visualization.py            # 结果可视化脚本
└── README.md                   # 项目说明文档
```

## 核心功能

1.  **数据预处理**：

    - 清洗 USITC DataWeb 贸易数据和 Tariff Database 关税数据。
    - 处理从 WITS 获取的中国分国别大豆进口数据（2020-2024）。

2.  **建模 (Armington Model)**：

    - 构建基于 Armington 假设的恒定替代弹性（CES）模型。
    - 以 2024 年为基准年，校准中国对美国、巴西、阿根廷大豆的偏好参数。

3.  **情景预测**：

    - **情景 1**：模拟中国对美国大豆加征 25% 报复性关税，其他国家关税不变。
    - **情景 2**：模拟关税冲击下，美国大豆离岸价格（FOB）下跌 10%，巴西/阿根廷价格上涨 5% 的市场反应。

4.  **结果可视化**：
    - 绘制历史贸易趋势图（进口量、市场份额）。
    - 绘制预测结果对比图（柱状图、饼图）。

## 使用说明

请按照以下顺序运行脚本：

1.  **清洗赛题附件数据**

    ```bash
    python data_preprocessing.py
    ```

    该脚本处理 `Tariff Data` 文件夹中的原始数据，生成美国出口和关税的基础清洗文件至 `output/cleaned_data/`。

2.  **处理外部贸易数据**

    ```bash
    python process_external_data.py
    ```

    该脚本读取 `external_data/` 中的 Excel 文件，提取并整理 2020-2024 年中国大豆进口数据，生成 `output/cleaned_data/china_soy_imports.csv`。这是模型运行的基准数据。

3.  **运行模型与预测**

    ```bash
    python model_q1.py
    ```

    该脚本读取基准数据，进行参数校准和情景模拟。运行完成后，将在 `output/prediction_results/` 目录下生成以下预测结果文件：

    - `prediction_results_scenario1.csv`: 情景 1（仅关税变化）预测结果。
    - `prediction_results_scenario2.csv`: 情景 2（关税+价格变化）预测结果。

4.  **生成可视化图表**
    ```bash
    python visualization.py
    ```
    该脚本读取清洗后的数据和预测结果，生成高质量图表至 `output/images/` 目录，包括：
    - 历史进口量趋势图
    - 历史市场份额堆叠图
    - 关税冲击前后出口量对比图
    - 市场份额变化对比饼图

## 输出文件说明

- **`output/cleaned_data/china_soy_imports.csv`**: 2020-2024 年中国自美、巴、阿三国进口大豆的历史数据（清洗后）。
- **`output/prediction_results/prediction_results_scenario1.csv`**: 预测结果表，包含各国的基准出口量 (`q0`)、预测出口量 (`q_new`)、变化量 (`delta_q`)、变化百分比 (`pct_change_q`) 及新的市场份额 (`share_new`)。
- **`output/cleaned_data/us_soybean_tariffs_cleaned.csv`**: 整理后的美国大豆相关关税历史数据。
- **`output/images/*.png`**: 用于论文写作的各类统计与预测图表。

## 依赖库

- pandas
- numpy
- openpyxl (用于读取 Excel 文件)
- matplotlib
- seaborn
