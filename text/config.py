"""
config.py · API 配置

使用方式:
1. 填入你的 API key
2. 通义千问注册地址: https://bailian.console.aliyun.com/
   免费额度充足,注册即可用
"""
import os

# ===== 通义千问 (阿里云百炼) =====
# 注册地址: https://bailian.console.aliyun.com/
# 控制台 → API Key 管理 → 创建 API Key
QWEN_API_KEY = os.getenv("QWEN_API_KEY", "sk-70dbbd8ffb074595bcbbd2f65ce7aa31")
QWEN_MODEL = "qwen-plus"  # 可选: qwen-turbo(更快更省) / qwen-plus / qwen-max

# ===== DeepSeek =====
# 注册地址: https://platform.deepseek.com
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "sk-a5eac9da0c5f473d9827789ab65ff253")
DEEPSEEK_MODEL = "deepseek-chat"  # 也可以换成 deepseek-reasoner

# ===== 通用参数 =====
TEMPERATURE = 0.7   # 中等温度,模拟真实用户场景
MAX_TOKENS = 1024   # 客服回复一般不超过这个长度
TIMEOUT = 60        # 单次请求超时(秒)

# 输出目录
OUTPUT_DIR = "outputs"
