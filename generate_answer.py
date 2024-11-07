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
    completion = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": constants.LLM_SYSTEM_PROMPT},
            {"role": "user", "content": problem_markdown + "\n" + constants.LLM_PROMPT},
        ],
        stream=True,
        temperature=0.2,
        max_tokens=4096,
    )
    answer = ""
    for chunk in completion:
        if chunk.choices[0].delta.content is not None:
            answer += chunk.choices[0].delta.content
            print(chunk.choices[0].delta.content, end="")
            code_block = answer.split("```cpp\n", 1)
            if len(code_block) > 1 and code_block[1] and "```" in code_block[1]:
                break
    # 提取代码块
    code_block = answer.split("```cpp\n", 1)[1]
    if code_block:
        code_block = code_block.split("\n```")[0]
    else:
        code_block = answer.split("```", 1)[1]
        code_block = code_block.split("```")[0]
    return code_block
