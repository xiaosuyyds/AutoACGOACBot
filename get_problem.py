"""
Copyright 2024 Xiaosu

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import time

import requests
from bs4 import BeautifulSoup, ResultSet

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
}


def filter_class_start(start_with: str, find_list: ResultSet):
    return [_ for _ in find_list if _.get("class") and _.get("class")[0].startswith(start_with)]


def format_markdown(text: str) -> str:
    # 去除每行首尾的多余空白字符
    lines = [line.strip() for line in text.splitlines()]

    # 删除空行，保留段落之间一个空行
    formatted_lines = []
    prev_blank = False
    for line in lines:
        if line == "":
            if not prev_blank:
                formatted_lines.append(line)
            prev_blank = True
        else:
            formatted_lines.append(line)
            prev_blank = False

    # 将处理过的行重新组合成字符串
    formatted_text = "\n".join(formatted_lines)

    # 确保最后一个字符不是空行
    formatted_text = formatted_text.strip()

    return formatted_text


def problem_item_2_list(problem_item: BeautifulSoup):
    item_text = []
    for elem in problem_item.children:
        # 如果是 NavigableString，直接提取文本
        if elem.name is None:
            item_text.append({"content": elem, "type": "text"})
            # 如果是包含 katex 的 span 标签，提取 MathML 或 TeX 表达式
        if elem.name == 's':
            # 删除线
            item_text.append({"content": f"~~{elem.get_text()}~~", "type": "text"})
        elif elem.name == 'u':
            # 下划线
            item_text.append({"content": f"<u>{elem.get_text()}</u>", "type": "text"})
        elif elem.name == 'span' and 'katex' in elem.get('class', []):
            tex_expr = elem.find('annotation', {'encoding': 'application/x-tex'})
            if tex_expr:
                item_text.append({"content": tex_expr.get_text(), "type": "tex"})
        elif elem.name == 'img':
            item_text.append({"content": elem.get("src"), "type": "image"})
        elif elem.name == 'code':
            item_text.append({"content": elem.text, "type": "code"})
        elif elem.name == 'br':
            item_text.append({"content": "\n\n", "type": "text"})
    return item_text


def problem_info_2_md(problem_info: BeautifulSoup, problem_statistics: dict):
    title = filter_class_start("info_title", problem_info.find_all("h1"))[0].text

    # sumary = filter_class_start("info_sumary", problem_info.find_all("div"))[0]
    # problem_source = filter_class_start("info_source", sumary.find_all("div"))[0].text
    # problem_difficulty = filter_class_start("Difficulty_tag", sumary.find_all("p"))[0].text

    problem_pass_rates = filter_class_start("info_passRateLine", problem_info.find_all("div"))[0]
    problem_pass_rates = filter_class_start("info_passRate", problem_pass_rates.find_all("p"))
    problem_pass_rates = [_.text for _ in problem_pass_rates]
    for i in range(len(problem_pass_rates)):
        rate = problem_pass_rates[i]
        if rate.startswith("通过率"):
            rate = rate.replace(":", "：").split("：")[0] + ":" + problem_statistics["data"]["passRate"]
            problem_pass_rates[i] = rate

    problem_items = []

    for problem_item in filter_class_start("info_item", problem_info.find_all("div")):
        item_title = problem_item.find("h4").text
        item_content = filter_class_start("displayer_mdDisplayerWrap", problem_item.find_all("div"))
        item_type = ""
        if item_content:
            item_type = "text"
            item_text = []
            for p in item_content[0]:
                flag = False
                if p.name == 'p':
                    p = problem_item_2_list(p)
                    item_text += p
                    if p:
                        flag = True
                elif p.name == 'hr' or p.name == 'hr/':
                    item_text.append({"content": "", "type": "hr"})
                    flag = True
                elif p.name == 'ul':
                    for li in p.find_all("li"):
                        for _ in li.find_all("p"):
                            _ = problem_item_2_list(_)
                            item_text += [{"content": "- ", "type": "text"}] + _ + [{"content": "\n", "type": "text"}]
                elif p.name == 'ol':
                    i = 0
                    for li in p.find_all("li"):
                        i += 1
                        li = problem_item_2_list(li)
                        item_text += [{"content": f"{i}. ", "type": "text"}] + li + [{"content": "\n", "type": "text"}]
                elif p.name == 'table':
                    thead = p.find("thead").find("tr")
                    thead = [problem_item_2_list(_) for _ in thead.find_all("th")]
                    tbody = p.find("tbody")
                    tbody = [problem_item_2_list(__) for _ in tbody.find_all("tr") for __ in tbody.find_all("td")]
                    item_text += [{"content": (thead, tbody), "type": "table"}]
                elif p.name == 'blockquote':
                    item_text_ = problem_item_2_list(p.find("p"))
                    for _ in item_text_:
                        flag_ = True
                        if _["type"] == "text" or _["type"] == "tex":
                            if _["content"].strip() != "\n\n" and _["content"].strip() != "":
                                item_text += [{"content": "> ", "type": "text"}]
                            if _["content"] == "\n\n":
                                item_text += [{"content": "\n>", "type": "text"}]
                                flag_ = False
                        if flag_:
                            item_text += [_]
                    flag = True
                if flag:
                    item_text += [{"content": "\n\n", "type": "text"}]
            item_content = item_text[:-1]
        else:
            item_type = "input_output"
            # 可能是输入输出样例
            item_content = []
            item_example_list = filter_class_start("info_exampleList", problem_item.find_all("ul"))[0]
            item_example_list = item_example_list.find_all("li")
            for item_examples in item_example_list:
                item_examples = filter_class_start("Example_example_", item_examples.find_all("div"))
                item_examples_content = []
                for item_example in item_examples:
                    item_example_title = filter_class_start("Example_exampleTitle", item_example.find_all("div"))
                    item_example_title = item_example_title[0].find("p").text
                    item_example_content = filter_class_start("Example_exampleContent",
                                                              item_example.find_all("pre"))
                    item_example_content = [__ for __ in [_.text for _ in item_example_content]]
                    item_example_content = "".join([__ for _ in item_example_content for __ in _])
                    item_example_input = {
                        "title": item_example_title,
                        "content": item_example_content
                    }
                    item_examples_content.append(item_example_input)
                item_content.append(item_examples_content)

        problem_items.append({
            "title": item_title,
            "content": item_content,
            "type": item_type
        })

    # print(title, problem_source, problem_difficulty, problem_pass_rates)
    # print("\n".join([str(i) for i in problem_items]))

    mark_down = ""
    mark_down += f"# {title}\n"
    # mark_down += f"#### 题目来源：{problem_source}\n"
    # mark_down += f"#### 题目难度：{problem_difficulty}\n"
    # mark_down += (f"#### 通过率：{problem_pass_rates[0]}"
    #               f"({problem_statistics['data']['passTotal']}/{problem_statistics['data']['total']})\n")
    mark_down += f"#### 限制：{" | ".join(problem_pass_rates[1:])}\n"
    for item in problem_items:
        mark_down += f"### {item['title']}\n"
        if item['type'] == "text":
            for content in item['content']:
                if content['type'] == "text":
                    mark_down += f"{content['content']}"
                elif content['type'] == "tex":
                    mark_down += f"$ {content['content']} $"
                elif content['type'] == "image":
                    mark_down += f"![]({content['content']})"
                elif content['type'] == "hr":
                    mark_down += "---"
                elif content['type'] == "code":
                    if "\n" not in content['content']:
                        mark_down += f"`{content['content']}`"
                    else:
                        mark_down += f"```\n{content['content']}\n```"
                elif content['type'] == "table":
                    # 未完成，先这么写着
                    mark_down += str(content['content'])
                    # mark_down += "\n" + table2md(content['content'])
        elif item['type'] == "input_output":
            for item_examples in item['content']:
                for item_example in item_examples:
                    mark_down += f"#### {item_example['title']}\n\n"
                    mark_down += f"```text\n{item_example['content']}\n```\n"
        mark_down += "\n"
    return format_markdown(mark_down)


def get_problem_statistics(problem_id):
    url = "https://gateway.acgo.cn/acgoPms/question-answer-record/statistics"

    data = {
        "questionId": problem_id,
    }

    res = requests.post(url, json=data, headers=headers)

    return res.json()


def get_problem_info(problem_id):
    url = "https://www.acgo.cn/problemset/info/"

    url_problem = url + str(problem_id)
    res = requests.get(url_problem, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")
    return soup


def get_problem_md(problem_id, problem_soup):
    info = filter_class_start("info_detailWra", problem_soup.find_all("div"))[0]
    return problem_info_2_md(info, get_problem_statistics(problem_id))


if __name__ == '__main__':
    problem_id = 33359
    # problem_id = 3
    t = time.time()
    mark_down = get_problem_info(problem_id)
    with open(f"{problem_id}.md", "w", encoding="utf-8") as f:
        f.write(mark_down)
    print("done!", f"time: {time.time() - t:.2f}s")