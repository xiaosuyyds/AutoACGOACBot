import constants
import openai
import os

base_url = os.getenv("OPENAI_BASE_URL")
if not base_url:
    base_url = constants.OPENAI_BASE_URL

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    api_key = constants.OPENAI_API_KEY

openai.base_url = base_url
openai.api_key = api_key


def generate_answer(problem_markdown):
    messages = [
            {"role": "system", "content": constants.LLM_SYSTEM_PROMPT},
            {"role": "user", "content": problem_markdown + "\n" + constants.LLM_PROMPT},
        ]
    for i in range(3):
        try:
            completion = openai.chat.completions.create(
                model=constants.LLM_MODEL,
                messages=messages,
                stream=True,
                temperature=0.4,
                max_tokens=32768,
            )
            answer = ""
            for chunk in completion:
                if chunk.choices[0].delta.content is not None:
                    answer += chunk.choices[0].delta.content
                    # print(chunk.choices[0].delta.content, end="")
            code_block = answer.split("```cpp\n", 1)[1]
            if code_block:
                code_block = code_block.split("\n```")[0]
            else:
                code_block = answer.split("```", 1)[1]
                code_block = code_block.split("```")[0]
            break
        except Exception as e:
            print(f"生成回复遇到异常: {repr(e)}\n正在重试")
    else:
        raise Exception("生成回复遇到异常")
    messages.append({"role": "assistant", "content": answer})
    # print(answer)
    # 提取代码块
    return code_block, messages


def fix_answer(content, messages):
    messages.append({"role": "user", "content": content})
    for i in range(3):
        try:
            completion = openai.chat.completions.create(
                model=constants.LLM_MODEL,
                messages=messages,
                stream=True,
                temperature=0.4,
                max_tokens=32768,
            )
            answer = ""
            for chunk in completion:
                if chunk.choices[0].delta.content is not None:
                    answer += chunk.choices[0].delta.content
                    # print(chunk.choices[0].delta.content, end="")
            code_block = answer.split("```cpp\n", 1)[1]
            if code_block:
                code_block = code_block.split("\n```")[0]
            else:
                code_block = answer.split("```", 1)[1]
                code_block = code_block.split("```")[0]
            break
        except Exception as e:
            print(f"生成回复遇到异常: {repr(e)}\n正在重试")
    else:
        raise Exception("生成回复遇到异常")

    messages.append({"role": "assistant", "content": answer})

    return code_block, messages
