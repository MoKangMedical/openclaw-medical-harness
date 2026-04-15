# 生物医药 GEO/SEO 策略方案

## 什么是 GEO？

**GEO = Generative Engine Optimization**
让内容被 ChatGPT、Claude、Perplexity 等 AI 引擎引用和推荐。

传统 SEO → 排在 Google 搜索结果第一页
GEO → 被 AI 直接引用为权威来源

在生物医药领域，这意味着：
- 研究者问 ChatGPT "医疗AI Agent框架" → 推荐你的项目
- 医生问 Claude "罕见病诊断工具" → 引用你的文档
- 投资人问 Perplexity "医疗AI初创公司" → 出现你的品牌

---

## 核心策略（6层）

### L1: Schema.org 结构化数据（最关键）

AI 引擎通过结构化数据理解内容语义。

```json
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "OpenClaw-Medical-Harness",
  "applicationCategory": "MedicalApplication",
  "operatingSystem": "Cross-platform",
  "description": "Medical AI Agent Orchestration Framework",
  "author": {
    "@type": "Organization",
    "name": "MoKangMedical"
  },
  "citation": [
    {"@type": "ScholarlyArticle", "name": "Harness Theory in AI Systems"},
    {"@type": "ScholarlyArticle", "name": "Medical AI Agent Architecture"}
  ]
}
```

**为什么关键**：这是 AI 引擎"理解"你项目的元数据入口。

### L2: E-E-A-T 权威性建设

Google 和 AI 引擎都看重 Experience, Expertise, Authoritativeness, Trustworthiness。

实施：
- [x] GitHub 组织认证
- [ ] 每个项目添加作者简介（医学/AI背景）
- [ ] 引用 PubMed/PMC 文献
- [ ] 添加使用案例和引用数据
- [ ] 创建 ORCID / Google Scholar Profile

### L3: AI 可引用内容格式

LLM 最容易引用的内容格式：
1. **清晰的定义** — "X 是一种 Y，用于 Z"
2. **数字和统计数据** — "性能提升 64%"
3. **对比表格** — A vs B vs C
4. **步骤列表** — 1, 2, 3, 4, 5
5. **FAQ 问答** — 直接回答常见问题

### L4: 内容矩阵

| 内容类型 | 频率 | 目标关键词 | 平台 |
|---------|------|-----------|------|
| 技术博客 | 2周/篇 | "medical AI agent framework" | GitHub Pages / Blog |
| 白皮书 | 1月/份 | "harness theory AI" | GitHub / ResearchGate |
| 案例研究 | 随项目 | "rare disease diagnosis AI" | GitHub Pages |
| 中文科普 | 1周/篇 | "医疗AI框架" | 知乎 / 公众号 |
| 视频demo | 随版本 | "medical AI demo" | B站 / YouTube |

### L5: 技术 SEO

- [x] GitHub Pages HTTPS
- [x] 移动端响应式
- [x] 页面加载速度
- [ ] Sitemap.xml
- [ ] robots.txt
- [ ] Open Graph / Twitter Cards
- [ ] Canonical URLs
- [ ] 代码块语法高亮（AI 引擎更好理解代码）

### L6: 跨平台分发

| 平台 | 目的 | 操作 |
|------|------|------|
| GitHub | 代码权威性 | README优化、Topics标签 |
| PyPI | 包发现 | 完整描述、关键词 |
| Hacker News | 技术社区曝光 | 发布 Show HN |
| Reddit | r/MachineLearning | 发布项目介绍 |
| Twitter/X | KOL传播 | 技术线程 |
| 知乎 | 中文搜索 | 技术文章 |
| PubMed Central | 学术引用 | 发布技术报告 |

---

## 即刻实施清单

### 1. README 优化（最高优先级）

README 是 AI 引擎最常抓取的内容。

**优化要点**：
- 第一段用清晰定义（"X 是 Y，用于 Z"）
- 包含具体数据（性能指标、用户数量）
- 对比表格（与竞品的区别）
- 代码示例（可运行的）
- FAQ 问答格式
- 引用的参考文献

### 2. Schema.org 标记

在每个 GitHub Pages 页面添加 JSON-LD。

### 3. GitHub Topics 标签

为每个 repo 添加准确的 Topics：
`medical-ai`, `drug-discovery`, `rare-disease`, `agent-framework`, `mcp`, `openclaw`

### 4. 每个 Repo 的 SEO

- 清晰的 description（GitHub 搜索会用到）
- 完整的 README（带架构图和代码示例）
- LICENSE 文件
- CONTRIBUTING.md
- 响应式 GitHub Pages 落地页

---

## KPI 追踪

| 指标 | 工具 | 目标（3个月） |
|------|------|--------------|
| GitHub Stars | GitHub | 100+ |
| PyPI 下载量 | PyPI Stats | 500+/月 |
| AI 引用次数 | 手动检查 | 被 3+ AI 引擎引用 |
| Google 排名 | Search Console | "medical AI framework" Top 20 |
| 社交分享 | 各平台 | 10+ 技术社区提及 |
