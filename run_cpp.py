import subprocess
import os
import sys
import constants


def compile_cpp(source_file, compiler_path=constants.COMPILER_PATH, executable_name=None, compile_flags=None):
    """
    编译 C++ 源文件。

    Args:
        source_file (str): C++ 源文件路径 (.cpp)。
        compiler_path (str): C++ 编译器路径 (例如 "g++", "clang++")。
        executable_name (str, optional): 编译后的可执行文件名。
                            默认为不带扩展名的源文件名。
        compile_flags (list, optional): 传递给编译器的附加标志列表 (例如：["-std=c++11", "-Wall"])。

    Returns:
        tuple: (is_ok, result)
               is_ok (bool): 如果编译成功则为 True，否则为 False。
               result (str): 如果 is_ok 为 True，则为可执行文件的路径；
                             如果 is_ok 为 False，则为包含编译器输出的错误信息。
    """
    print(f"--- 开始编译: {source_file} ---")
    if not os.path.exists(source_file):
        error_msg = f"错误：源文件 '{source_file}' 不存在。"
        print(error_msg)
        return False, error_msg

    base_name = os.path.splitext(source_file)[0]
    # 生成一个临时或指定的可执行文件名 (最好放在当前目录或临时目录)
    exec_name = executable_name or base_name
    # 为 Windows 添加 .exe 后缀
    if sys.platform == "win32" and not exec_name.lower().endswith(".exe"):
        exec_name += ".exe"
    # 使用绝对路径或相对路径，这里用相对当前目录的
    executable_path = os.path.abspath(exec_name)  # 获取绝对路径以便后续使用

    compile_command = [compiler_path, source_file, "-o", executable_path]
    if compile_flags:
        compile_command.extend(compile_flags)

    print(f"执行编译命令：{' '.join(compile_command)}")
    try:
        compile_proc = subprocess.run(
            compile_command,
            capture_output=True,
            text=True,
            check=False  # 我们手动检查返回码
        )

        compile_stdout = compile_proc.stdout
        compile_stderr = compile_proc.stderr

        if compile_stdout:
            print(f"编译器标准输出:\n{compile_stdout.strip()}")
        if compile_stderr:
            print(f"编译器标准错误:\n{compile_stderr.strip()}")  # 警告信息也会出现在 stderr

        if compile_proc.returncode != 0:
            error_msg = (f"编译失败！退出码：{compile_proc.returncode}\n"
                         f"编译器输出:\n{compile_stdout}\n"
                         f"编译器错误:\n{compile_stderr}")
            print(error_msg)
            # 尝试清理失败时可能产生的空或部分文件
            if os.path.exists(executable_path):
                try:
                    os.remove(executable_path)
                    print(f"已清理可能存在的失败产物：{executable_path}")
                except OSError as e:
                    print(f"警告：无法清理失败产物 '{executable_path}': {e}")
            return False, error_msg
        else:
            print(f"编译成功！可执行文件位于：{executable_path}")
            return True, executable_path

    except Exception as e:
        error_msg = f"编译期间发生意外错误：{e}"
        print(error_msg)
        return False, error_msg


def run_executable(executable_path, input_data, timeout_seconds=5):
    """
    运行一个可执行文件，提供输入并捕获输出。

    Args:
        executable_path (str): 要运行的可执行文件的路径。
        input_data (str): 要传递给程序标准输入的字符串。
        timeout_seconds (int): 运行的超时时间（秒）。

    Returns:
        tuple: (is_ok, run_stdout, run_stderr, message)
               is_ok (bool): 如果运行成功（退出码为0且未超时）则为 True。
               run_stdout (str or None): 程序的标准输出。
               run_stderr (str or None): 程序的标准错误。
               message (str or None): 如果运行失败或超时，则为描述信息；否则为 None。
    """
    # print(f"\n--- 开始运行: {executable_path} ---")
    if not os.path.exists(executable_path):
        error_msg = f"错误：可执行文件 '{executable_path}' 不存在。"
        # print(error_msg)
        return False, None, None, error_msg

    # 在类 Unix 系统上，通常需要 './' 来运行当前目录的文件
    # 但如果 executable_path 是绝对路径，则不需要
    # subprocess 库通常能正确处理路径
    run_command = [executable_path]
    # 注意：在 Windows 上，如果路径包含空格，可能需要特殊处理，
    # 但 subprocess 通常能处理好列表形式的命令。

    # print(f"执行命令：{' '.join(run_command)}")
    # print(f"提供输入：\n{input_data.strip()}")

    run_stdout = None
    run_stderr = None
    message = None
    is_ok = False

    try:
        run_proc = subprocess.run(
            run_command,
            input=input_data,
            capture_output=True,
            text=True,
            timeout=timeout_seconds
        )

        run_stdout = run_proc.stdout
        run_stderr = run_proc.stderr

        # print(f"\n执行标准输出:\n{run_stdout.strip()}")
        # if run_stderr:  # 只在有内容时打印 stderr
        #     print(f"\n执行标准错误:\n{run_stderr.strip()}")

        if run_proc.returncode == 0:
            # print(f"程序成功执行，退出码：0")
            is_ok = True
            message = "执行成功"
        else:
            message = f"程序执行完成，但退出码非零：{run_proc.returncode}"
            # print(message)
            is_ok = False  # 退出码非零通常表示有问题

    except subprocess.TimeoutExpired as e:
        # 即使超时，也尝试获取已有的输出
        run_stdout = e.stdout if e.stdout else ""
        run_stderr = e.stderr if e.stderr else ""
        message = f"程序执行超时（超过 {timeout_seconds} 秒）！"
        # print(message)
        # if run_stdout:
        #     print(f"超时前的标准输出:\n{run_stdout.strip()}")
        # if run_stderr:
        #     print(f"超时前的标准错误:\n{run_stderr.strip()}")
        is_ok = False
    except FileNotFoundError:
        # 这个理论上在函数开头检查过了，但再加一层保险
        message = f"错误：无法找到或执行命令 '{executable_path}'。"
        # print(message)
        is_ok = False
    except Exception as e:
        message = f"执行期间发生意外错误：{e}"
        # print(message)
        is_ok = False

    # 调整返回值顺序以匹配文档说明
    if is_ok:
        return True, run_stdout, run_stderr, None  # 成功时 message 为 None
    else:
        return False, run_stdout, run_stderr, message  # 失败时返回具体原因
