# BlockExtractor
Module Technical Specification
模块技术规范
Version: v1.0.0-alpha
Schema Standard: JSON Schema Draft 2020-12

---

## 1. Module Identity
## 1. 模块标识

- module_name: `BlockExtractor`
- module_type: `LLM`
- primary_output: `BlockExtractionArtifact`
- downstream_dependencies:
  - `DeterministicRuleEngine`
  - `SemanticRiskDetector`

说明：

BlockExtractor 是系统的第一步，负责从图片中提取结构化文本块。
它是一个 LLM 模块，但职责仅限于“识读与分块”，不参与风险判断。

---

## 2. Purpose
## 2. 模块目标

BlockExtractor converts food label images into:

1) **raw_text_lines**: line-level, replayable extracted text
2) **blocks**: grouped functional/semantic regions

中文说明：

本模块的目标是将食品标签图片转换为：

1）原始文本行（raw_text_lines）——可回放、逐字忠实
2）结构化文本块（blocks）——按功能区分组

这些输出将作为后续规则引擎与语义检测的唯一输入依据。

---

## 3. Scope (Must / Must Not)
## 3. 范围定义（必须 / 禁止）

### 3.1 Must Do
### 3.1 必须执行

- Extract visible text from image(s) with maximal fidelity
- Produce `raw_text_lines` and `blocks`
- Provide `bbox` in normalized coordinates
- Preserve original text exactly (case, units, symbols)
- Ensure block text reproducible from referenced lines

中文说明：

必须：

- 逐字提取可见文本
- 输出文本行与分块
- 提供归一化坐标
- 保留大小写、单位、符号原样
- block 内容必须能由 line_refs 严格拼接复现

---

### 3.2 Must Not
### 3.2 严禁行为

- Must not output risk decisions
- Must not assign severity
- Must not perform missing checks
- Must not normalize units or correct spelling
- Must not merge unrelated regions into new sentences

中文说明：

严禁：

- 输出 risk_type 或 severity
- 判断缺失项
- 修改单位写法（如 ML → mL）
- 自动纠错或补全文本
- 跨区域拼接生成新句子

---

## 4. Inputs
## 4. 输入

### 4.1 Input Data
- One or multiple food label images

### 4.2 Multi-image Rule
- Each image = one `source_page`
- `source_page` starts from 1

中文说明：

若输入多张图片：

- 按顺序编号 source_page
- 不得混淆跨页文本

---

## 5. Outputs
## 5. 输出结构

Output must be a single JSON object.
Only JSON. No markdown fences. No extra explanation.

中文说明：

只允许输出一个合法 JSON 对象。
不得输出解释、前言或 markdown 包裹。

---

## 6. Coordinate System
## 6. 坐标系统

### 6.1 Fixed Choice
- `coordinate_system` = `"normalized"`

### 6.2 bbox Definition

```

{
"x": float,
"y": float,
"w": float,
"h": float
}

```

- range: 0.0 ~ 1.0
- (x, y) = top-left corner

中文说明：

所有坐标必须归一化。
禁止输出像素级绝对坐标。

---

## 7. raw_text_lines Specification
## 7. 原始文本行规范

### 7.1 Extraction Rules

- Extract by visual continuity
- Preserve text exactly
- Follow human reading order for rotated text

中文说明：

提取逻辑：

- 按视觉连续性提取
- 旋转/竖排按人类阅读顺序
- 不得推测缺字

---

### 7.2 Line Identity

- format: `L0001`, `L0002`, ...
- globally unique

中文说明：

必须全局唯一编号。

---

### 7.3 Line Confidence

Readability score only (not probability):

- 0.90~1.00 = clear
- 0.60~0.89 = minor issues
- 0.00~0.59 = unclear

中文说明：

confidence 表示“可读性”，
不是准确率概率。

---

## 8. blocks Specification
## 8. 分块规范

### 8.1 Block Formation

Group lines by functional region.

中文说明：

按功能区分块，例如：

- 配料表
- 营养成分表
- 标准号区域
- 生产者信息区域

---

### 8.2 Block Text Rules

- `text_raw` = join(line_refs, "\n")
- `text_final` = identical to `text_raw`

中文说明：

Alpha 阶段禁止做文本清洗。

---

### 8.3 Block Granularity Rule

Do not merge all marketing text into one giant block.

中文说明：

若有多个卖点条，应拆分成多个 `claim_strip`。

---

### 8.4 Block Identity

- format: `B0001`, `B0002`, ...
- globally unique

---

## 9. block_type Enumeration
## 9. 块类型枚举（闭集）

Allowed values:

- title
- claim_strip
- ingredient
- nutrition
- standard
- license
- producer
- date_shelf_life
- storage
- warning
- barcode
- other

中文说明：

block_type 必须严格使用上述枚举值，
不得新增或拼写变体。

---

## 10. Minimal Output Structure
## 10. 最小输出结构

必须输出：

- system_version
- module_name
- module_version
- spec_version
- schema_version
- coordinate_system
- image_size
- raw_text_lines[]
- blocks[]

中文说明：

禁止输出额外字段。

---

## 11. Internal Quality Checks
## 11. 内部自检（不输出）

- JSON 可解析
- 无尾逗号
- block_type 合法
- text_raw 可由 line_refs 严格复现
- 不包含 risk 相关字段

---

## 12. Error Handling
## 12. 异常处理

If partial extraction fails:
- Output what is reliable
- Lower confidence
- Do not hallucinate

If complete failure:
- Return valid JSON with empty arrays

中文说明：

宁可空，不可编造。

---

End of BlockExtractor TechSpec

---

## 13. Schema Alignment (v1.0.0-alpha)
## 13. 与Schema对齐（v1.0.0-alpha）

Authoritative schema file:

- `schemas/block.schema.json`

Key enforced constraints:

- `line_id` pattern: `^L\d{4,}$`
- `block_id` pattern: `^B\d{4,}$`
- `text` / `text_raw` / `text_final`: `minLength = 1`
- `bbox` values constrained to 0~1
- `source_page` >= 1
- `additionalProperties = false` for top-level and core sub-objects

中文说明：
- Dify 中的 BE Prompt 与输出校验请严格按 `schemas/block.schema.json` 对齐。
- schema 为最终契约，prompt 示例仅用于引导输出格式。

---

## Dify Runtime Baseline (Reference)
## Dify 运行基线（参考）

For current Dify deployment baseline, see:

- `prompts/block-extractor/model_config_v1.0.0-alpha.json`

中文说明：
- 该文件用于记录当前线上/联调用的模型与参数（如 model、temperature、top_p、json object 输出、视觉输入绑定等）。
- 未声明项默认沿用 Dify 平台默认值。

