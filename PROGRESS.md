# SCAD 几何标注工具 — 项目进度文档

> 本文档是 AI 参与此项目的唯一参考文档。开始操作前必须完整阅读。
> 最后更新：2026-05-13

---

## 一、项目定位

### 核心问题

AI 辅助 OpenSCAD 建模时存在根本缺陷：**AI 和用户之间缺少共享的空间参照系**。

用户说"在顶面中间打个孔"，AI 靠猜。用户说"对那条边做倒角"，AI 不知道是哪条边。这不是 prompt 写得好不好的问题，而是整个交互机制缺少**几何指代能力**。

### 解决方案

```
用户在 3D 预览中点选面 / 边
        ↓
系统提取几何属性（法线、坐标、面积、长度等）
        ↓
用户贴标签和备注（face_001 / edge_a）
        ↓
导出结构化 JSON 文件
        ↓
AI 读取 SCAD + JSON → 收到精确几何依据 → 生成准确代码
```

### 参考项目

| 项目 | 参考价值 | 缺失的部分 |
|---|---|---|
| CADAM (Adam-CAD/CADAM) | React+Three.js 渲染管线，Claude API 架构 | 无几何 context 注入，无面/边交互 |
| FluidCAD (Fluid-CAD/FluidCAD) | 完整的面/边查询过滤 API 设计 | B-Rep 内核，非 OpenSCAD CSG |
| Pointer-CAD (CVPR 2026) | 确认"面/边选取"是 LLM+CAD 核心问题 | 需要 57.5 万训练数据 fine-tune |

本项目核心优势：**用户点选替代 LLM 预测**，无需训练，通用 LLM 即可工作。

---

## 二、项目文件结构

```
Vibe-Cading/
├── PROGRESS.md           # 本文件（项目说明 + AI 工作规范）
├── server.py             # 本地 HTTP 服务器（提供 REST API）
├── build.sh              # 编译 SCAD → STL，自动启动服务器
│
├── viewer/
│   └── index.html        # 核心工具：STL 查看器 + 标注界面（纯 HTML+JS）
│
└── model/
    ├── example.scad      # 示例 SCAD 文件
    ├── example.stl       # 编译输出（由 build.sh 生成）
    └── example.json      # 几何标注输出（由工具导出，供 AI 读取）
```

### 命名规则

SCAD / STL / JSON 三文件同名，只有后缀不同：
```
keyboard.scad → keyboard.stl → keyboard.json
```

---

## 三、本地服务器 API

服务器由 `python3 server.py 8080` 启动，监听 `localhost:8080`。

| 端点 | 方法 | 说明 |
|---|---|---|
| `GET /api/list-stl` | GET | 返回 model/ 目录下所有 .stl 文件名列表 |
| `GET /api/stl?file=x.stl` | GET | 返回 STL 二进制文件 |
| `GET /api/stl-mtime?file=x.stl` | GET | 返回 STL 最后修改时间戳 |
| `GET /api/scad?file=x.scad` | GET | 返回 SCAD 源码文本 + mtime |
| `GET /api/scad-mtime?file=x.scad` | GET | 返回 SCAD 最后修改时间戳 |
| `GET /api/json?file=x.json` | GET | 返回已保存的标注 JSON |
| `POST /api/save-json` | POST | 写入标注 JSON（body: `{filename, content}`） |

---

## 四、geometry.json 格式规范

```json
{
  "version": "1.0",
  "scad_file": "keyboard.scad",
  "stl_file": "keyboard.stl",
  "generated_at": "2026-05-13T10:30:00",
  "coordinate_system": "OpenSCAD (Z-up, mm)",
  "faces": [
    {
      "id": "face_001",
      "label": "键盘顶面",
      "normal": [0.00, 0.00, 1.00],
      "click_point": [0.0, 0.0, 10.0],
      "area_mm2": 4800.0,
      "semantic": "TOP",
      "semantic_confidence": 1.0,
      "notes": "放置按键开孔的主平面"
    }
  ],
  "edges": [
    {
      "id": "edge_a",
      "label": "a",
      "start": [40.0, -30.0, 10.0],
      "end": [-40.0, -30.0, 10.0],
      "midpoint": [0.0, -30.0, 10.0],
      "direction": [-1.00, 0.00, 0.00],
      "length_mm": 80.0,
      "notes": "顶面前边缘，需做 1mm 圆角"
    }
  ]
}
```

---

## 五、坐标系约定

```
Z 轴（↑）= 上下，正方向朝上
X 轴（→）= 左右，正方向朝右
Y 轴（↗）= 前后，正方向朝前（屏幕外）
单位：毫米（mm）
```

| 语义 | 方向 | 法线 |
|---|---|---|
| 顶面 TOP | +Z | [0, 0, 1] |
| 底面 BOTTOM | -Z | [0, 0, -1] |
| 前面 FRONT | +Y | [0, 1, 0] |
| 后面 BACK | -Y | [0, -1, 0] |
| 右侧面 RIGHT | +X | [1, 0, 0] |
| 左侧面 LEFT | -X | [-1, 0, 0] |

---

## 六、已实现功能

### 查看器（viewer/index.html）

- [x] STL 拖拽加载 + 按钮加载
- [x] Three.js WebGL 渲染 + OrbitControls
- [x] 左下角坐标轴指示器（实时随相机旋转）
- [x] 左侧 SCAD 预览面板（语法高亮，可折叠，自动监视更新）

### 面标注

- [x] Raycaster 点选面
- [x] **平面精确高亮**（法线 + 平面距离双重判断，不会误染同法线的其他面）
- [x] 几何属性提取：法线、点击坐标、面积估算、语义推断（TOP/BOTTOM/FRONT 等）
- [x] 已标注面显示独立颜色（10 色循环，蓝/绿/橙/紫等）
- [x] 标签下拉预设（BOSL2 语义锚点）

### 边标注

- [x] EdgesGeometry 提取模型边缘（15° 二面角阈值）
- [x] 点击边自动吸附（阈值随模型尺寸自适应）
- [x] 选中边黄色高亮，已标注边红色高亮
- [x] 边信息：长度、起点、终点、方向向量
- [x] 标签 ID 格式：edge_a / edge_b / edge_c ...
- [x] 标签下拉预设（a-l 小写字母）

### 标注面板

- [x] 面/边共用标注表单（标签 + 备注）
- [x] 统一标注列表，面显示蓝色"面"徽章，边显示橙色"边"徽章
- [x] 3D 浮标标签（CSS2DRenderer，面=红边框，边=橙边框）
- [x] 标签遮挡检测（被模型遮挡时自动隐藏）
- [x] 删除单个标注

### 文件工作流

- [x] 监视模式：启动后自动扫描 model/ 目录
- [x] 多 STL 时弹出选择框
- [x] STL 变化自动重载，标注保留
- [x] 点击"监视 STL"自动读取同名 JSON，恢复所有面和边标注
- [x] "保存 JSON" 直接写入 model/ 目录，无对话框
- [x] 下载 / 复制到剪贴板

### 本地服务器

- [x] server.py：静态文件 + REST API
- [x] build.sh：编译 SCAD + 自动启动服务器（端口已占用则跳过）
- [x] WSL 兼容：通过 localhost HTTP 完全绕过 File System Access API 限制

---

## 七、AI 工作规范

### 开始工作前必须做的事

1. 读取 `GET /api/scad?file=x.scad`，了解当前模型结构
2. 读取 `GET /api/json?file=x.json`，了解用户已标注的面/边
3. 如果 JSON 不存在或 faces/edges 为空，提示用户先在浏览器完成标注

### 描述几何位置时的规则

```
✅ 正确："在 face_001（顶面，normal=[0,0,1]）中心打直径 6mm 的孔"
✅ 正确："对 edge_a（长 80mm，前边缘）做 1mm 圆角"
✅ 正确："沿 face_002 的法线方向偏移 3mm"
❌ 错误："在上面打个孔"（模糊）
❌ 错误："在 [0,0,10] 处打孔"（直接用坐标，未引用标注）
```

### 修改 SCAD 后的提示

每次修改 SCAD 代码后，告知用户：
```
已修改 xxx.scad。
请运行：bash build.sh
浏览器将自动重载模型。
如果标注因几何变化失效，请告诉我哪些面/边发生了变化，
我会读取新的 JSON 并修正标注后保存。
```

### 标注修正工作流（几何变化后）

当模型形状改变导致标注失效时：
1. 用户告知 AI 哪些标注可能失效
2. AI 读取新的 SCAD + 当前 JSON
3. AI 理解几何变化，重新推算正确的 `click_point`、`normal`、`area_mm2` 等
4. AI 通过 `POST /api/save-json` 直接更新 JSON
5. 浏览器刷新后标注自动恢复

---

## 八、标准工作流程

```
① IDE + AI 编写/修改 xxx.scad
        ↓
② bash build.sh
   → 编译 SCAD → STL
   → 自动启动服务器（如未运行）
        ↓
③ Windows 浏览器访问 http://localhost:8080/viewer/index.html
   → 点击"监视 STL" → 选择 model/ 目录
   → 自动加载 STL + 恢复 JSON 标注
        ↓
④ 在 3D 视图中点选面/边 → 添加标注 → 保存 JSON
        ↓
⑤ 回到 IDE，告诉 AI：
   "请读取 xxx.scad 和 xxx.json，在 face_001 上增加..."
        ↓
⑥ AI 修改 SCAD → 回到 ②
```

---

## 九、待完成步骤

### 近期优先

- [x] **AI 对接 Skill（阶段 B）**：`/scad` Claude Code 命令（`.claude/commands/scad.md`）——自动从服务器读取 SCAD + JSON，注入几何上下文，约束 AI 操作规范
- [ ] **标注 prompt 生成**：在工具界面添加"复制 AI 上下文"按钮，一键生成包含当前所有标注的格式化 prompt 供直接粘贴给 AI

### 阶段 C 规划（直接 API 对接，最终目标）

AI 自主调用工具读取/写入几何数据，无需用户手动触发：

```
Claude Tool: read_scad(filename)   → 调用 GET /api/scad
Claude Tool: read_annotations(filename) → 调用 GET /api/json
Claude Tool: save_annotations(filename, json) → 调用 POST /api/save-json
```

实现方式选项：
- **MCP Server**：在 server.py 中追加 MCP 协议层，Claude Code 通过 `claude mcp add` 注册
- **Tool Use API**：在独立客户端中定义工具 schema，Claude API 自主决定何时调用

阶段 C 前提：阶段 B 的 prompt 模板格式 = 阶段 C 的 tool response 格式，可直接复用。

### 中期

- [ ] **边缘类型识别**：区分直线边和圆弧边，圆弧边提取半径和圆心
- [ ] **面/边重新匹配**（已有 AI 辅助方案，代码匹配作为备选）
- [ ] **标注状态标记**：模型更新后标记可能失效的标注为"⚠ 待确认"

### 后期

- [ ] 边（Edge）的点选标注完整化（圆弧边合并）
- [ ] 标注持久化跨 STL 重载（几何特征匹配）
- [ ] 多文件管理（同时标注多个 SCAD 组件）
- [ ] README 面向用户的使用文档

---

## 十、技术约束

- **无构建工具**：viewer/index.html 纯 HTML+JS，双击可运行（无服务器时功能受限）
- **CDN 依赖**：Three.js r158 via unpkg.com
- **WSL 兼容**：必须通过 `bash build.sh` 启动服务器后访问 localhost，不能直接双击 HTML
- **兼容性**：Chrome / Edge（File System Access API）；Firefox 降级为下载模式
