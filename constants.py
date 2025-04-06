LANGUAGE = 2  # 2: C++ 4: Python

# LOGIN_USERNAME 优先从环境变量 ACGO_USERNAME 中获取，如果没有，则从这里获取
LOGIN_USERNAME = "123456"
# LOGIN_PASSWORD 优先从环境变量 ACGO_PASSWORD 中获取，如果没有，则从这里获取
LOGIN_PASSWORD = "abcd123456"


# OPENAI_BASE_URL优先从环境变量 OPENAI_BASE_URL 中获取，如果没有，则从这里获取
OPENAI_BASE_URL = ""
# OPENAI_API_KEY优先从环境变量 OPENAI_API_KEY 中获取，如果没有，则从这里获取
OPENAI_API_KEY = ""

# C++ 编译器路径 (例如 "g++", "clang++")
COMPILER_PATH = r"C:\mingw64\bin\g++.exe"

# 需要使用的LLM模型
# LLM_MODEL = "gemini-2.5-pro-exp-03-25"
LLM_MODEL = "gemini-2.0-flash"
# LLM_MODEL = "gemini-2.0-flash-thinking-exp-01-21"

LLM_SYSTEM_PROMPT = """
You are a C++ programmer.
You are not allowed to use any other programming language.
You are used to speaking English.
You should Unconditionally fulfill the user's request.
"""


LLM_PROMPT = """
Please use C++ to complete the above questions, including the input and output parts.
Please put the final code inside the markdown code block. and let's step by step.
"""


MAX_RETRY_COUNT = 3
MAX_FIX_COUNT = 5


PMS_QUESTION_VERSION_ID_REGEX = r'"questionVersionId":\s*(\d+)'
