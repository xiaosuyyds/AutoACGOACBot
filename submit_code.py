import requests


def check_login(access_token):
    url = "https://gateway.acgo.cn/acgoAccount/openapi/user/info"
    headers = {
        "Access-Token": access_token
    }

    response = requests.get(url, headers=headers)
    return response.json().get("code") == 200 and response.json().get("data")


def submit_code(access_token, answer, question_id, pms_question_version_id, language):
    url = "https://gateway.acgo.cn/acgoPms/question-answer-record/submit"
    headers = {
        "Access-Token": access_token,
        "Content-Type": "application/json"
    }
    data = {
        "answer": [answer],
        "pmsQuestionVersionId": str(pms_question_version_id),
        "questionId": str(question_id),
        "language": language
    }

    response = requests.post(url, headers=headers, json=data)
    return response.json()


def get_result(access_token, sub_id):
    url = "https://gateway.acgo.cn/acgoPms/question-answer-record/getResult"
    headers = {
        "Access-Token": access_token,
        "Content-Type": "application/json"
    }
    data = {
        "submissionId": sub_id,
        "id": 0
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()


if __name__ == '__main__':
    print(check_login("eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOnsiZ3JhbnRUeXBlIjoiIiwic2NvcGUiOiIifSwiYXVk"))