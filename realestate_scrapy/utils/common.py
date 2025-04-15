import re


def extract_external_id(url: str) -> str:
    """
    从 URL 中提取房源的唯一标识ID，例如：
    https://www.homely.com.au/homes/105-conrad-street-st-albans-vic-3021/11105399
    返回结果: '11105399'
    """
    pattern = re.compile(r'/(\d+)/?$')
    match = pattern.search(url)
    if match:
        return match.group(1)
    return None

# 示例：如何使用 extract_external_id 函数
if __name__ == "__main__":
    test_url = "https://www.homely.com.au/homes/105-conrad-street-st-albans-vic-3021/11105399"
    house_id = extract_external_id(test_url)
    print(f"提取的房源ID：{house_id}")

