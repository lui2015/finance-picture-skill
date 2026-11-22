# finance-picture-skill

**用三张竖版知识卡，把一个金融概念讲清楚。**

这是一个 [WorkBuddy](https://www.workbuddy.cn/) Skill。给它一个金融小知识点（ROE、PE、毛利率、复利、市盈率……），它会产出三张 1080×1440 的竖版贴图，适合发小红书 / 视频号。三张图分别讲「是什么」「怎么算」「怎么用与避坑」。

核心取向是**文字为主、图片为辅**：先靠文字把知识点讲明白，卡通形象只做统一的视觉 IP 和配角。

## IP 固定：八戒

本系列的 IP **只能是「八戒」**——`assets/bajie-reference.jpg` 里那只粉白色 3D 招财小猪：黑金瓜皮帽配红宝石、蓝色袍子金袖口、双手捧福字金元宝，背景是浅蓝到暖金渐变加淡淡的 K 线、金币和上涨箭头。

- 系列名固定 **「八戒讲金融」**，右侧口诀标签用「八戒说人话」等八戒口径
- 生成三张插画时**必须**把这张图作为唯一参考图，并提高风格匹配度；角色描述逐字复用 `references/image-prompts.md` 里的固化锚点
- **禁止**换成其他动物、人物、吉祥物或另造角色，也不接受用户另选 IP —— 这是为了保证任何 AI、任何一期产出都是同一个八戒
- 三张插画里八戒的帽子、服装、元宝等识别元素不得改动

## 三张图各自讲什么

| 图 | 任务 | 每张包含 |
|---|---|---|
| 01 | 是什么 | 大标题、一句话导语、3 张要点卡、右下角口诀、底部金句 |
| 02 | 怎么算 | 公式拆解（分子/分母）、一个具体数字例子、完整公式金句 |
| 03 | 怎么用 | 2 条常见误用 + 1 条正确做法、避坑口诀 |

版式固定 1080×1440（3:4）：上方约 60% 是结构化文字，下方约 30% 是「左图右卡」配图区（完整八戒竖像 + 记忆口诀卡），底部约 5% 是金句条。

> 所有中文、数字和公式都由脚本用系统字体绘制，图像模型只负责画插画。这样能彻底避免 AI 生图常见的中文乱码和错字。

## 目录结构

```
finance-picture-skill/
├── SKILL.md                           Skill 入口：触发条件、完整工作流、硬性规则
├── README.md                          本文件
├── scripts/
│   └── make_cards.py                  通用排版引擎，读 config.json 输出三张图 + 预览
├── assets/
│   ├── bajie-reference.jpg            八戒 IP 唯一参考图（生成插画必用）
│   └── config.example.json            ROE 的完整示例配置
└── references/
    ├── image-prompts.md               八戒固化锚点、三张插画的图生图提示词模板
    └── layout-and-pitfalls.md         版式坐标、配色字号、文案结构、踩坑清单
```

## 安装

把本仓库放到用户级 Skill 目录：

```bash
git clone https://github.com/lui2015/finance-picture-skill.git \
  ~/.workbuddy/skills/finance-picture-skill
```

或者在 WorkBuddy 里直接说一句「用 finance-picture-skill 讲讲 PE」即可触发（若列表未刷新，重开会话）。

依赖：`Python 3` + `Pillow`。脚本的字体回退列表目前面向 macOS（冬青黑体 / 苹方 / 华文黑体 / Arial Unicode），在 Linux / Windows 上需要修改 `make_cards.py` 里的 `FONT_SPECS`。生成三张插画需要调用图像模型，会消耗额外积分（约 15–30）。

## 三步复用一个新概念

1. **写文案**：复制 `assets/config.example.json` 为 `config.json`，改 `cards` 里的三组文案（标题、导语、3 个要点、口诀、金句）。`label` 保持「八戒讲金融 · 第 N 课」。参考 `references/layout-and-pitfalls.md` 的字数与语气规范。
2. **生成插画**：按 `references/image-prompts.md` 的模板，**以 `assets/bajie-reference.jpg` 为唯一参考图**做图生图，产出三张**不含任何文字**的竖版插画，命名为 `scene1.png` / `scene2.png` / `scene3.png`。查看新插画后，重新量出 `portraits`（框住完整八戒的裁剪框）。
3. **排版出图**：

```bash
python3 scripts/make_cards.py /abs/path/to/config.json
```

输出：3 张 `1080×1440` PNG + 1 张三联预览图。逐张打开检查后再发布。

## config.json 关键字段

| 字段 | 说明 |
|---|---|
| `base_dir` | 素材与输出目录；相对路径按 config.json 所在目录解析 |
| `scenes` | 三张无文字插画的文件名 |
| `portraits` | 三个 `[x0,y0,x1,y1]`（原图坐标），框住完整八戒 |
| `clean_patches` | 可选，抹掉压住文字的背景元素（金币等），可为 `null` |
| `cards` | 三张卡的完整文案，含 `title` / `lead` / `points` / `aside` / `punch` |
| `preview` | 三联预览图文件名 |

`title` 支持分段着色：`[["ROE ", "gold"], ["到底是啥？", "navy"]]`，颜色可选 `navy` / `gold` / `red` / `slate`。

## 几条已验证的约定

- **IP 与系列名锁定为八戒**，任何 AI 调用都不得替换形象或改用其他称呼。
- 图像模型写中文必乱码，提示词里必须明确禁止任何文字、字母、数字。
- 三张插画复用同一参考图、同一段固化锚点描述，并提高风格匹配度，角色才不会漂。
- 插画铺满画面会喧宾夺主；配图区用「左图右卡」，不要留两侧大片空白。
- 角色裁剪框要框住完整八戒，只裁到额头/眼睛会切掉半张脸。
- 小字折行后不要留下只剩一两个字的孤行，改短文案比缩字号更好。
- 改版前备份上一版；改配置重跑，不要手工修图。

完整版见 `references/layout-and-pitfalls.md`。

## 示例

`assets/config.example.json` 是 **ROE** 的完整配置：第 1 课「ROE 到底是啥？」、第 2 课「那，怎么算？」、第 3 课「越高越好？别急！」，可直接拿来跑通全流程，也可以作为新概念的模板。
