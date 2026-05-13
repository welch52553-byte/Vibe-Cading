# /scad — 加载 OpenSCAD 模型几何上下文

**用法：** `/scad [文件名]`
例：`/scad example` 或 `/scad keyboard`（无需后缀）
不带参数时自动选取 model/ 目录中第一个 STL。

---

## 执行步骤

**第一步：确定目标文件名**

如果 `$ARGUMENTS` 不为空，则 `BASE=$ARGUMENTS`（自动去掉 .scad/.stl/.json 后缀）。

否则运行：
```bash
curl -s http://localhost:8080/api/list-stl
```
取返回列表的第一个文件名，去掉 `.stl` 后缀作为 `BASE`。

---

**第二步：读取 SCAD 源码**

```bash
curl -s "http://localhost:8080/api/scad?file=${BASE}.scad"
```

提取返回 JSON 的 `content` 字段，这就是当前模型的完整源码。

---

**第三步：读取几何标注**

```bash
curl -s "http://localhost:8080/api/json?file=${BASE}.json"
```

- 如果返回 `{"error": "not found"}`，告知用户：
  > 尚未找到 `${BASE}.json`，请先在浏览器 `http://localhost:8080/viewer/index.html` 中完成面/边标注并保存 JSON，再使用此命令。

- 如果 `faces` 和 `edges` 均为空数组，同样提示用户先完成标注。

---

**第四步：输出上下文摘要**

整理后用以下格式输出，让用户确认上下文已正确加载：

```
📐 模型已加载：{BASE}.scad
━━━━━━━━━━━━━━━━━━━━━━━
面标注（{N} 个）：
  · face_001 — {label}（{semantic}，法线 {normal}）
  · face_002 — ...

边标注（{M} 个）：
  · edge_a — {label}（长 {length_mm}mm）
  · edge_b — ...
━━━━━━━━━━━━━━━━━━━━━━━
请告诉我需要做什么修改？
```

---

## 后续操作规范

收到用户指令后，严格按 PROGRESS.md 第七节"AI 工作规范"执行：

1. **描述几何位置必须引用标注 ID**
   - ✅ `在 face_001（顶面，normal=[0,0,1]）中心打直径 6mm 的孔`
   - ❌ `在上面打个孔`

2. **修改 SCAD 后告知用户**
   ```
   已修改 {BASE}.scad。
   请运行：bash build.sh
   浏览器将自动重载模型。
   ```

3. **标注失效时的修正流程**
   - 用户告知哪些标注可能失效
   - 读取新 SCAD，推算正确的 click_point / normal / area_mm2
   - 通过以下命令更新 JSON：
   ```bash
   curl -s -X POST http://localhost:8080/api/save-json \
     -H "Content-Type: application/json" \
     -d '{"filename": "${BASE}.json", "content": "<更新后的完整JSON字符串>"}'
   ```
