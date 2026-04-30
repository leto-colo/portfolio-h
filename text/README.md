# Bad Case Runner · BC#001 多轮对话角色漂移测试

## 快速开始(5 分钟)

### 1. 安装依赖

```bash
pip install anthropic openai
```

### 2. 配置 API key

打开 `config.py`,把你的 key 填进去。或者用环境变量(更安全):

```bash
export ANTHROPIC_API_KEY=sk-ant-xxx
export DEEPSEEK_API_KEY=sk-xxx
```

### 3. 先跑连通性测试

```bash
python runner.py --test
```

这会只跑 G01 和 G04 各 1 组,验证两个 API 都能通。预计 1-2 分钟。

### 4. 跑全部 12 组

```bash
python runner.py
```

预计 10-15 分钟。中间断网了可以单独补跑某一组:

```bash
python runner.py G07
```

### 5. 标注

打开 `outputs/` 目录,12 个 markdown 一个一个看:
- 重点看**最后一轮**模型怎么回应诱导
- 在文件最底部填上漂移等级和观察笔记

---

## 常见问题

### Claude API 报 401

key 没填对,或者用了网页版 key(网页版不能调 API)。
去 https://console.anthropic.com 申请。

### DeepSeek API 国内能直连吗

能。注册地址 https://platform.deepseek.com,1 元充值能跑 1000+ 次。

### 我只想跑 Claude 的 6 组,DeepSeek 留到明天

```bash
python runner.py --model claude
```

### 我跑到一半想停

Ctrl+C。已经写好的 markdown 不会丢。

### 模型版本可以换吗

可以。在 `config.py` 改 `CLAUDE_MODEL` 或 `DEEPSEEK_MODEL`。
**但要在所有 12 组里用同一个版本**——不然实验失去可比性。

---

## 文件清单

```
bad_case_runner/
├── config.py              # 你填 API key 的地方
├── scenarios.py           # 12 组场景定义(可改)
├── runner.py              # 主脚本
├── README.md              # 本文件
└── outputs/               # 跑完后这里会有 12 个 .md
```
