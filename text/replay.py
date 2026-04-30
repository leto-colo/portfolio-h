"""
replay.py · BC#001 复现实验

用法:
    python replay.py G08 --times 4

说明:
    - 用与原实验完全一致的条件(系统提示/热身/诱导/temperature)重复跑 N 次
    - 输出到 outputs/replay_G08/ 子目录,文件名带 _r1/_r2/_r3/_r4 后缀
    - 不会覆盖原 G08 markdown(原文件保留作为 r0)
"""
import argparse
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from config import OUTPUT_DIR
from scenarios import SYSTEM_PROMPT, get_scenario
from runner import call_deepseek, write_markdown


# ===== Qwen 调用器(原脚本里没有,这里补上)=====
def call_qwen(messages: list, system: str) -> str:
    """阿里云 Qwen,通过 DashScope OpenAI 兼容接口调用。"""
    from openai import OpenAI
    qwen_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_API_KEY")
    if not qwen_key:
        raise RuntimeError("请设置环境变量 DASHSCOPE_API_KEY 或 QWEN_API_KEY")
    client = OpenAI(
        api_key=qwen_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    full_messages = [{"role": "system", "content": system}] + messages
    resp = client.chat.completions.create(
        model="qwen-plus",
        messages=full_messages,
        max_tokens=1024,
        temperature=0.7,
    )
    return resp.choices[0].message.content


CALL_FN = {
    "claude": call_qwen,
    "deepseek": call_deepseek,
    "qwen": call_qwen,
}


def run_once(scenario: dict, run_idx: int, output_dir: Path):
    """跑一次完整对话,保存到指定目录,文件名带 _r{idx}。"""
    sid = scenario["id"]
    model = scenario["model"]
    print(f"\n{'='*60}")
    print(f"[{sid} · 第 {run_idx} 次复现] {model} · {scenario['induction_type']}")
    print(f"{'='*60}")

    call_fn = CALL_FN[model]
    messages = []

    # 热身
    for i, user_msg in enumerate(scenario["warmup"], start=1):
        print(f"\n[轮 {i}] {user_msg[:40]}...")
        messages.append({"role": "user", "content": user_msg})
        try:
            reply = call_fn(messages, SYSTEM_PROMPT)
        except Exception as e:
            print(f"  ❌ 失败: {e}")
            return False
        messages.append({"role": "assistant", "content": reply})
        print(f"  → {reply[:60]}...")
        time.sleep(1)

    # 诱导
    induction_idx = len(scenario["warmup"]) + 1
    print(f"\n[轮 {induction_idx} ⚠️ 诱导] {scenario['induction_turn'][:50]}...")
    messages.append({"role": "user", "content": scenario["induction_turn"]})
    try:
        reply = call_fn(messages, SYSTEM_PROMPT)
    except Exception as e:
        print(f"  ❌ 失败: {e}")
        return False
    messages.append({"role": "assistant", "content": reply})
    print(f"  → {reply[:200]}")  # 关键回复多打一些

    # 写文件
    result = {
        "id": f"{sid}_r{run_idx}",
        "model": model,
        "induction_type": scenario["induction_type"],
        "induction_turn_idx": induction_idx,
        "turns": messages,
        "model_version": "qwen-plus" if model == "qwen" else (
            "claude-opus-4-5" if model == "claude" else "deepseek-chat"
        ),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    write_markdown(result, str(output_dir))
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("scenario_id", help="要复现的场景,如 G08")
    parser.add_argument("--times", type=int, default=4, help="重复次数(默认 4 次,加上原实验共 5 次)")
    args = parser.parse_args()

    scenario = get_scenario(args.scenario_id)
    # 注意:原 G08 在 scenarios.py 里 model 写的是 "claude",
    # 但你实际把 Claude 换成了 Qwen,所以这里强制改成 qwen
    if scenario["model"] == "claude":
        scenario = {**scenario, "model": "qwen"}
        print(f"⚠️  原场景 model=claude,实测用的是 qwen,已自动切换")

    out_dir = Path(OUTPUT_DIR) / f"replay_{args.scenario_id}"
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 输出目录:{out_dir.absolute()}\n")

    success = 0
    for i in range(1, args.times + 1):
        if run_once(scenario, i, out_dir):
            success += 1
        time.sleep(2)

    print(f"\n{'='*60}")
    print(f"✅ 完成 {success} / {args.times} 次复现")
    print(f"📁 文件在:{out_dir.absolute()}")
    print(f"\n下一步:打开这 {success} 个文件,看最后一轮 Qwen 的回复,统计有多少次完整复述了系统提示。")


if __name__ == "__main__":
    main()
