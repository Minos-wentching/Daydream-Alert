# YOLOv8 数据集制作与训练（手把手）

目标：让模型能识别你的场景中“工作 / 分神 / 休息”，并支持更细粒度（如“低头”“看手机”）的扩展。

> 建议：先用“手机”作为目标（容易收集、直观），再做“低头/走神”等更主观的类别。

## A. 先明确你要标什么（类别设计）

### 方案 1（推荐：可落地、误判低）
- `phone`：手里/桌面出现手机（检测到且持续出现 → 分神加权）
- `head_down`：低头（可选，主观更强，需要一致的标注标准）
- `no_person`：不建议用框标（更适合分类/规则：检测不到人脸/人离开）

### 方案 2（三分类：work/distracted/rest）
这更像“分类”，而 YOLO 的强项是“目标检测”。如果你用 YOLO 做三分类，通常要把“整个人”框出来并贴标签，工作量更大且标准更难统一。

## B. 安装标注工具（推荐 labelImg）

### 方式 1：用 pip 安装（最省事）
```powershell
pip install labelImg
labelImg
```

### 方式 2：下载可执行版本
如果你不想装 Python 包，可以搜索 “labelImg windows release” 下载发布包（zip/exe），解压后运行。

## C. 采集素材（图片/视频抽帧）

建议先做 300~1000 张图片的小数据集：
- 光线：白天/晚上/背光
- 角度：笔记本摄像头高/低
- 行为：看屏幕、低头、拿手机、手机放桌面、手机贴脸

### 从视频抽帧（可选）
你可以用任意工具把自拍视频抽成 1fps/2fps 的图片，避免相邻帧太像。

## D. 标注规范（最重要）

统一标准能显著降低误判：
- 同一类别的框尽量覆盖目标主体（例如 `phone` 框住手机本体）
- 模糊/遮挡严重的样本：要么不标，要么单独放到“难例”集合，后续再加入训练
- 负样本也要保留（例如没有手机的图片），这样模型不会“见啥都像手机”

## E. 导出为 YOLO 格式

1) 在 labelImg 里选择保存格式为 **YOLO**
2) 每张图片会生成一个同名的 `.txt`
3) 目录结构建议：

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

`data.yaml` 示例：
```yaml
path: dataset
train: images/train
val: images/val
names:
  0: phone
```

## F. 用 Ultralytics 训练

安装依赖：
```powershell
pip install ultralytics
```

训练（CPU 也能跑，但慢）：
```powershell
yolo detect train data=dataset/data.yaml model=yolov8n.pt imgsz=640 epochs=50 batch=8
```

训练结束后，会生成权重文件（通常在 `runs/detect/train/weights/best.pt`）。

## G. 接入到本项目

v1 代码默认加载 `yolov8n.pt`，你训练好后可以替换为自己的权重：
- 把 `best.pt` 放到项目根目录（或你自定义路径）
- 然后在 `app/vision/analyzer.py` 里把 `YOLO("yolov8n.pt")` 改成你的文件名

## H. 标注/训练的小技巧

- 先做小而干净的数据集，快速训练，验证能否区分目标
- 发现误判后再补“难例”（例如手握黑色手机/反光/背光）
- 每次新增数据都保留一份独立 `val`，用来对比改进是否真实有效

