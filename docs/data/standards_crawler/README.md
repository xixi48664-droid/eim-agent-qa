# 标准爬虫系统使用说明

本目录用于按 `docs/data/行业规范录入格式.md` 生成行业规范 YAML。

## 环境要求

- Python 3.8+
- 依赖：`pip install requests beautifulsoup4 lxml pdfplumber pyyaml`

## 快速开始

在本目录运行：

```bash
python main.py
```

默认会根据文档“推荐收集的规范”和官方目录清单生成 YAML，输出到：

```text
docs/data/
```

## 命令参数

```bash
python main.py --source recommended
python main.py --source official
python main.py --source gb --max-pages 10
python main.py --source sjt --max-pages 5
python main.py --source jedec
python main.py --source ipc
python main.py --source iso
python main.py --source all --max-pages 10
python main.py --source gb --max-pages 10 --skip-enrich
```

默认 `--source all` 会先生成文档指定来源的官方目录条目，再访问可直接检索的官网补充元数据。

`recommended` 不访问网络，只生成推荐规范的 YAML 模板。`official` 生成 IPC、ISO、IEC、JEDEC、GB、SJ/T 等官网检索入口对应的标准目录 YAML。其它来源会访问对应网站，并在可获得 PDF 或元数据时生成 YAML。

除非指定 `--skip-enrich`，主程序最后会统一清理非真实 `section` 并重写 `summary`：

- `section` 只接受类似 `第 5 章 — 焊接`、`Chapter 5 Soldering`、`5.1 Soldering` 的真实章节编号和章节名称。
- 如果爬虫没有从 PDF、在线正文或可信目录页拿到真实章节，`section` 按录入规则留空。
- 一个标准如果有多个真实章节，输出器支持在同一个 YAML 文件中写入多条记录，每条记录一个 `section`。
- `summary` 聚焦电子信息制造业的应用重点，弱化标准来源、状态、发布日期等基础介绍。
- 国家标准详情页若显示“采标”或受验证码/FileOpen 控制，程序会保留官方详情 URL，但不会自行推断章节。

## 各标准来源说明

### GB/T 标准

- 通过国家标准全文公开系统按“电子、印制板、半导体、静电、电磁兼容、可靠性、环境试验”等关键词检索。
- 解析标准号、标准名称、状态、发布日期、实施日期和 `newGbInfo` 详情页 `hcno`。
- 生成的摘要会保留官方详情 URL，便于后续人工复核；最终摘要会通过补全步骤改写为电子信息制造业应用重点。未拿到 PDF/正文目录时 `section` 保持为空。

### SJ/T 行业标准

- 通过全国标准信息服务平台检索。
- 仅处理能找到 PDF 附件的结果。

### JEDEC 标准

- 通过 `crawlers/jedec_crawler.py` 中的 `JEDEC_STD_LIST` 控制采集清单。
- 自动搜索、下载 PDF，生成摘要和章节。

### 官方目录条目

- `crawlers/official_catalog.py` 维护来自 `行业规范录入格式.md` 所列来源的重点电子制造标准目录。
- 用于覆盖 IPC、ISO、IEC、JEDEC 等官网目录、付费标准或反爬限制导致无法稳定批量解析正文的来源。
- 每条记录仍按模板输出 6 个字段，并在摘要中保留对应官网检索 URL。

### IPC 标准

- 仅爬取 IPC 官网目录元数据。
- 付费正文不会自动下载，生成的 `summary` 会提示需要人工补充。

### ISO 标准

- 需要手动下载 ISO 开放数据 CSV。
- 放置于 `docs/data/standards_crawler/data/iso_standards.csv`。

## 输出格式

每个标准一个 YAML 文件，文件名来自规范编号归一化结果，例如 `IPC-A-610.yaml`、`GB_T_4588.3.yaml`。

文件内容固定为文档模板中的 6 个字段；同一标准的多个真实章节写成同一个 YAML 文件中的多个列表项：

```yaml
- standard_code: IPC-A-610
  standard_name: 电子组件的可接受性
  section: ''
  summary: ''
  tags: SMT,焊接,品质验收,IPC标准
  related_process: 回流焊,波峰焊,手工焊
```

`standard_name` 是必填字段。爬取来源返回语言字典或列表时，输出器会转换为字符串，以匹配录入格式。
