# Daydream Alert / Daydream Focus：运行与数据集制作（一步一步）

本文把你问的所有问题集中整理成“可直接照做”的步骤，包含：
- 如何在虚拟环境里运行本项目（含 `uv` 的推荐用法）
- `requirements.txt` 里依赖应不应该装在同一个虚拟环境
- labelImg 是否可以在虚拟环境安装、如何安装（以及避免冲突的推荐方式）
- 更详细、更完整的 YOLOv8 数据集制作与训练流程（按你的类别设计：`phone` / `head_down` / `no_person`）

> 说明：虚拟环境（venv）主要解决“依赖隔离/版本冲突”，并不会天然让程序更省 CPU/GPU；想降低运行负载，应优先关闭 YOLO/MediaPipe 等重模块。

---

## 1) 我应该如何运行这个项目（Windows，推荐虚拟环境）

### 1.1 前置条件
- Windows 10/11
- Python 3.11+（建议 64 位）
- 你已在本机有项目目录（例如 `D:\daydream`）
- 你已安装 `uv`

### 1.2 推荐方式：`uv` + venv（隔离依赖、安装更快）

在 PowerShell 中执行：

```powershell
cd D:\daydream

# 1) 创建虚拟环境（放在项目里，方便隔离）
uv venv .venv

# 2) 激活虚拟环境
#    如果你遇到 “脚本执行被禁用”，先执行下面这句（只对当前窗口生效）
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1

# 3) 安装依赖（本项目是 requirements.txt 形态）
uv pip install -r requirements.txt

# 4) （可选）安装开发/测试依赖
uv pip install -r requirements-dev.txt

# 5) 启动
python main.py
```

（可选）跑单测：
```powershell
pytest -q
```

### 1.3 备选方式：`python -m venv` + pip（不依赖 uv）

```powershell
cd D:\daydream
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r requirements-dev.txt
python main.py
```

---

## 2) “虚拟环境是不是更好/更省资源？”

虚拟环境的作用是：
- 隔离依赖：避免和其他项目的包/版本冲突（你担心的“插件/版本冲突”主要靠这个解决）
- 可复现：同一套依赖安装在 `.venv`，删掉就干净

它通常不会显著降低运行时资源占用（CPU/GPU/内存），因为：
- 运行时开销主要来自：摄像头采样、OpenCV、MediaPipe、YOLO 推理（尤其 YOLO）
- venv 只是“装在哪里不一样”，不是“跑起来更省”

想让它更轻量，建议优先做这几件：
- 在首页取消勾选：`启用手机检测（YOLOv8，CPU 上可能偏重）`
- 或取消勾选：`启用低头/视线粗判（MediaPipe）`
- 不想用摄像头时，直接取消勾选：`启用摄像头检测（建议开启）`

---

## 3) `requirements.txt` 里的 opencv-python / mediapipe / ultralytics 要装在同一个虚拟环境里吗？

如果你的目标是“运行这个项目”，那么答案是：建议装在同一个虚拟环境里。

原因：
- 程序运行时会 import 这些库（OpenCV 读摄像头帧、MediaPipe 粗判、Ultralytics YOLO 手机检测）
- 分散在多个环境会导致运行时找不到依赖

但有两个例外你可以拆开：
- **labelImg（标注工具）**：建议独立环境/独立安装（见第 4 节），避免 Qt 依赖冲突
- **训练环境**：如果你训练 YOLO 想用 GPU/CUDA，通常会有更复杂的 torch 版本匹配；把“训练”单独开一个 venv 会更稳（运行本项目的 venv 保持干净）

---

## 4) 我能不能在虚拟环境里装 labelImg？应该怎么做？

可以装在虚拟环境里；但我更推荐你“单独给 labelImg 一个虚拟环境”，原因是：
- labelImg 常用 PyQt5
- 本项目 GUI 用 PySide6
- 把两套 Qt 绑定装在同一个 venv 里，有时会出现冲突（不是必然，但一旦冲突会很烦）

### 方式 A（推荐）：labelImg 单独一个 venv（最稳）

```powershell
cd D:\daydream

# 1) 单独建一个 venv（与项目运行 venv 分开）
uv venv .venv-labelimg

# 2) 激活
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv-labelimg\Scripts\Activate.ps1

# 3) 安装并启动
uv pip install labelImg
labelImg
```

### 方式 B：下载 labelImg 的 Windows 发布包（不占用 Python 依赖）

你可以搜索并下载 labelImg 的 Windows release（zip/exe），解压后直接运行。
优点：完全不影响你的 Python 虚拟环境。

### 方式 C：装在本项目同一个 venv（不推荐，但可尝试）

如果你坚持同一个 venv（图省事），可以：

```powershell
cd D:\daydream
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
uv pip install labelImg
labelImg
```

如果出现 Qt 相关报错/打不开窗口，直接回到“方式 A”即可。

---

## 5) 我应该用 `uv sync` 吗？还是 `uv pip install -r ...`？

以当前仓库结构为准：
- 项目根目录只有 `requirements.txt` / `requirements-dev.txt`
- 没有 `pyproject.toml`

因此推荐用：
- `uv venv .venv`
- `uv pip install -r requirements.txt`（以及可选的 `requirements-dev.txt`）

`uv sync` 更适合 “`pyproject.toml` + lock 文件” 的项目形态；如果你未来想把本项目迁移到 `pyproject.toml`，再考虑 `uv sync` 会更顺滑。

---

## 6) YOLO 手机检测（权重文件）与“为什么我这里没反应”

本项目在运行时会检查项目根目录是否存在 `yolov8n.pt`：
- 存在：才会启用 YOLO 手机检测
- 不存在：会自动跳过（避免自动联网下载权重、避免卡住）

你可以选择：
- 不使用 YOLO：在首页取消勾选 `启用手机检测（YOLOv8，CPU 上可能偏重）`
- 使用 YOLO：把 `yolov8n.pt` 放到项目根目录 `D:\daydream\yolov8n.pt`

（可选）如果你想强制指定 YOLO 使用 CPU/GPU，可以在启动前设置环境变量（只对当前窗口生效）：

```powershell
$env:DAYDREAM_YOLO_DEVICE = "cpu"   # 或 "cuda"
python main.py
```

---

## 7) YOLOv8 数据集制作与训练（你指定的类别设计，完整版）

这部分就是“把 `phone/head_down/no_person` 做成可落地数据集”的一步一步流程。

### 7.1 类别设计（你采用的方案）
- `phone`：手里/桌面出现手机（检测到且持续出现 → 分神加权）
- `head_down`：低头（可选，主观更强，需要一致的标注标准）
- `no_person`：不建议用框标（更适合分类/规则：检测不到人脸/人离开）

> 建议顺序：先只做 `phone`，跑通流程；再做 `head_down`；`no_person` 用规则实现。

### 7.2 准备工作（建议先把目录结构定好）

```
dataset/
  images/
    train/
    val/
  labels/
    train/
    val/
  data.yaml
```

划分建议：
- `val` 至少留 10%（或 100–300 张起步）
- `val` 不要包含“相邻帧”（否则验证分数虚高）

### 7.3 采集素材（图片/视频抽帧）

起步数据量：
- `phone`：300–1000 张起步
- `head_down`：至少 300+ 张，并且“低头标准”必须一致

多样性清单（尽量覆盖）：
- 光线：白天 / 夜间 / 背光
- 角度：摄像头高/低/偏侧
- 手机：黑/白/带壳/反光/屏幕亮暗
- 行为：手持、贴脸、放桌面、半遮挡（手/杯子/书）
- 负样本：桌面上其他物体但没有手机

抽帧建议：
- 1fps 或 2fps（减少相邻帧重复）

### 7.4 标注工具（labelImg）

推荐：labelImg 单独一个 venv（见第 4 节）。

在 labelImg 中：
1) 选择保存格式 **YOLO**
2) 打开图片目录（例如 `dataset/images/train`）
3) 开始标注并保存

检查点：
- 每张 `xxx.jpg` 对应 `xxx.txt`
- `xxx.txt` 每行：`class_id x_center y_center w h`（0~1 归一化）

### 7.5 标注规范（决定你最后效果的关键）

#### `phone`（建议严格按这个标）
- 只框手机机身（不要把整只手框进去）
- 桌面手机也要框（因为你把它定义为“分神信号”）
- 多个手机：一个手机一个框
- 太小/太糊/完全不确定：可以不标（或单独当“难例”后续再加）

#### `head_down`（可选，但必须先写清“什么算低头”）
建议先写一个“可操作”的统一标准，比如：
- “低头”= 眼睛明显朝下 / 头部朝下倾斜明显，能稳定判断
- “非低头”= 只是轻微低一点，或者在看屏幕下半部但仍明显在看屏幕

框范围建议二选一并保持一致：
- 只框头部（含脸+头发）
- 框上半身（含头+肩）

#### `no_person`（不要框标）
用规则实现更合理：
- MediaPipe 检测不到脸 → `no_face`（本项目已有）

### 7.6 `data.yaml` 示例

阶段 1：只训练手机：

```yaml
path: dataset
train: images/train
val: images/val
names:
  0: phone
```

阶段 2：加入低头：

```yaml
path: dataset
train: images/train
val: images/val
names:
  0: phone
  1: head_down
```

### 7.7 训练（Ultralytics）

如果你在本项目虚拟环境里训练，这一步通常不需要额外安装（因为 `requirements.txt` 已包含 `ultralytics`）。

训练示例：

```powershell
yolo detect train data=dataset/data.yaml model=yolov8n.pt imgsz=640 epochs=30 batch=8
```

产物一般在：
- `runs/detect/train/weights/best.pt`

### 7.8 快速验证（不要跳过）

```powershell
yolo detect predict model=runs/detect/train/weights/best.pt source=dataset/images/val save=True conf=0.35
```

看输出图：
- 漏检多：补同类型数据，或调低 `conf`
- 误检多：补负样本（没有手机但很像手机的物体），并统一标注标准

### 7.9 接入本项目（你训练了自定义类别时要注意）

本项目默认用 COCO 的类别名 `cell phone` 来判断手机，如果你的自定义模型类别名是 `phone`，需要让代码匹配你的名字：
- 位置：`daydream_vision.py`、`app/vision/analyzer.py`
- 把判断 `cell phone` 的地方改为 `phone`

你也可以图省事：把自定义权重改名为 `yolov8n.pt` 放在项目根目录（并同步改类别判断）。

---

## 8) 你要找的“更详细教程”在哪里？

- 数据集制作/训练的专门文档：`docs\yolo8_dataset_tutorial.md`
- 本文（整合所有回答）：`doc\guidance_steps.md`
