import os
import random
import shutil

# 路径配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GREEN_DIR = os.path.join(BASE_DIR, "Green_Images")
GRAY_DIR = os.path.join(BASE_DIR, "Gray_Images")
OUTPUT_DIR = os.path.join(BASE_DIR, "GFP_data")

TRAIN_COUNT = 120
TEST_COUNT = 28

# 找到绿色和灰色图片都存在的配对（通过提取公共前缀）
green_files = {f.replace("_green.jpg", ""): f for f in os.listdir(GREEN_DIR) if f.endswith("_green.jpg")}
gray_files = {f.replace("_gray.jpg", ""): f for f in os.listdir(GRAY_DIR) if f.endswith("_gray.jpg")}

# 取交集，确保每组绿色和灰色图片都存在
paired_keys = sorted(set(green_files.keys()) & set(gray_files.keys()))
print(f"找到 {len(paired_keys)} 组配对图片")

if len(paired_keys) < TRAIN_COUNT + TEST_COUNT:
    print(f"警告: 配对图片数({len(paired_keys)})少于所需数量({TRAIN_COUNT + TEST_COUNT})，将按比例划分")
    total = len(paired_keys)
    TRAIN_COUNT = round(total * 120 / 148)
    TEST_COUNT = total - TRAIN_COUNT
    print(f"调整为: 训练集 {TRAIN_COUNT}, 测试集 {TEST_COUNT}")

# 随机打乱并划分
random.shuffle(paired_keys)
train_keys = paired_keys[:TRAIN_COUNT]
test_keys = paired_keys[TRAIN_COUNT:TRAIN_COUNT + TEST_COUNT]

# 创建目录结构
dirs = [
    os.path.join(OUTPUT_DIR, "Train", "GFP"),
    os.path.join(OUTPUT_DIR, "Train", "PC"),
    os.path.join(OUTPUT_DIR, "Test", "GFP"),
    os.path.join(OUTPUT_DIR, "Test", "PC"),
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# 复制文件
for key in train_keys:
    shutil.copy2(os.path.join(GREEN_DIR, green_files[key]), os.path.join(OUTPUT_DIR, "Train", "GFP", green_files[key]))
    shutil.copy2(os.path.join(GRAY_DIR, gray_files[key]), os.path.join(OUTPUT_DIR, "Train", "PC", gray_files[key]))

for key in test_keys:
    shutil.copy2(os.path.join(GREEN_DIR, green_files[key]), os.path.join(OUTPUT_DIR, "Test", "GFP", green_files[key]))
    shutil.copy2(os.path.join(GRAY_DIR, gray_files[key]), os.path.join(OUTPUT_DIR, "Test", "PC", gray_files[key]))

print(f"\n划分完成！")
print(f"训练集: {len(train_keys)} 组 (GFP: {len(os.listdir(dirs[0]))}, PC: {len(os.listdir(dirs[1]))})")
print(f"测试集: {len(test_keys)} 组 (GFP: {len(os.listdir(dirs[2]))}, PC: {len(os.listdir(dirs[3]))})")
