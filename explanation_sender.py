import requests


def send_explanation(access_token, question_id, answer):
    # 不建议使用
    url = "https://gateway.acgo.cn/acgoForum/post/add"
    headers = {
        "Access-Token": access_token,
        "Content-Type": "application/json"
    }

    data = {
        "questionId": question_id,
        "content": f"""```cpp
{answer}
```""",
        "type": 1,
        "digest": "",
        "title": "题解",
        "module": 1
    }

    response = requests.post(url, headers=headers, json=data)
    return response.json()
