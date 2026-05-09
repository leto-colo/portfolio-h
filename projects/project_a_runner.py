"""
Project A 实验脚本
主题：中文长文本摘要 Prompt 策略对比实验
实验设计：20 篇语料 × 5 种 Prompt 策略 × 2 模型 = 200 条数据

依赖：
    pip install openai python-dotenv

.env 格式（project_a.env）：
    DASHSCOPE_API_KEY=sk-xxx
    DOUBAO_API_KEY=ark-xxx
    DOUBAO_BASE_URL=https://ark.volces.com/api/v3
    DOUBAO_MODEL_ID=ep-xxx

运行：
    python project_a_runner.py
输出：
    project_a_results.json
"""

import os
import sys
import json
import time
import datetime
from dotenv import load_dotenv
from openai import OpenAI

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv(os.path.join(os.path.dirname(__file__), "project_a.env"))

# ──────────────────────────────────────────
# 模型配置
# ──────────────────────────────────────────

MODELS = {
    "qwen-plus": {
        "label": "Qwen-Plus",
        "client": OpenAI(
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        ),
        "model_id": "qwen-plus",
    },
    "doubao-pro": {
        "label": "Doubao-Pro",
        "client": OpenAI(
            api_key=os.getenv("DOUBAO_API_KEY"),
            base_url=os.getenv("DOUBAO_BASE_URL", "https://ark.volces.com/api/v3"),
        ),
        "model_id": os.getenv("DOUBAO_MODEL_ID", "ep-your-endpoint-id"),
    },
}

# ──────────────────────────────────────────
# 5 种 Prompt 策略
# ──────────────────────────────────────────

STRATEGIES = {
    "P0": {
        "name": "基线",
        "desc": "最简指令，无任何额外约束",
        "build": lambda text: f"请总结以下文章：\n\n{text}"
    },
    "P1": {
        "name": "长度约束",
        "desc": "加入不超过150字的硬性字数限制",
        "build": lambda text: f"请用不超过150字总结以下文章，不得超出字数限制：\n\n{text}"
    },
    "P2": {
        "name": "结构引导",
        "desc": "要求输出核心论点+关键数据+结论三段式结构",
        "build": lambda text: (
            f"请按照以下结构总结文章：\n"
            f"【核心论点】（文章的主要观点是什么）\n"
            f"【关键数据】（文章中的重要数字、事实或案例）\n"
            f"【结论】（文章的最终判断或建议）\n\n"
            f"文章内容：\n{text}"
        )
    },
    "P3": {
        "name": "受众设定",
        "desc": "为不懂技术的HR总结，要求通俗易懂",
        "build": lambda text: (
            f"请为一位不了解AI技术的HR撰写这篇文章的摘要。"
            f"要求：语言通俗易懂，避免专业术语，重点突出与招聘和人才相关的信息，"
            f"帮助HR快速理解文章的核心价值。\n\n"
            f"文章内容：\n{text}"
        )
    },
    "P4": {
        "name": "思维链",
        "desc": "先提炼关键信息再写摘要，显式分步推理",
        "build": lambda text: (
            f"请按以下步骤完成摘要任务：\n"
            f"第一步：列出文章中最重要的3-5个信息点\n"
            f"第二步：基于以上信息点，写出一段150字以内的摘要\n\n"
            f"文章内容：\n{text}"
        )
    },
}

# ──────────────────────────────────────────
# 打标维度说明（人工评估用）
# ──────────────────────────────────────────
EVAL_GUIDE = """
Project A 摘要质量评估维度：

【事实保留率】fact_retention
  3分：覆盖原文所有核心论点和关键数据，无遗漏
  2分：覆盖大部分核心论点，有少量遗漏但不影响主旨理解
  1分：仅覆盖部分内容，有重要信息缺失
  0分：严重遗漏或与原文主旨不符

【信息准确性】accuracy
  3分：所有信息均与原文一致，无错误或扭曲
  2分：基本准确，存在1-2处细节出入但不影响主旨
  1分：存在明显错误或对原文信息有明显扭曲
  0分：出现幻觉，生成了原文中不存在的信息

【简洁性】conciseness
  3分：表达高效，无冗余，信息密度高
  2分：基本简洁，有少量冗余表达
  1分：存在明显冗余，有效信息比例偏低
  0分：大量重复或填充性表述

【指令遵从】instruction_follow
  true：完整遵从了 Prompt 的所有要求（字数/格式/受众/步骤）
  false：未完整遵从

综合评分 total_score = fact_retention + accuracy + conciseness（满分9分）
"""


# ──────────────────────────────────────────
# 工具函数
# ──────────────────────────────────────────

def call_model(model_key: str, prompt: str, max_tokens: int = 600) -> str:
    cfg = MODELS[model_key]
    try:
        resp = cfg["client"].chat.completions.create(
            model=cfg["model_id"],
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,  # 摘要任务用低温度，减少随机性
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"ERROR: {e}"


# ──────────────────────────────────────────
# 主流程
# ──────────────────────────────────────────

def main():
    # 读取语料（和本脚本放在同一目录）
    corpus_path = os.path.join(os.path.dirname(__file__), "project_a_corpus.json")
    with open(corpus_path, "r", encoding="utf-8") as f:
        corpus = json.load(f)

    results = []
    total = len(corpus) * len(STRATEGIES) * len(MODELS)
    idx = 0

    print(f"Project A 实验启动")
    print(f"语料：{len(corpus)} 篇 × 策略：{len(STRATEGIES)} 种 × 模型：{len(MODELS)} 个 = {total} 条数据")
    print(f"{'─'*60}")
    print(EVAL_GUIDE)

    for doc in corpus:
        doc_id = doc["id"]
        doc_type = doc["type"]
        doc_topic = doc["topic"]
        text = doc["text"]
        ref_summary = doc["reference_summary"]

        print(f"\n文章 {doc_id} [{doc_type}] {doc_topic[:25]}...")

        for strat_key, strat in STRATEGIES.items():
            prompt = strat["build"](text)

            for m_key in MODELS:
                idx += 1
                model_label = MODELS[m_key]["label"]
                print(f"  [{idx:03d}/{total}] {strat_key}-{strat['name']} · {model_label}")

                output = call_model(m_key, prompt)
                time.sleep(0.8)

                record = {
                    "id": f"PA-{doc_id}-{strat_key}-{m_key}",
                    "doc_id": doc_id,
                    "doc_type": doc_type,
                    "doc_topic": doc_topic,
                    "model_key": m_key,
                    "model_label": model_label,
                    "strategy_key": strat_key,
                    "strategy_name": strat["name"],
                    "strategy_desc": strat["desc"],
                    "timestamp": datetime.datetime.now().isoformat(),
                    "prompt": prompt,
                    "output": output,
                    "reference_summary": ref_summary,
                    # 人工评估字段（跑完后填写）
                    "eval": {
                        "fact_retention": None,     # 0-3分：事实保留率
                        "accuracy": None,            # 0-3分：信息准确性
                        "conciseness": None,         # 0-3分：简洁性
                        "instruction_follow": None,  # true/false：指令遵从
                        "total_score": None,         # 综合评分（自动计算）
                        "note": ""                   # 备注
                    }
                }
                results.append(record)

                # 实时写盘，防止中途崩溃丢数据
                with open("project_a_results.json", "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)

                preview = output[:80].replace('\n', ' ')
                print(f"    → {preview}...")

    print(f"\n{'─'*60}")
    print(f"✅ 完成！共 {len(results)} 条记录，已保存至 project_a_results.json")
    print(f"\n下一步：打开 project_a_results.json，填写每条的 eval 字段")
    print(f"参考上方 EVAL_GUIDE 进行评分")
    print(f"total_score = fact_retention + accuracy + conciseness")


if __name__ == "__main__":
    main()
