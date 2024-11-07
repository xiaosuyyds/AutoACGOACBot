import re
import time
import generate_answer
import explanation_sender
import get_problem
import submit_code
import auto_login
import constants
import os
import json

access_token_cache_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "access_token.json")


def auto_get_access_token():
    if not os.path.exists(access_token_cache_path):
        print("未检测到登录信息/登录信息过期，正在尝试登录")
        access_token = auto_login.refresh_cookie()
        with open(access_token_cache_path, "w") as f:
            json.dump({"access_token": access_token}, f)
            print("登录成功")
    with open(access_token_cache_path, "r") as f:
        access_token = json.load(f).get("access_token")

    if not submit_code.check_login(access_token):
        print("登录信息失效，正在尝试登录")
        access_token = auto_login.refresh_cookie()
        with open(access_token_cache_path, "w") as f:
            json.dump({"access_token": access_token}, f)
            print("登录成功")

    return access_token


def auto_ac_problem(problem_id):
    print(f"正在处理题目{problem_id}")
    print("正在获取题目")
    problem = get_problem.get_problem_info(problem_id)
    problem_markdown = get_problem.get_problem_md(problem_id, problem)
    # 获取pms_question_version_id
    pms_question_version_id = re.search(constants.PMS_QUESTION_VERSION_ID_REGEX, problem.prettify())
    pms_question_version_id = pms_question_version_id.group(1)
    print("题目的pms_question_version_id为:", pms_question_version_id)
    print("题目获取完成，正在生成答案")
    answer = generate_answer.generate_answer(problem_markdown)
    print(f"LLM生成的答案为:\n{answer}")
    print("答案生成完毕，正在提交代码")
    access_token = auto_get_access_token()
    submit_res = submit_code.submit_code(access_token, answer, problem_id, pms_question_version_id, constants.LANGUAGE)
    print("代码提交完成:", submit_res)
    if submit_res["data"]:
        while True:
            resul_res = submit_code.get_result(access_token, submit_res["data"]["ojSubmissionId"])
            if resul_res and resul_res["data"]:
                print("结果:", resul_res)
                for i in resul_res["data"]["list"]:
                    print(f"{i["testCaseName"]}: {i["result"]}, {i["resultDesc"]}")
                return resul_res["data"], answer
            print("正在等待结果", resul_res)
            time.sleep(0.5)
            continue


if __name__ == '__main__':
    # 需要完成的题目id
    problem_id = 1
    result, answer = auto_ac_problem(problem_id)
    print(result)
    ac_flag = True
    for i in result["list"]:
        if i["result"] != "AC":
            ac_flag = False

    if ac_flag:
        print("测试点全部通过正在提交题解")
        result = explanation_sender.send_explanation(auto_get_access_token(), problem_id, answer)
        print(result)
        print("题解提交完毕")
    else:
        print("测试点未全部通过，跳过提交题解")
