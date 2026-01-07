import re

def num_handler(text: str) -> float:
    mark = 1
    if text == None:
        return 0
    # 先检测+/-是否再匹配字段中
    if '-' in text:
        mark = -1
    # 按空格切开取最后一个
    text_split = text.split(' ')
    amt = text_split[-1]
    pattern = '\\D+'
    amt = re.sub(pattern, '', amt)
    if amt=='':
        return 0
    else:
        return mark * float(amt)

def trim(s):
    # 获取字符串的长度
    length = len(s)
    start = 0

    # 查找前导空白字符
    while start < length and s[start] <= ' ':
        start += 1

    # 查找尾部空白字符
    end = length
    while end > start and s[end - 1] <= ' ':
        end -= 1

    # 如果没有空白字符，返回原字符串，否则返回修剪后的字符串
    return s[start:end] if start > 0 or end < length else s