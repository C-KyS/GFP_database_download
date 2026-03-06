# GFP Database Download

从 [JIC GFP Database](https://data.jic.ac.uk/Gfp/) 下载 GFP 荧光图像与相差（Phase Contrast）图像，并将数据集划分为训练集和测试集。

## 最终目录结构

```
GFP_data/
├── Train/
│   ├── GFP/       # 训练集 GFP 荧光图像
│   └── PC/        # 训练集相差图像
└── Test/
    ├── GFP/       # 测试集 GFP 荧光图像
    └── PC/        # 测试集相差图像
```

## 使用方法

### 1. 安装依赖

```bash
pip install requests beautifulsoup4
```

### 2. 下载数据

```bash
python 1.py
```

脚本会自动从 JIC GFP 数据库爬取所有绿色荧光图像（`Green_Images/`）和灰度相差图像（`Gray_Images/`）。

### 3. 划分数据集

```bash
python split_dataset.py
```

将配对的图像随机划分为训练集（120 组）和测试集（28 组），输出到 `GFP_data/` 目录。
