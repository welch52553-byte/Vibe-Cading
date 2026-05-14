# VIBE-CADING — AI 工作上下文

> 本文件是 AI 参与此项目的工作规范。开始工作前必须完整读取本文件。
> 本文件顶部内容为固定规范，**不允许修改**。

---

## 项目说明

本项目是一个 OpenSCAD 几何标注辅助工具。用户在浏览器中点选 3D 模型的面和边，添加标注后导出 JSON 文件。AI 读取 SCAD 源码 + JSON 标注，获得精确几何依据后再生成或修改代码。

```
用户标注面/边 → 导出 JSON → AI 读取 SCAD + JSON → 修改 SCAD → 保存至服务器 → 浏览器自动重新编译渲染
```

> 浏览器每 2 秒轮询 SCAD 文件的修改时间。AI 调用 `POST /api/save-scad` 写入文件后，浏览器会在 2 秒内自动检测到变化并重新编译渲染，**无需用户手动操作**。

---

## 每次工作前必须执行的步骤

**第一步：确认当前模型名称**（从用户的指令中获取，或询问用户）

**第二步：读取 SCAD 源码**

服务器运行在 `http://localhost:8080`，执行：
```
GET http://localhost:8080/api/scad?file={模型名}.scad
```
返回 JSON：`{"content": "...源码...", "mtime": 时间戳}`

**第三步：读取几何标注**

```
GET http://localhost:8080/api/json?file={模型名}.json
```

- 如果返回 `{"error": "not found"}` 或 faces/edges 均为空：
  告知用户先在浏览器 `http://localhost:8080/viewer/index.html` 完成标注并保存 JSON，再继续。

**第四步：确认上下文已加载，列出已标注的面和边，然后等待用户指令。**

---

## 修改 SCAD 的完整流程

### 第一步：生成修改后的完整 SCAD 内容

基于读取到的源码进行修改，得到完整的新版 SCAD 字符串。

### 第二步：通过 API 保存 SCAD 文件

```
POST http://localhost:8080/api/save-scad
Content-Type: application/json

{
  "filename": "{模型名}.scad",
  "content": "{完整的新版 SCAD 内容}"
}
```

返回 `{"ok": true, "saved": "{模型名}.scad"}` 表示成功。

保存后浏览器会在约 2 秒内自动重新编译并渲染新模型，**无需提示用户执行任何操作**。

### 第三步：更新几何标注 JSON

对照 SCAD 改动，逐一检查每个 face 和 edge 标注是否仍然有效：

- **几何仍然存在** → 推算并更新 `click_point`、`normal`、`area_mm2`、`length_mm` 等数据，`status` 保持 `"valid"`
- **几何已不存在或无法确定** → 保留原始数据，将 `status` 设为 `"invalid"`

将修正后的完整 JSON 写回：

```
POST http://localhost:8080/api/save-json
Content-Type: application/json

{
  "filename": "{模型名}.json",
  "content": "{完整的更新后 JSON 字符串}"
}
```

### 第四步：告知用户结果

```
已保存 {模型名}.scad，浏览器正在重新编译。
标注更新：
- face_001（顶面）：坐标已修正 ✓
- edge_a（前边缘）：已失效，请在浏览器重新标注 ⚠
```

---

## 几何操作规范

### 描述位置时必须引用标注 ID

```
✅ 正确："在 face_001（顶面，normal=[0,0,1]）中心打直径 6mm 的孔"
✅ 正确："对 edge_a（长 80mm，前边缘）做 1mm 圆角"
✅ 正确："沿 face_002 的法线方向偏移 3mm"
❌ 错误："在上面打个孔"（模糊，无法定位）
❌ 错误："在 [0,0,10] 处打孔"（直接用坐标，未引用标注）
```

如果在回复中无法引用任何标注 ID，说明 JSON 尚未读取，**必须先执行上面的读取步骤**。

### 坐标系

```
Z 轴（↑）= 上下，正方向朝上
X 轴（→）= 左右，正方向朝右
Y 轴（↗）= 前后，正方向朝前（屏幕外）
单位：毫米（mm）
```

| 语义 | 法线 |
|---|---|
| 顶面 TOP | [0, 0, 1] |
| 底面 BOTTOM | [0, 0, -1] |
| 前面 FRONT | [0, 1, 0] |
| 后面 BACK | [0, -1, 0] |
| 右侧面 RIGHT | [1, 0, 0] |
| 左侧面 LEFT | [-1, 0, 0] |

---

## JSON 标注格式参考

```json
{
  "version": "1.0",
  "scad_file": "example.scad",
  "faces": [
    {
      "id": "face_001",
      "label": "顶面",
      "normal": [0.00, 0.00, 1.00],
      "click_point": [0.0, 0.0, 10.0],
      "area_mm2": 4800.0,
      "semantic": "TOP",
      "notes": "放置开孔的主平面"
    }
  ],
  "edges": [
    {
      "id": "edge_a",
      "label": "a",
      "start": [40.0, -30.0, 10.0],
      "end": [-40.0, -30.0, 10.0],
      "midpoint": [0.0, -30.0, 10.0],
      "length_mm": 80.0,
      "notes": "顶面前边缘，需做 1mm 圆角"
    }
  ]
}
```

### status 字段说明

```json
{ "status": "valid" }    // 默认，标注有效（也可以不填此字段）
{ "status": "invalid" }  // 标注失效，浏览器将显示警告，用户需重新标注
```

---

## 服务器 API 速查

| 端点 | 方法 | 说明 |
|---|---|---|
| `/api/list-scad` | GET | 列出 model/ 目录中所有 .scad 文件 |
| `/api/scad?file=x.scad` | GET | 读取 SCAD 源码 + mtime |
| `/api/scad-mtime?file=x.scad` | GET | 仅返回 SCAD 修改时间戳 |
| `/api/json?file=x.json` | GET | 读取标注 JSON |
| `/api/save-scad` | POST | **写入 SCAD 文件（触发浏览器自动重编译）** |
| `/api/save-json` | POST | 写入标注 JSON |
