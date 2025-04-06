import re
import time
import generate_answer
import run_cpp
import get_problem
import submit_code
import auto_login
import constants
import os
import json

# 定义一些用于打印输出格式化的常量
PREFIX_INFO = "[INFO]"
PREFIX_STEP = "[STEP]"
PREFIX_AUTH = "[AUTH]"
PREFIX_ERROR = "[ERROR]"
PREFIX_WARN = "[WARN]"
PREFIX_SUCCESS = "[SUCCESS]"
PREFIX_DETAIL = "  [DETAIL]"
SEPARATOR = "-" * 40
EXPECTED_ACCEPT_STATUS = "AC"  # 定义表示“答案正确”状态的字符串

# 定义失败状态字符串
STATUS_FAIL_GET_PROBLEM = "获取题目信息失败"
STATUS_FAIL_GET_PMS_ID = "未能提取题目版本ID"
STATUS_FAIL_LOGIN = "登录或Token验证失败"
STATUS_FAIL_GENERATE = "LLM未能生成代码"
STATUS_FAIL_LOCAL_TEST = "本地测试未通过"
STATUS_FAIL_SUBMIT = "提交代码失败"
STATUS_FAIL_GET_RESULT = "未能获取判题结果"
STATUS_FAIL_PARSE_RESULT = "解析判题结果失败"
STATUS_FAIL_UNKNOWN = "未知错误"
STATUS_EXCEPTION = "发生异常"  # 用于主流程的异常捕获

# 访问令牌缓存文件的路径
access_token_cache_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "access_token.json")


def auto_get_access_token():
    """
    检查是否存在有效的访问令牌，如果需要，则尝试登录或刷新。
    返回访问令牌，如果失败则返回 None。
    """
    print(f"{PREFIX_AUTH} 检查登录状态...")
    access_token = None
    needs_login = True  # 默认需要登录

    # 检查缓存文件是否存在
    if os.path.exists(access_token_cache_path):
        try:
            # 读取缓存的token
            with open(access_token_cache_path, "r", encoding='utf-8') as f:
                data = json.load(f)
                access_token = data.get("access_token")
            # 检查token是否有效
            if access_token and submit_code.check_login(access_token):
                print(f"{PREFIX_AUTH} Token有效，继续。")
                needs_login = False  # Token有效，无需登录
            else:
                print(f"{PREFIX_AUTH} 本地Token无效或已过期。")
                access_token = None  # 明确将无效token设为None
        except (json.JSONDecodeError, IOError) as e:
            # 处理读取文件或解析JSON时的错误
            print(f"{PREFIX_WARN} 读取Token缓存文件失败: {e}")
            access_token = None  # 确保读取失败时token为None

    # 如果需要登录（缓存不存在、无效或读取失败）
    if needs_login:
        print(f"{PREFIX_AUTH} 尝试自动登录/刷新...")
        try:
            # 调用自动登录/刷新Cookie的函数
            access_token = auto_login.refresh_cookie()
            if access_token:
                # 登录成功，保存新的token
                with open(access_token_cache_path, "w", encoding='utf-8') as f:
                    json.dump({"access_token": access_token}, f)
                print(f"{PREFIX_SUCCESS} 登录成功，Token已保存。")
                # 立刻验证新获取的token
                if not submit_code.check_login(access_token):
                    print(f"{PREFIX_ERROR} 登录后Token验证失败！请检查登录逻辑或网络。")
                    return None  # 严重错误，返回None
            else:
                # 自动登录失败
                print(f"{PREFIX_ERROR} 自动登录/刷新失败，未能获取Token。")
                return None  # 严重错误，返回None
        except Exception as e:
            # 处理登录过程中的异常
            print(f"{PREFIX_ERROR} 登录过程中发生错误: {e}")
            return None

    # 返回有效的token
    return access_token


def auto_ac_problem(problem_id):
    """
    自动化处理流程：获取题目 -> 生成/修复代码 -> 本地编译测试 -> 提交 -> 检查结果。
    始终返回三个值：(判题结果数据, 代码字符串, 状态字符串)。
    成功时，判题结果数据是一个字典，状态字符串是判题状态(如 "AC", "WA")。
    失败时，判题结果数据是 None，状态字符串描述失败原因。
    """
    print(f"\n{'=' * 10} 开始处理题目 P{problem_id} {'=' * 10}")

    # --- 步骤 1: 获取题目信息 ---
    print(f"\n{PREFIX_STEP} 1. 获取题目信息...")
    problem = None
    problem_markdown = None
    input_output_samples = None
    pms_question_version_id = None
    try:
        # 获取题目基本信息对象
        problem = get_problem.get_problem_info(problem_id)
        if not problem:
            print(f"{PREFIX_ERROR} 获取题目基本信息失败！")
            return None, None, STATUS_FAIL_GET_PROBLEM
        # 获取格式化后的题目描述和样例
        problem_markdown, input_output_samples = get_problem.get_problem_md(problem_id, problem)
        if not problem_markdown:
            print(f"{PREFIX_ERROR} 转换题目信息到Markdown失败！")
            return None, None, STATUS_FAIL_GET_PROBLEM

        # 保存题目描述到本地文件
        md_filename = f"{problem_id}.md"
        with open(md_filename, "w", encoding='utf-8') as f:
            f.write(problem_markdown)
        print(f"{PREFIX_INFO} 题目描述已转换为Markdown并保存到: {md_filename}")

        # 提取题目版本ID (pms_question_version_id)
        pms_match = re.search(constants.PMS_QUESTION_VERSION_ID_REGEX, problem.prettify())
        if not pms_match:
            # 备选方案：尝试从Markdown文本中查找ID
            pms_match_md = re.search(r'pmsQuestionVersionId=(\d+)', problem_markdown)
            if pms_match_md:
                pms_question_version_id = pms_match_md.group(1)
                print(
                    f"{PREFIX_WARN} 未能在HTML结构中找到pms_question_version_id，但在Markdown中找到: {pms_question_version_id}")
            else:
                print(f"{PREFIX_ERROR} 未能从题目信息中提取 pms_question_version_id！")
                return None, None, STATUS_FAIL_GET_PMS_ID
        else:
            # 从HTML结构中成功提取ID
            pms_question_version_id = pms_match.group(1)
            print(f"{PREFIX_INFO} 题目 PMS Question Version ID: {pms_question_version_id}")

        print(f"{PREFIX_SUCCESS} 题目信息获取完成。")

    except Exception as e:
        # 处理获取题目信息过程中的任何异常
        print(f"{PREFIX_ERROR} 获取题目信息时出错: {e}")
        return None, None, f"{STATUS_FAIL_GET_PROBLEM} ({e})"  # 返回更具体的错误

    # --- 步骤 2: 生成和修复代码 ---
    print(f"\n{PREFIX_STEP} 2. 生成和修复代码...")
    answer = None
    messages = None
    final_code_ok = False  # 标记最终代码是否通过本地测试

    # 外层循环：控制整体重试（包括重新生成）次数
    for i in range(constants.MAX_RETRY_COUNT):
        print(f"\n{PREFIX_INFO} 第 {i + 1}/{constants.MAX_RETRY_COUNT} 次尝试 (包括生成/重新生成)...")

        # --- 代码生成/重新生成 ---
        try:
            if i == 0:
                # 首次尝试，调用生成答案接口
                print(f"{PREFIX_INFO} 请求LLM生成初始代码...")
                answer, messages = generate_answer.generate_answer(problem_markdown)
            else:
                # 非首次尝试（意味着之前的修复都失败了），重新生成代码
                print(f"{PREFIX_WARN} 代码本地测试失败，请求LLM更换思路并重新生成...")
                answer, messages = generate_answer.generate_answer(problem_markdown)  # 重新调用生成

            if not answer:
                # LLM未能生成代码
                print(f"{PREFIX_ERROR} LLM在第 {i + 1} 次尝试中未能生成代码。")
                # 不需要立即返回，外层循环会继续或结束
                if i == constants.MAX_RETRY_COUNT - 1:  # 如果是最后一次尝试则退出
                    print(f"{PREFIX_ERROR} 已达到最大生成重试次数，放弃。")
                    return None, None, STATUS_FAIL_GENERATE
                continue  # 进行下一次外层循环（如果还有）

            print(f"{PREFIX_INFO} LLM 生成/重新生成的代码:")
            print(SEPARATOR)
            print(answer)
            print(SEPARATOR)

        except Exception as e:
            # 处理调用LLM生成/重新生成时的错误
            print(f"{PREFIX_ERROR} 调用LLM生成代码时出错 (尝试 {i + 1}): {e}")
            if i == constants.MAX_RETRY_COUNT - 1:  # 如果是最后一次尝试则退出
                print(f"{PREFIX_ERROR} 已达到最大生成重试次数，放弃。")
                return None, answer, f"{STATUS_FAIL_GENERATE} ({e})"  # 返回当前可能存在的代码
            continue  # 继续下一次外层循环

        # --- 内层循环：控制单次生成后的修复次数 ---
        code_passes_local_tests = False  # 重置本地测试通过标记
        for j in range(constants.MAX_FIX_COUNT):
            print(f"\n  {PREFIX_INFO} 第 {i + 1} 次生成后的第 {j + 1}/{constants.MAX_FIX_COUNT} 次本地修复尝试...")

            # 保存当前代码到文件
            cpp_filename = f"{problem_id}.cpp"
            try:
                with open(cpp_filename, "w", encoding='utf-8') as f:
                    f.write(answer)
                print(f"  {PREFIX_INFO} 代码已保存到: {cpp_filename}")
            except IOError as e:
                print(f"  {PREFIX_ERROR} 保存代码文件失败: {e}")
                # 保存失败是严重问题，中断当前修复尝试
                break  # 跳出内层修复循环

            # --- 编译代码 ---
            print(f"  {PREFIX_STEP} 正在编译...")
            compile_ok, compile_result = run_cpp.compile_cpp(source_file=cpp_filename)

            if not compile_ok:
                # 编译失败
                print(f"  {PREFIX_ERROR} 编译失败!")
                # 如果还有修复机会，则反馈给LLM
                if j < constants.MAX_FIX_COUNT - 1:
                    print(f"  {PREFIX_INFO} 将编译错误反馈给 LLM 进行修复...")
                    message = f"你的代码编译失败！请修复错误并再次提供完整的代码，编译错误信息：\n{compile_result}"
                    print(f"{PREFIX_DETAIL} 编译错误信息:")
                    print(compile_result)
                    print(SEPARATOR)
                    try:
                        # 调用修复接口
                        answer, messages = generate_answer.fix_answer(message, messages)
                        if not answer:
                            print(f"  {PREFIX_ERROR} LLM 未能修复编译错误。")
                            # LLM修复失败，中断当前修复循环，可能需要重新生成
                            break
                        print(f"  {PREFIX_INFO} LLM 修复后的代码:")
                        print(SEPARATOR)
                        print(answer)
                        print(SEPARATOR)
                        # 继续下一次修复尝试
                        continue  # 跳过本次修复循环的剩余部分
                    except Exception as e:
                        print(f"  {PREFIX_ERROR} 调用LLM修复编译错误时出错: {e}")
                        break  # LLM调用出错，中断修复
                else:
                    print(f"  {PREFIX_WARN} 已达到最大修复次数，编译仍失败。")
                    break  # 编译失败且无修复机会，跳出内层循环

            # 编译成功
            print(f"  {PREFIX_SUCCESS} 编译成功。可执行文件: {compile_result}")

            # --- 运行样例测试 ---
            if not input_output_samples:
                # 没有样例，无法本地测试，假设通过
                print(f"  {PREFIX_WARN} 没有找到输入输出样例，跳过本地运行测试。")
                code_passes_local_tests = True
                break  # 编译成功且无样例，视为本地测试通过，跳出内层循环

            all_samples_passed = True  # 假设所有样例都通过
            failed_sample_message = None  # 存储失败样例的反馈信息
            for k, sample in enumerate(input_output_samples):
                print(f"  {PREFIX_STEP} 运行样例 {k + 1}/{len(input_output_samples)}...")
                try:
                    # 执行编译后的程序
                    run_ok, final_stdout, final_stderr, final_message = run_cpp.run_executable(
                        executable_path=compile_result,
                        input_data=sample["input"],
                        timeout_seconds=15
                    )

                    if not run_ok:
                        # 运行出错 (例如超时、运行时错误)
                        print(f"  {PREFIX_ERROR} 样例 {k + 1} 运行失败!")
                        all_samples_passed = False
                        failed_sample_message = (f"你的代码在运行测试样例时失败了！请修复错误并再次提供完整的代码。\n"
                                                 f"错误原因：{final_message}\n"
                                                 f"输入:\n{sample['input']}\n"
                                                 f"程序标准输出（可能不完整）：\n{final_stdout if final_stdout is not None else '(无)'}\n"
                                                 f"程序标准错误（可能不完整）：\n{final_stderr if final_stderr is not None else '(无)'}")
                        print(f"{PREFIX_DETAIL} 运行错误详情:")
                        print(f"    Input:\n{sample['input']}")
                        print(f"    Reason: {final_message}")
                        print(f"    Stdout: {final_stdout if final_stdout is not None else '(无)'}")
                        print(f"    Stderr: {final_stderr if final_stderr is not None else '(无)'}")
                        print(SEPARATOR)
                        break  # 一个样例失败，无需测试其他样例，跳出样例循环

                    else:
                        # 运行成功，比较输出
                        # 清理预期输出和实际输出中的空白字符以便比较
                        expected_output_clean = "\n".join(
                            line.strip() for line in sample["output"].splitlines()).strip()
                        actual_output_clean = "\n".join(
                            line.strip() for line in
                            (final_stdout or "").splitlines()).strip()  # 处理 final_stdout 可能为 None 的情况

                        if actual_output_clean == expected_output_clean:
                            # 输出匹配
                            print(f"  {PREFIX_SUCCESS} 样例 {k + 1} 通过。")
                            continue  # 测试下一个样例
                        else:
                            # 输出不匹配 (答案错误 - WA)
                            print(f"  {PREFIX_ERROR} 样例 {k + 1} 输出错误!")
                            all_samples_passed = False
                            failed_sample_message = (
                                f"你的代码在运行测试样例时输出了错误的结果！请修复错误并再次提供完整的代码。\n"
                                f"输入:\n{sample['input']}\n"
                                f"预期输出:\n{expected_output_clean}\n"
                                f"你的输出:\n{actual_output_clean}")
                            print(f"{PREFIX_DETAIL} 输出对比:")
                            print(f"    Input:\n{sample['input']}")
                            print(f"    Expected:\n{expected_output_clean}")
                            print(f"    Actual:\n{actual_output_clean}")
                            print(SEPARATOR)
                            break  # 一个样例失败，跳出样例循环

                except Exception as e:
                    # 运行样例时发生意外错误
                    print(f"  {PREFIX_ERROR} 运行样例 {k + 1} 时发生意外错误: {e}")
                    all_samples_passed = False
                    failed_sample_message = f"运行测试样例时发生意外错误: {e}. 输入:\n{sample['input']}"
                    break  # 发生意外错误，中断样例测试

            # --- 处理样例测试结果 ---
            if all_samples_passed:
                # 所有样例（或无样例）通过本地测试
                print(f"\n  {PREFIX_SUCCESS} 所有本地样例测试通过！")
                code_passes_local_tests = True
                break  # 本地测试成功，跳出内层修复循环
            else:
                # 存在失败的样例
                if failed_sample_message and j < constants.MAX_FIX_COUNT - 1:
                    # 如果还有修复机会，反馈给LLM
                    print(f"  {PREFIX_INFO} 将样例运行错误反馈给 LLM 进行修复...")
                    try:
                        answer, messages = generate_answer.fix_answer(failed_sample_message, messages)
                        if not answer:
                            print(f"  {PREFIX_ERROR} LLM 未能修复样例运行错误。")
                            break  # LLM修复失败，中断修复
                        print(f"  {PREFIX_INFO} LLM 修复后的代码:")
                        print(SEPARATOR)
                        print(answer)
                        print(SEPARATOR)
                        # LLM提供了修复后的代码，内层循环继续下一次尝试
                    except Exception as e:
                        print(f"  {PREFIX_ERROR} 调用LLM修复样例错误时出错: {e}")
                        break  # LLM调用出错，中断修复
                elif not failed_sample_message:
                    print(f"  {PREFIX_ERROR} 内部错误：样本测试失败但未生成修复消息。")
                    break  # 内部逻辑错误，中断修复
                else:
                    # 样例失败且已达到最大修复次数
                    print(f"  {PREFIX_WARN} 已达到最大修复次数，样例测试仍未通过。")
                    break  # 跳出内层循环

        # --- 内层修复循环结束 ---
        if code_passes_local_tests:
            # 当前生成的代码已通过所有本地测试
            print(f"\n{PREFIX_SUCCESS} 第 {i + 1} 次尝试生成的代码已通过本地编译和测试。")
            final_code_ok = True
            break  # 找到了可行的代码，跳出外层重试循环
        else:
            # 当前生成的代码未能通过本地测试（编译失败或样例失败，且修复次数用尽）
            print(f"\n{PREFIX_WARN} 第 {i + 1} 次尝试生成的代码未能通过所有本地修复/测试。")
            # 外层循环将继续下一次尝试（重新生成），除非已达上限

    # --- 外层重试循环结束 ---
    if not final_code_ok:
        # 所有重试（包括重新生成和修复）都失败了
        print(f"\n{PREFIX_ERROR} 经过 {constants.MAX_RETRY_COUNT} 次尝试后，未能生成可通过本地测试的代码。")
        print(f"{PREFIX_INFO} 请考虑检查LLM设置、提示或题目本身。")
        return None, answer, STATUS_FAIL_LOCAL_TEST  # 返回最后一次尝试的代码

    # --- 步骤 3: 提交代码 ---
    print(f"\n{PREFIX_STEP} 3. 提交代码...")
    # 再次获取/确认token，以防过期
    access_token = auto_get_access_token()
    if not access_token:
        print(f"{PREFIX_ERROR} 无法获取有效的 Access Token，无法提交。")
        # 虽然代码本地测试通过，但无法提交
        return None, answer, STATUS_FAIL_LOGIN  # 返回本地测试通过的代码

    submission_id = None
    try:
        print(f"{PREFIX_INFO} 提交语言: {constants.LANGUAGE}, pmsId: {pms_question_version_id}")
        # 调用提交代码接口
        submit_res = submit_code.submit_code(access_token, answer, problem_id, pms_question_version_id,
                                             constants.LANGUAGE)

        # 安全地获取提交ID
        submission_data = submit_res.get("data") if isinstance(submit_res, dict) else None
        submission_id = submission_data.get("ojSubmissionId") if isinstance(submission_data, dict) else None

        if submission_id:
            print(f"{PREFIX_SUCCESS} 代码提交成功。提交ID: {submission_id}")
        else:
            # 提交API调用成功但未返回有效ID
            print(f"{PREFIX_ERROR} 代码提交失败！未能获取提交ID。")
            print(f"{PREFIX_DETAIL} 提交API响应: {json.dumps(submit_res)}")
            return None, answer, STATUS_FAIL_SUBMIT  # 返回本地测试通过的代码

    except Exception as e:
        # 调用提交API时发生异常
        print(f"{PREFIX_ERROR} 提交代码时出错: {e}")
        return None, answer, f"{STATUS_FAIL_SUBMIT} ({e})"  # 返回本地测试通过的代码

    # --- 步骤 4: 检查判题结果 ---
    print(f"\n{PREFIX_STEP} 4. 检查判题结果...")
    print(f"{PREFIX_INFO} 轮询提交ID {submission_id} 的状态...")

    max_poll_attempts = 60  # 最大轮询次数
    poll_count = 0
    final_result_data = None  # 存储最终的判题结果
    overall_status = STATUS_FAIL_GET_RESULT  # 默认状态为获取失败

    # 轮询判题结果
    while poll_count < max_poll_attempts:
        poll_count += 1
        try:
            # 调用获取结果接口
            result_res = submit_code.get_result(access_token, submission_id)

            # 检查响应是否有效且包含数据
            if isinstance(result_res, dict) and result_res.get("data"):
                result_data = result_res["data"]
                # 判断判题是否完成（根据示例中的status或list字段）
                completion_status_value = 1  # 假设 status=1 表示完成
                is_complete = result_data.get("status") == completion_status_value or bool(result_data.get("list"))

                if is_complete:
                    # 判题完成
                    print(f"\n{PREFIX_SUCCESS} 获取到最终判题结果 (状态: {result_data.get('status', 'N/A')})。")
                    final_result_data = result_data
                    # 在这里解析最终状态
                    try:
                        print(f"\n{SEPARATOR}")
                        print("                判题详情")
                        print(f"{SEPARATOR}")
                        print(f"  Overall Status Code: {final_result_data.get('status', 'N/A')}")
                        print(
                            f"  Max Memory Used:     {final_result_data.get('memoryRate', 'N/A')} ({final_result_data.get('memory', 'N/A')} bytes)")
                        print(
                            f"  Max CPU Time Used:   {final_result_data.get('cpuTimeRate', 'N/A')} ({final_result_data.get('cpuTime', 'N/A')} ms)")
                        print(f"  Language Code:       {final_result_data.get('language', 'N/A')}")
                        print(f"  Judge Mode:          {final_result_data.get('judgeMode', 'N/A')}")
                        print(f"{SEPARATOR}")

                        test_case_list = final_result_data.get("list", [])
                        if test_case_list:
                            print("  测试点详情:")
                            all_ac = True
                            first_non_ac = None
                            for i, test_case in enumerate(test_case_list):
                                result = test_case.get('result', 'N/A')
                                print(f"  - {test_case.get('testCaseName', 'Case ' + str(i + 1)):<10}: "
                                      f"{test_case.get('resultDesc', 'N/A'):<12} "
                                      f"({result:<4}) "
                                      f"Time: {test_case.get('cpuTime', '?')}ms, "
                                      f"Memory: {test_case.get('memory', '?')}B")
                                if result != EXPECTED_ACCEPT_STATUS:
                                    all_ac = False
                                    if first_non_ac is None:
                                        first_non_ac = result
                            print(f"{SEPARATOR}")

                            if all_ac:
                                overall_status = EXPECTED_ACCEPT_STATUS
                            elif first_non_ac:
                                overall_status = first_non_ac
                            else:
                                overall_status = "Unknown (Check Details)"
                            print(f"  推断的总体结果: {overall_status}")
                        else:
                            print("  未找到详细的测试点列表，尝试根据顶层状态推断。")
                            top_status = final_result_data.get('status')
                            if top_status == 1:
                                overall_status = "Potentially Accepted (No Details)"
                            elif top_status is not None:
                                overall_status = f"Failed (Status Code: {top_status})"
                            else:
                                overall_status = "Unknown (No Details)"

                        print(f"{SEPARATOR}")
                        print(f"\n{PREFIX_INFO} 自动处理流程结束。最终状态: {overall_status}")

                    except Exception as e:
                        print(f"{PREFIX_ERROR} 解析或打印判题详情时出错: {e}")
                        print(f"{PREFIX_DETAIL} 原始数据: {final_result_data}")
                        overall_status = STATUS_FAIL_PARSE_RESULT  # 标记解析错误
                        final_result_data = None  # 解析失败时，结果数据也视为无效

                    break  # 无论解析是否成功，已获取到结果，退出轮询

                else:
                    # 仍在判题中
                    status_msg = "等待中"
                    if result_data.get("list"):
                        status_msg = f"正在判题 ({len(result_data['list'])}/{result_data.get('totalTestCaseCount', '?')})"
                    elif 'status' in result_data:
                        status_msg = f"状态码: {result_data['status']}"
                    print(f"{PREFIX_INFO} 状态: {status_msg}... (尝试 {poll_count}/{max_poll_attempts})")

            else:
                # API响应无效或无数据
                print(f"{PREFIX_WARN} 获取结果响应无效或无数据: {result_res} (尝试 {poll_count}/{max_poll_attempts})")

            # 等待一段时间再轮询
            time.sleep(0.5)

        except Exception as e:
            # 查询结果时发生异常
            print(f"{PREFIX_ERROR} 查询判题结果时出错: {e}")
            overall_status = f"{STATUS_FAIL_GET_RESULT} ({e})"  # 更新状态为包含异常信息
            time.sleep(1)  # 发生错误时等待稍长时间

    # --- 轮询结束 ---
    # 无论轮询是否成功找到结果，都返回三个值
    if final_result_data is None and poll_count >= max_poll_attempts:
        print(f"\n{PREFIX_ERROR} 在 {max_poll_attempts} 次尝试后未能获取最终判题结果。")
        # 保持 overall_status 为 STATUS_FAIL_GET_RESULT

    # 返回最终结果
    return final_result_data, answer, overall_status


if __name__ == '__main__':
    # 需要完成的题目id
    problem_id = 9  # 示例ID
    final_result_data = None
    final_code = None
    overall_status = "Process Started"  # 初始状态

    try:
        # 调用主处理函数，始终接收三个返回值
        final_result_data, final_code, overall_status = auto_ac_problem(problem_id)

        print("\n" + "=" * 20 + " 最终总结 " + "=" * 20)

        if final_result_data is not None:
            # 成功获取到判题结果（即使结果不是AC）
            print(f"{PREFIX_SUCCESS} 流程完成，获取到判题结果。")
            print(f"题目 P{problem_id} 的最终判题状态: {overall_status}")

            if overall_status == EXPECTED_ACCEPT_STATUS:
                print("🎉🎉🎉 恭喜！题目 Accepted! 🎉🎉🎉")
                if final_code:
                    final_cpp_filename = f"{problem_id}_AC.cpp"
                    try:
                        with open(final_cpp_filename, "w", encoding='utf-8') as f:
                            f.write(final_code)
                        print(f"{PREFIX_INFO} Accepted 代码已保存到: {final_cpp_filename}")
                    except IOError as e:
                        print(f"{PREFIX_WARN} 保存AC代码文件失败: {e}")
            else:
                # 题目未通过
                print(f"🤔 题目未完全通过 ({overall_status})，请检查上面的详细判题结果。")
                if final_code:
                    print(f"{PREFIX_INFO} 最后提交的代码保存在 {problem_id}.cpp")

        else:
            # 流程中途失败（final_result_data 为 None）
            print(f"{PREFIX_ERROR} 流程未能成功获取最终判题结果。")
            print(f"失败原因/状态: {overall_status}")
            if final_code:
                # 即使失败，也可能生成了代码
                print(f"{PREFIX_INFO} 最后生成的/尝试的代码保存在 {problem_id}.cpp")
            else:
                print(f"{PREFIX_INFO} 未能生成有效代码。")

        print(f"\n最终状态: {overall_status}")

    except Exception as main_exception:
        # 捕获主流程中的未处理异常
        print("\n" + "=" * 20 + " 发生严重错误 " + "=" * 20)
        print(f"{PREFIX_ERROR} 脚本执行过程中遇到未处理的异常: {main_exception}")
        import traceback

        print(traceback.format_exc())
        overall_status = STATUS_EXCEPTION  # 更新状态为异常
        print(f"\n最终状态: {overall_status}")

    # 可以取消注释以查看原始判题数据
    # if final_result_data:
    #    print("\n最终判题原始数据:")
    #    print(json.dumps(final_result_data, indent=2, ensure_ascii=False))
