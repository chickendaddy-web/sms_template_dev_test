import regex as re
# import re
# from stirng_utils import trim

# 定义与 Java 中相同的正则表达式
pattern = re.compile(r'[\s.:>](http|https)?(://)?[a-zA-Z0-9\-]+\.[a-zA-Z0-9.\-]+/[a-zA-Z0-9/]*')
import string


def remove_url(content: str) -> str | None:
    if content is None:
        return None
    return pattern.sub('', content)


def content_main(content, phone):
    content = content_raw(content)
    content = remove_punctuation(content)
    content = remove_url(content)
    type_dict = classify_sms(content, str(phone))
    amt_dict = extract_amount_with_context(content)
    return type_dict, amt_dict


def content_raw(input_str):
    # Define regex patterns
    # number_regex = r"(\d+\,\d+)(,\d+)*(\.\d+)?|\d+\.\d+|\d+"  # Match all numbers (including decimals and comma-separated amounts)
    # replace_number = '∅'  # For replacing numbers

    date_regex = r"(\d+[-/]\d+)([-/]\d+)?"  # Match date formats like 2020-01-01 or 2020/01/01 or 2020-01 or 2020/01
    time_regex = r"(\d+:\d+)(:\d+)?"  # Match time formats like 12:00 or 12:00:00
    replace_date = '∆'  # For replacing dates
    replace_time = '∇'  # For replacing times

    # Perform replacements in sequence
    result1 = re.sub(date_regex, replace_date, input_str)  # Replace dates
    result2 = re.sub(time_regex, replace_time, result1)  # Replace times
    # result3 = re.sub(number_regex, replace_number, result2)  # Replace numbers
    return result2


def remove_punctuation(text):
    """
    去除所有标点符号并替换为空格（保留字母、数字、越南语字母和特殊符号∅∆∇）

    参数:
        text (str): 输入文本

    返回:
        str: 处理后的文本
    """
    if not isinstance(text, str):
        return ""

    # 定义所有需要保留的越南语字母（小写和大写）
    vietnamese_chars = (
        "áàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵ"
        "ÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴ"
    )

    # 创建安全字符集（包括英文字母、数字、越南语字母、特殊符号和空格）
    safe_chars = set(
        string.ascii_letters +
        string.digits +
        "∅∆∇+- " +
        vietnamese_chars
    )

    # 处理文本：保留安全字符，其他替换为空格
    cleaned = ''.join(char if char in safe_chars else ' ' for char in text)

    # 合并连续空格
    return re.sub(r'\s+', ' ', cleaned).strip()


def extract_amounts(ori_content, template, amount_positions):
    """
    根据模板和金额位置提取金额

    参数:
        ori_content (str): 原始内容（处理后的）
        template (str): 模板（处理后的）
        amount_positions (dict): 金额位置映射（例：{"金额1": 1, "金额2": 2}）

    返回:
        dict: 提取的金额结果（例：{"金额1": "100", "金额2": "200"}）
    """
    # 如果金额位置字典为空，直接返回空结果
    if amount_positions == {}:
        return {}

    # 处理空输入
    if not ori_content or not template:
        return {}

    # 转换模板为正则表达式
    pattern = template.pattern  # 假设 template 有 pattern 属性，包含正则表达式字符串

    # 执行正则匹配
    match = re.search(pattern, ori_content)
    if not match:
        return {}

    # 提取所有捕获组
    groups = match.groups()

    # 根据位置提取金额
    results = {}
    for amount_field, pos in amount_positions.items():
        if isinstance(pos, int) and 1 <= pos <= len(groups):
            # 移除金额字符串中的空格（合并数字）
            amount_str = groups[pos - 1].replace(" ", "")
            results[amount_field] = amount_str

    return results


def get_replacement_list(input_str):
    # Regular expressions for matching patterns
    date_regex = r"(\d+[-/]\d+)([-/]\d+)?"
    time_regex = r"(\d+:\d+)(:\d+)?"
    number_regex = r"(\d+\,\d+)(,\d+)*(\.\d+)?|\d+\.\d+|\d+"

    occupied = []  # Tracks occupied intervals (start, end)
    replacements = []  # List of replaced strings in order of replacement

    # Replace dates: find all non-overlapping matches
    for match in re.finditer(date_regex, input_str):
        start, end = match.span()
        # For the same regex, matches won't overlap, so no need to check occupied here
        replacements.append(match.group())
        occupied.append((start, end))

    # Replace times: find all non-overlapping matches not in occupied regions
    for match in re.finditer(time_regex, input_str):
        start, end = match.span()
        if not any(start < e and end > s for (s, e) in occupied):
            replacements.append(match.group())
            occupied.append((start, end))

    # Replace numbers: find all non-overlapping matches not in occupied regions
    for match in re.finditer(number_regex, input_str):
        start, end = match.span()
        if not any(start < e and end > s for (s, e) in occupied):
            replacements.append(match.group())
            occupied.append((start, end))

    return replacements


def content_mark_preprocess(content: str) -> tuple | None:
    if content is None:
        return None
    # 去除文本中的 URL
    content = remove_url(content)
    content = clean_text(content)
    lst = get_replacement_list(content)
    return lst


def clean_text(input_str):
    # Pattern to keep letters (including accented), numbers, and certain punctuation
    pattern = r"[^:/,\-\.$$\sA-Za-z0-9\u00C0-\u00FF\u0100-\u017F\u1E00-\u1EFF\u4E00-\u9FFF]"

    # Replace unwanted characters with space
    cleaned = re.sub(pattern, " ", input_str)

    # Collapse multiple spaces and trim
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return cleaned


def replace_variable(input_str):
    # Define regex patterns
    number_regex = r"(\d+\,\d+)(,\d+)*(\.\d+)?|\d+\.\d+|\d+"  # Match all numbers (including decimals and comma-separated amounts)
    replace_number = '∅'  # For replacing numbers

    date_regex = r"(\d+[-/]\d+)([-/]\d+)?"  # Match date formats like 2020-01-01 or 2020/01/01 or 2020-01 or 2020/01
    time_regex = r"(\d+:\d+)(:\d+)?"  # Match time formats like 12:00 or 12:00:00
    replace_date = '∆'  # For replacing dates
    replace_time = '∇'  # For replacing times

    # Perform replacements in sequence
    result1 = re.sub(date_regex, replace_date, input_str)  # Replace dates
    result2 = re.sub(time_regex, replace_time, result1)  # Replace times
    result3 = re.sub(number_regex, replace_number, result2)  # Replace numbers
    return result3


####################################分类函数#####################################
import re
from typing import Dict, List, Tuple
from collections import Counter

# 短信发送方映射
# 银行类发送方关键词（小写去重）
BANK_SENDER_KEYWORDS = [
    'mbbank', 'vietinbank', 'techcombank', 'agribank', 'sacombank', 'eximbank', 'acb',
    'vib', 'ocb', 'hdbank', 'bidv', 'shb', 'vpbank', 'msb', 'tpbank', 'scb', 'seabank',
    'pvcombank', 'kienvietbank', 'lienvietpostbank', 'bacabank', 'abbank', 'dongabank',
    'gpbank', 'kienlongbank', 'namabank', 'ncb', 'oceanbank', 'pgbank', 'saigonbank',
    'vietabank', 'vietcapitalbank', 'publicbank', 'shinhanbank', 'cimb', 'hsbc',
    'standardchartered', 'anz', 'uob', 'wooribank', 'indovinabank', 'vrb', 'tpb',
    'vietcombank', 'shinhan', 'woori', 'cidirect', 'petrolimex'
]

# 贷款机构类发送方关键词（小写去重）
LOAN_SENDER_KEYWORDS = [
    'mcredit', 'tima', 'homecredit', 'fecredit', 'fe_credit', 'vtpay', 'vtmoney', 'tien24', 'tiền24',
    'safe', 'cayvang', 'prudential', 'akulaku', 'easycredit', 'miraeasset', 'hd-saison',
    'shinhan', 'lotte', 'vnfinance', 'vnpay', 'mpos', 'myvay', 'prime credit', 'cake',
    'swift funds', 'vaypay', 'soloan', 'fin vui', 'viet dong', 'live cash', 'cash365',
    'chia khoa vang', 'fastdong', 'mdong', 'sdong', 'tieno', '79dong', 'moneyveo',
    'vayantoan', 'vaykipthoi', 'tientay24', 'mekongmobile', 'mar vay', 'okcredit',
    'timvay', 'dh loan', 'catcredi', 'yocredi', 'think credit', 'kredivo', 'sky credit',
    'takomo', 'kdongcredit', 'tnex finance', 'tnex', 'fe credit', 'hd saison',
    'mirae asset', 'vay tieu dung', 'tima.vn', 'tima credit', 'cashwagon', 'oncredit',
    'easy finance', 'cash flow', 'tala', 'quick cash', 'fast money', 'smart loan',
    'capital craft', 'cash crest', 'credit ease', 'flexi credit', 'lend link',
    'vay no', 'viet dong e', 'viet dong pro', 'vi tot', 'app vay nở', 'ví bắc nam', 'ví tiện lợi'
]

# 运营商类发送方关键词（小写去重）
OPERATOR_SENDER_KEYWORDS = [
    'viettel', 'vina', 'mobi', 'mobifone', 'vinaphone', 'vietnamobile', 'gmobile',
    'vnpt', 'redsun', 'vietnammobile', 'vtel', 'vnm', 'gh', 'vms', 'viettel_dv',
    'viettel_km', 'viettel_pt', 'viettel_qc', 'mobicloud', 'mobiedu', 'm_service',
    'viettel_post', 'viettel_money', 'myvietteldv', 'critical', 'major', 'clear', 'vt'
]

# 购物类发送方关键词（小写去重）
SHOPPING_SENDER_KEYWORDS = [
    'canifa', 'vascara', 'cayvang', 'fpt', 'aristino', 'cps', 'vietnam post', 'postpay', 'viettel pay',
    'elise', '5s fashion', 'sixdo', 'lotte', 'big c', 'coop', 'guardian', 'pharmacity',
    'circle k', 'ministop', 'gs25', 'bibo mart', 'winmart', 'aeon', 'lotte mart',
    'global mall', 'tiki', 'shopee', 'leika', 'crocs', 'lazada', 'sendo', 'momo',
    'zalopay', 'viettelpay', 'onepay', 'vnpay', 'airpay', 'mypay', 'payoo',
    'hasaki', 'mediamart', 'dienmayxanh', 'nguyen kim', 'thien long', 'vinamilk',
    'uniqlo', 'h&m', 'zara', 'adidas', 'nike', 'puma', 'gucci', 'lv', 'prada'
]

# 短号码映射（特殊处理）
SHORT_CODE_MAPPING = {
    # 原有映射保留
    '999': '运营商',  # 运营商营销服务（Mobifone核心服务）
    '9199': '运营商',  # 运营商客户服务（Mobifone套餐服务）
    '191': '运营商',  # Viettel服务号码
    '1595': '运营商',  # 特殊营销服务（Viettel）
    '195': '运营商',  # Mobifone客服
    '789': '运营商',  # Mobifone套餐注册
    # '155': '其他',
    '9748': '运营商',  # Viettel游戏服务
    '9241': '运营商',  # Mobifone退订服务
    '1402': '其他',
    '9488': '运营商',  # Vinaphone视频服务
    '9969': '银行',  # 银行特殊服务
    # '5092': '其他',  # 验证码常用短号
    # '8099': '其他',  # 验证码常用短号
    # '8044': '其他',  # 验证码常用短号
    '1221': '运营商',  # 音乐服务（IMUZIK）
    '9062': '运营商',  # 视频服务（Viettel）

    # ====== 新增映射（基于完整分析） ======
    # 运营商核心服务
    '198': '运营商',  # Viettel主服务号
    '9923': '运营商',  # Vinaphone营销服务
    '9090': '运营商',  # Mobifone客服
    '1077': '运营商',  # Mobifone数据服务
    '193': '运营商',  # Viettel通知服务
    '333': '运营商',  # Vinaphone抽奖服务
    '9135': '运营商',  # Viettel农业服务
    '909': '运营商',  # Viettel客服
    '1331': '运营商',  # TV360电视服务
    '199': '运营商',  # Viettel客服主号
    '5108': '运营商',  # Vinaphone娱乐服务
    '9628': '运营商',  # Vinaphone娱乐服务
    '1567': '运营商',  # 未明确运营商服务
    '1356': '运营商',  # Viettel营销服务

    # 金融服务
    '1313': '贷款机构',  # 多品牌金融服务（CAKE/VIB等）
    '1551': '贷款机构',  # 金融客服专线（CAKE/HomeCredit等）
    '90004': '银行',  # 银行服务（VIB/FE CREDIT）

    # 其他服务
    '6789': '其他',  # VNSKY娱乐平台
    '1250': '其他',  # VNSKY客服
    # '777556666': '其他', # 未明确服务
    # '777': '其他',     # 未明确服务
    '1379': '银行'  # 银行服务（VIB）但已归类到1551
    # '996': '其他',     # 未明确服务
    # '9947': '其他',    # 未明确服务
    # '135': '其他',     # 未明确服务
    # '156': '其他',     # 未明确服务
    # '159': '其他',     # 未明确服务
    # '169': '其他',     # 未明确服务
    # '179': '其他',     # 未明确服务
    # '189': '其他',     # 未明确服务
    # '1999': '其他',    # 未明确服务

    # # 特殊服务（新增类别）
    # '1221': '娱乐',    # IMUZIK音乐服务（从运营商调整为娱乐）
    # '9062': '娱乐',    # 视频服务（从运营商调整为娱乐）
}

# 运营商机构关键词列表
OPERATOR_INSTITUTIONS_EXTENDED = [
    'VIETTEL', 'MOBIFONE', 'VINAPHONE', 'VIETNAMOBILE', 'GMOBILE', 'REDSUN',
    'VNM', 'VT', 'GH', 'MobiFone', 'Vinaphone', 'Viettel', 'Vietnamobile'
]

# 银行机构名称列表
BANK_INSTITUTIONS = [
    'tpbank', 'vietcombank', 'acb', 'bidv', 'techcombank', 'vib', 'vpbank',
    'shb', 'scb', 'ocb', 'msb', 'hdbank', 'kienvietbank', 'lienvietpostbank',
    'bacabank', 'abbank', 'agribank', 'dongabank', 'eximbank', 'gpbank',
    'kienlongbank', 'namabank', 'ncb', 'oceanbank', 'pgbank', 'pvcombank',
    'saigonbank', 'seabank', 'vietabank', 'vietinbank', 'sacombank',
    'vietcapitalbank', 'publicbank', 'shinhanbank', 'cimb', 'hsbc',
    'standardchartered', 'anz', 'uob', 'wooribank', 'indovinabank', 'vrb'
]

# 购物机构关键词列表
SHOPPING_INSTITUTIONS = [
    'LEIKA', 'CROCS', 'SHOPEE', 'LAZADA', 'TIKI', 'SENDO', 'FPT', 'ARISTINO', 'CAYVANG',
    'MOMO', 'ZALOPAY', 'VIETTELPAY', 'ONEPAY', 'VNPAY', 'AIRPAY', 'MYPAY', 'PAYOO',
    'HASAKI', 'MEDIAMART', 'DIENMAYXANH', 'NGUYEN KIM', 'THIEN LONG', 'VINAMILK',
    'UNIQLO', 'H&M', 'ZARA', 'ADIDAS', 'NIKE', 'PUMA', 'GUCCI', 'LV', 'PRADA'
]

# 预定义关键词列表
bank_keywords = [
    'tpbank', 'vietcombank', 'acb', 'bidv', 'techcombank', 'vib', 'vpbank',
    'shb', 'scb', 'ocb', 'msb', 'hdbank', 'kienvietbank', 'lienvietpostbank',
    'bacabank', 'abbank', 'agribank', 'dongabank', 'eximbank', 'gpbank',
    'kienlongbank', 'namabank', 'ncb', 'oceanbank', 'pgbank', 'pvcombank',
    'saigonbank', 'seabank', 'vietabank', 'vietinbank', 'sacombank',
    'vietcapitalbank', 'publicbank', 'shinhanbank', 'cimb', 'hsbc',
    'standardchartered', 'anz', 'uob', 'wooribank', 'indovinabank', 'vrb',
    # 增强的交易特征词
    'stk', 'so tai khoan', 'tai khoan', 'the', 'card', 'atm card', 'credit card',
    'vnd', 'usd', 'currency', 'so du', 'so du kha dung', 'transaction',
    'ps', 'gd', 'pos', 'atm', 'giatri', 'gia tri',
    'so tien', 'amount', 'chuyen khoan', 'rut tien', 'nap tien', 'thanh toan',
    'vib online', 'online banking', 'internet banking', 'account number',
    'transaction id', 'balance', 'available balance'
]

loan_keywords = [
    'fecredit', 'homecredit', 'prudential', 'tima', 'akulaku', 'easycredit',
    'miraeasset', 'hd-saison', 'shinhan', 'lotte', 'vnfinance', 'vnpay', 'mpos',
    'capital craft', 'cash crest', 'credit ease', 'flexi credit', 'lend link',
    'myvay', 'prime credit', 'swift funds', 'vaypay', 'soloan', 'tien 24',
    'fin vui', 'vay no', 'viet dong', 'viet dong e', 'viet dong pro', 'vi tot',
    'live cash', 'cash365', 'chia khoa vang', 'fastdong', 'mdong', 'sdong',
    'tieno', '79dong', 'moneyveo', 'vayantoan', 'vaykipthoi', 'tientay24',
    'mekongmobile', 'mar vay', 'okcredit', 'timvay', 'dh loan', 'catcredi',
    'yocredi', 'think credit', 'kredivo', 'app vay nở', 'ví bắc nam', 'ví tiện lợi',
    'sky credit', 'takomo', 'kdongcredit', 'mcredit', 'tnex finance', 'tnex',  # 新增Tiền24相关关键词
    'tien24', 'tiền24', 'tien 24', 'tiền 24'
]

operator_keywords = [
    'mobifone', 'vinaphone', 'viettel', 'vietnamobile', 'gmobile', 'redsun', 'vietnammobile',
    'mobi', 'vina', 'vtel', 'vnm', 'gh', 'vt', 'vnpt',
    'data', 'dữ liệu', 'du lieu', '4g', '5g', '3g', 'lte', 'internet',
    'cước', 'cuoc', 'cước phí', 'cuoc phi', 'cước data', 'cuoc data',
    'gói cước', 'goi cuoc', 'gói data', 'goi data', 'gói internet', 'goi internet',
    'sim', 'thẻ sim', 'the sim', 'sim số', 'sim so', 'esim',
    'roaming', 'data roaming', 'dataroaming',
    'tốc độ cao', 'toc do cao', 'tốc độ', 'toc do', 'băng thông rộng', 'bang thong rong',
    'tổng đài', 'tong dai', 'hotline', 'hỗ trợ', 'ho tro', 'chăm sóc khách hàng', 'cham soc khach hang',
    'thuê bao', 'thue bao', 'số thuê bao', 'so thue bao', 'dịch vụ', 'dich vu',
    'khuyến mãi', 'khuyen mai', 'ưu đãi', 'uu dai', 'combo', 'promo', 'sale', 'deal',
    'tặng data', 'tang data', 'miễn phí', 'mien phi', 'free data',
    'đăng ký', 'dang ky', 'kích hoạt', 'kich hoat', 'gia hạn', 'gia han',
    'cảnh báo', 'canh bao', 'thông báo', 'thong bao', 'nhắc nhở', 'nhac nho'
]

shopping_keywords = [
    'fpt', 'aristino', 'shop', 'cayvang', 'cps', 'vietnam post', 'postpay', 'viettel pay'
]

verification_keywords = [
    'otp', 'mã xác thực', 'ma xac thuc', 'xác nhận', 'xac nhan', 'verify', 'mã otp', 'ma otp',
    'xác thực', 'xac thuc', 'mã xác nhận', 'ma xac nhan', 'mat khau', 'password', 'pin'
]

transaction_keywords = [
    'rút tiền', 'rut tien', 'chuyển khoản', 'chuyen khoan', 'nhận tiền', 'nhan tien',
    'thanh toán', 'thanh toan', 'tiền vào', 'tien vao', 'tiền ra', 'tien ra', 'ps', 'sd',
    'so du', 'số dư', 'gửi tiền', 'gui tien', 'chuyen tien', 'chuyển tiền', 'nap tien',
    'nap the', 'nap card', 'gd', 'giao dich', 'giai ngan', 'giai ngan', 'tk'
]

repayment_keywords = [
    'trả góp', 'tra gop', 'trả nợ', 'tra no', 'hoàn nợ', 'hoan no', 'đáo hạn', 'dao han',
    'quá hạn', 'qua han', 'trễ hạn', 'tre han', 'thanh toan', 'thanh toán', 'tra no',
    'tra gop', 'tới hạn', 'quá hạn', 'quá hạn thanh toán', 'tới hạn thanh toán'
]

collection_keywords = [
    'nhắc', 'nhac', 'reminder', 'quá hạn', 'qua han', 'trễ hạn', 'tre han', 'đóng tiền',
    'dong tien', 'thanh toan', 'thanh toán', 'nhắc nợ', 'nhac no', 'báo nợ', 'bao no',
    'truy thu', 'thu hồi nợ', 'thu hoi no', 'trốn tránh', 'trốn nợ', 'tranh thủ'
]

loan_ad_keywords = [
    'vay', 'cho vay', 'tư vấn', 'tu van', 'hỗ trợ', 'ho tro', 'lãi suất', 'lai suat',
    'tài chính', 'tai chinh', 'tín chấp', 'tin chap', 'thế chấp', 'the chap', 'đăng ký',
    'dang ky', 'sdt', 'hotline', 'zalo', 'lien he', 'call', 'alo', 'chi can', 'khong can'
]

marketing_keywords = [
    'km', 'khuyen mai', 'khuyến mãi', 'uu dai', 'ưu đãi', 'ctkm',
    'chuong trinh khuyen mai', 'chương trình khuyến mãi',
    'chuong trinh uu dai', 'chương trình ưu đãi',
    'giảm giá', 'giam gia', 'giam', 'giảm', 'discount', 'sale', 'off',
    'giảm sốc', 'giam soc', 'sale sốc', 'sale soc',
    'giá sốc', 'gia soc', 'flash sale', 'sale flash',
    'miễn phí', 'mien phi', 'free', 'zero đ', 'zero d',
    'miễn cước', 'mien cuoc', 'free data', 'free internet',
    'tặng', 'tang', 'tặng thêm', 'tang them', 'bonus', 'quà tặng', 'qua tang'
]

recharge_keywords = [
    'nap the', 'nạp thẻ', 'nap tien', 'nạp tiền', 'thanh toan', 'thanh toán', 'đóng tiền',
    'dong tien', 'recharge', 'topup', 'nap card', 'mua the cao', 'the cao'
]

arrears_keywords = [
    'hết tiền', 'het tien', 'dừng dịch vụ', 'dung dich vu', 'ngừng dịch vụ', 'ngung dich vu',
    'tạm ngưng', 'tam ngung', 'hết hạn', 'het han', 'gia han khong thanh cong'
]

data_notification_keywords = [
    'data', 'lưu lượng', 'luu luong', 'gb', 'mb', 'tốc độ', 'toc do', 'internet', '3g',
    '4g', '5g', 'dung luong', 'toc do cao'
]

# 信用卡补充关键词
credit_card_keywords = [
    'credit card', 'the tin dung', 'visa', 'mastercard', 'creditcard',
    'the credit', '信用卡', 'thẻ tín dụng'
]
# 二级分类关键词映射
SECONDARY_KEYWORDS_MAP = {
    '验证码': verification_keywords,
    '动账提示': transaction_keywords,
    '还款提醒': repayment_keywords,
    '催收': collection_keywords,
    '贷款广告': loan_ad_keywords,
    '授信通过': loan_ad_keywords,
    '部分还款': repayment_keywords,
    '还款行为': repayment_keywords,
    '结清还款': repayment_keywords,
    '授信拒绝': loan_ad_keywords
}

# 运营商分类关键词映射
OPERATOR_CATEGORY_MAP = {
    '充值': recharge_keywords,
    '缴费': recharge_keywords,
    '欠费': arrears_keywords,
    '停机': arrears_keywords,
    '流量通知': data_notification_keywords,
    '营销': marketing_keywords,
    '验证码': verification_keywords
}

# 银行强提示词
BANK_STRONG_INDICATORS = [
    'tk', 'stk', 'so du', 'so du kha dung', 'account', 'balance', 'available balance',
    'transaction', 'ps', 'gd', 'chuyen khoan', 'rut tien', 'nap tien', 'thanh toan',
    'transfer', 'withdraw', 'deposit', 'payment', 'pos', 'atm', 'merchant'
]

# 运营商强提示词
OPERATOR_STRONG_INDICATORS = [
    'sim', 'data', 'internet', '4g', '5g', '3g', 'lte', 'goi cuoc', 'cuoc phi', 'nap the',
    'nap tien', 'recharge', 'topup', 'thue bao', 'tong dai', 'hotline', 'ho tro', 'cskh'
]


def preprocess_text(text: str) -> str:
    """改进的预处理函数，保留关键数字和符号"""
    # 保留金额模式（如50,000VND）
    text = re.sub(r'(\d+[,\d]*\s*(vnd|usd|d))', '[AMOUNT]', text, flags=re.IGNORECASE)

    # 保留贷款进度符号（∆tr）
    text = re.sub(r'∆\s*tr', '[LOAN_PROGRESS]', text, flags=re.IGNORECASE)

    # 移除其他∆和∇符号
    text = re.sub(r'[∆∇]', ' ', text)

    # 移除特殊字符但保留基本格式
    text = re.sub(r'[^\w\s\[\]]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text.lower()


def classify_sender(sender: str) -> Tuple[str, str]:
    """根据发送方分类短信"""
    sender_lower = sender.lower()

    # 1. 检查短号码映射
    if sender_lower in SHORT_CODE_MAPPING:
        primary_category = SHORT_CODE_MAPPING[sender_lower]

        # 特殊处理验证码短号
        if primary_category == '验证码':
            return '运营商', '验证码'

        # 特殊处理运营商营销服务
        if sender_lower in ['999', '1595', '9923']:
            return '运营商', '营销活动'

        return primary_category, ''

    # 2. 检查银行发送方
    for bank in BANK_SENDER_KEYWORDS:
        if bank.lower() in sender_lower:
            return '银行', ''

    # 3. 检查贷款机构发送方
    for loan in LOAN_SENDER_KEYWORDS:
        if loan.lower() in sender_lower:
            return '贷款机构', ''

    # 4. 检查运营商发送方
    for operator in OPERATOR_SENDER_KEYWORDS:
        if operator.lower() in sender_lower:
            return '运营商', ''

    # 5. 检查购物发送方
    for shop in SHOPPING_SENDER_KEYWORDS:
        if shop.lower() in sender_lower:
            return '购物', ''

    if sender_lower.startswith('19') and len(sender_lower) < 9:
        return '运营商', ''

    return '', ''


def cross_validate_category(text: str, current_category: str, matched_keywords: List[str]) -> Tuple[str, List[str]]:
    """交叉验证分类结果，使用正则表达式优化性能"""
    text_upper = text.upper()  # 用于机构关键词匹配

    # 1. 检查是否包含购物机构关键词（最高优先级）
    shopping_pattern = r'\b(' + '|'.join([re.escape(shop) for shop in SHOPPING_INSTITUTIONS]) + r')\b'
    shopping_matches = re.findall(shopping_pattern, text_upper)

    if shopping_matches:
        return '购物', shopping_matches + matched_keywords

    # 2. 检查是否包含运营商机构关键词（第二优先级）
    operator_pattern = r'\b(' + '|'.join([re.escape(operator) for operator in OPERATOR_INSTITUTIONS_EXTENDED]) + r')\b'
    operator_matches = re.findall(operator_pattern, text_upper)

    if operator_matches:
        return '运营商', operator_matches + matched_keywords

    # 3. 检查是否包含银行机构关键词（第三优先级）
    bank_pattern = r'\b(' + '|'.join([re.escape(bank) for bank in BANK_INSTITUTIONS]) + r')\b'
    bank_matches = re.findall(bank_pattern, text_upper)

    # 特殊处理MB银行
    filtered_bank_matches = []
    for match in bank_matches:
        if match.lower() == 'mb':
            if not any(exclude in text_upper for exclude in ['MOBIFONE', 'MOBIEDU', 'COMBO KHÓA HỌC']):
                filtered_bank_matches.append(match)
        else:
            filtered_bank_matches.append(match)

    if filtered_bank_matches:
        return '银行', filtered_bank_matches + matched_keywords

    # 如果以上都不匹配，返回当前分类
    return current_category, matched_keywords
def detect_primary_category(text: str, sender: str = "") -> Tuple[str, List[str]]:
    """改进的一级分类检测函数，使用正则表达式优化性能"""
    # 首先根据发送方分类
    if sender:
        sender_primary, sender_secondary = classify_sender(sender)
        if sender_primary:
            return sender_primary, [sender]

    text_lower = text.lower()
    matches = []

    # 1. 贷款机构检测 - 最高优先级
    # 构建贷款相关关键词的正则表达式
    loan_financial_terms = [
        'vay', 'cho vay', 'lai suat', 'lãi suất', 'ho so vay', 'tra no', 'trả nợ',
        'tín dụng', 'tin dung', 'hạn mức', 'han muc', 'duyet ho so', 'duyet ho so',
        'giải ngân', 'giai ngan', 'trả góp', 'tra gop', 'duyet', 'giai ngan',
        'khoan vay', 'khoản vay', 'vay tien', 'vay tiền', 'vay nhanh', 'vay online',
        'vay tín chấp', 'vay tin chap', 'vay thế chấp', 'vay the chap', 'vay tiêu dùng',
        'vay tieu dung', 'lending', 'loan', 'credit', 'borrow', 'finance'
    ]

    loan_keywords = [
        'fecredit', 'homecredit', 'prudential', 'tima', 'akulaku', 'easycredit',
        'miraeasset', 'hd-saison', 'shinhan', 'lotte', 'vnfinance', 'vnpay', 'mpos',
        'capital craft', 'cash crest', 'credit ease', 'flexi credit', 'lend link',
        'myvay', 'prime credit', 'swift funds', 'vaypay', 'soloan', 'tien 24',
        'fin vui', 'vay no', 'viet dong', 'viet dong e', 'viet dong pro', 'vi tot',
        'live cash', 'cash365', 'chia khoa vang', 'fastdong', 'mdong', 'sdong',
        'tieno', '79dong', 'moneyveo', 'vayantoan', 'vaykipthoi', 'tientay24',
        'mekongmobile', 'mar vay', 'okcredit', 'timvay', 'dh loan', 'catcredi', 'catcredit',
        'yocredi', 'think credit', 'kredivo', 'app vay nở', 'ví bắc nam', 'ví tiện lợi',
        'sky credit', 'takomo', 'kdongcredit', 'mcredit', 'tnex finance', 'tnex',
        'tien24', 'tiền24', 'tien 24', 'tiền 24', 'happycredit', 'happycred1t',
        'vamo', 'timo', 'vaycucde', 'vaytienonline', 'oncredit', 'cashwagon',
        'tien24h', 'tiền24h', 'tien24.com', 'tiền24.com', 'tien24vn', 'tiền24vn',
        'tien24 vn', 'tiền24 vn', 'tien24.vn', 'tiền24.vn', 'tien24 online'
    ]

    loan_progress_terms = [
        'duyet ho so', 'duyet', 'duyệt', 'giai ngan', 'disbursement', 'xet duyet',
        'xét duyệt', 'tien do', 'tiến độ', 'progress', 'ho so', 'application'
    ]

    # 构建贷款关键词的正则表达式
    loan_pattern = r'\b(' + '|'.join([re.escape(term) for term in loan_financial_terms + loan_keywords + loan_progress_terms]) + r')\b'
    loan_matches = re.findall(loan_pattern, text_lower)

    if loan_matches:
        matches.extend(loan_matches)
        category, final_matches = '贷款机构', list(set(matches))
        return cross_validate_category(text, category, final_matches)

    # 2. 银行检测 - 第二优先级
    # 银行交易特征词正则表达式
    bank_transaction_indicators = [
        'tk \d+', 'stk \d+', 'so tk \d+', 'tai khoan \d+', 'account \d+',
        'so du', 'balance', 'so du kha dung', 'available balance',
        'chuyen khoan', 'rut tien', 'nap tien', 'thanh toan',
        'transfer', 'withdraw', 'deposit', 'payment',
        'pos', 'atm',
        'jcb', 'visa', 'mastercard', 'amex', 'credit card',
        'the tin dung', '信用卡', 'thẻ tín dụng',
        'ps \d+', 'gd \d+', 'giao dich \d+', 'transaction \d+',
        'han muc', 'han muc kha dung', 'hạn mức', 'hạn mức khả dụng'
    ]

    # 构建银行交易特征词正则表达式
    bank_transaction_pattern = r'\b(' + '|'.join([re.escape(indicator) for indicator in bank_transaction_indicators]) + r')\b'
    bank_transaction_matches = re.findall(bank_transaction_pattern, text_lower)

    if bank_transaction_matches:
        matches.extend(bank_transaction_matches)
        category, final_matches = '银行', matches
        return cross_validate_category(text, category, final_matches)

    # 银行名称正则表达式
    bank_keywords_list = [
        'tpbank', 'vietcombank', 'acb', 'bidv', 'techcombank', 'vib', 'vpbank',
        'shb', 'scb', 'ocb', 'msb', 'hdbank', 'kienvietbank', 'lienvietpostbank',
        'bacabank', 'abbank', 'agribank', 'dongabank', 'eximbank', 'gpbank',
        'kienlongbank', 'namabank', 'ncb', 'oceanbank', 'pgbank', 'pvcombank',
        'saigonbank', 'seabank', 'vietabank', 'vietinbank', 'sacombank',
        'vietcapitalbank', 'publicbank', 'shinhanbank', 'cimb', 'hsbc',
        'standardchartered', 'anz', 'uob', 'wooribank', 'indovinabank', 'vrb'
    ]

    bank_name_pattern = r'\b(' + '|'.join([re.escape(bank) for bank in bank_keywords_list]) + r')\b'
    bank_name_matches = re.findall(bank_name_pattern, text_lower)

    # 特殊处理MB银行和Shinhan银行
    filtered_bank_matches = []
    for match in bank_name_matches:
        if match == 'mb':
            if not any(exclude in text_lower for exclude in ['mobifone', 'mobiedu', 'combo khóa học']):
                filtered_bank_matches.append(match)
        elif match == 'shinhan':
            if 'shinhanlife' not in text_lower:
                filtered_bank_matches.append(match)
        else:
            filtered_bank_matches.append(match)

    if filtered_bank_matches:
        matches.extend(filtered_bank_matches)
        category, final_matches = '银行', matches
        return cross_validate_category(text, category, final_matches)

    # 3. 购物检测 - 第三优先级
    shopping_keywords_list = [
        'fpt', 'aristino', 'shop', 'cayvang', 'cps', 'vietnam post', 'postpay', 'viettel pay',
        'mua sắm', 'mua sam', 'shopping', 'cửa hàng', 'cua hang', 'store', 'giỏ hàng', 'gio hang',
        'đặt hàng', 'dat hang', 'order', 'sản phẩm', 'san pham', 'product', 'thanh toán đơn hàng',
        'giao hàng', 'giao hang', 'delivery', 'vận chuyển', 'van chuyen', 'ship', 'shipping',
        'cart', 'checkout', 'purchase', 'buy', 'mua', 'đơn hàng', 'don hang'
    ]

    shopping_pattern = r'\b(' + '|'.join([re.escape(keyword) for keyword in shopping_keywords_list]) + r')\b'
    shopping_matches = re.findall(shopping_pattern, text_lower)

    if shopping_matches:
        matches.extend(shopping_matches)
        category, final_matches = '购物', matches
        return cross_validate_category(text, category, final_matches)

    # 4. 运营商检测 - 第四优先级
    operator_specific_indicators = [
        'data', 'internet', '4g', '5g', '3g', 'lte',
        'goi cuoc', 'cuoc phi', 'cuoc data',
        'nap the', 'nap tien', 'recharge', 'topup',
        'sim', 'the sim', 'esim', 'thue bao',
        'tong dai', 'hotline', 'ho tro', 'cskh',
        'mobifone', 'vinaphone', 'viettel', 'vietnamobile', 'gmobile', 'redsun', 'vietnammobile',
        'mobi', 'vina', 'vtel', 'vnm', 'gh', 'vt', 'vnpt',
        'du lieu', 'cước', 'cuoc', 'cước phí', 'cuoc phi', 'cước data', 'cuoc data',
        'gói cước', 'goi cuoc', 'gói data', 'goi data', 'gói internet', 'goi internet',
        'sim số', 'sim so', 'roaming', 'data roaming', 'dataroaming',
        'tốc độ cao', 'toc do cao', 'tốc độ', 'toc do', 'băng thông rộng', 'bang thong rong',
        'tổng đài', 'tong dai', 'hỗ trợ', 'ho tro', 'chăm sóc khách hàng', 'cham soc khach hang',
        'thuê bao', 'thue bao', 'số thuê bao', 'so thue bao', 'dịch vụ', 'dich vu',
        'khuyến mãi', 'khuyen mai', 'ưu đãi', 'uu dai', 'combo', 'promo', 'sale', 'deal',
        'tặng data', 'tang data', 'miễn phí', 'mien phi', 'free data',
        'đăng ký', 'dang ky', 'kích hoạt', 'kich hoat', 'gia hạn', 'gia han',
        'cảnh báo', 'canh bao', 'thông báo', 'thong bao', 'nhắc nhở', 'nhac nho'
    ]

    operator_pattern = r'\b(' + '|'.join([re.escape(indicator) for indicator in operator_specific_indicators]) + r')\b'
    operator_matches = re.findall(operator_pattern, text_lower)

    if operator_matches:
        matches.extend(operator_matches)
        category, final_matches = '运营商', matches
        return cross_validate_category(text, category, final_matches)

    category, final_matches = '其他', []
    return cross_validate_category(text, category, final_matches)



def detect_secondary_category(text: str, primary_category: str, sender: str = "") -> Tuple[str, List[str]]:
    """检测二级分类 - 使用正则表达式优化性能"""
    text_lower = text.lower()
    matched_keywords = []

    # 特殊处理验证码短号
    if sender in ['5092', '8099', '8044']:
        return '验证码', ['验证码短号']

    # 特殊处理运营商营销服务
    if sender in ['999', '1595', '9923']:
        return '营销活动', ['营销短号']

    if primary_category == '银行':
        # 银行交易的特定特征词正则表达式
        transaction_indicators = [
            'giatri', 'gia tri', 'so tien', 'amount', 'vnd', 'usd',
            'tai ', 'tai cua hang', 'pos', 'atm', 'merchant',
            'stk', 'so tai khoan', 'the', 'card', 'tk', 'sd tk', 'sd',
            'thanh toan', 'chuyen khoan', 'rut tien', 'nap tien',
            'ps', 'gd', 'giao dich', 'transaction', 'tk \d+', 'stk \d+', 'so tk \d+', 'tai khoan \d+', 'account \d+',
            'so du', 'balance', 'so du kha dung', 'available balance',
            'chuyen khoan', 'rut tien', 'nap tien', 'thanh toan',
            'transfer', 'withdraw', 'deposit', 'payment',
            'pos', 'atm',
            'jcb', 'visa', 'mastercard', 'amex', 'credit card',
            'the tin dung', '信用卡', 'thẻ tín dụng',
            'ps \d+', 'gd \d+', 'giao dich \d+', 'transaction \d+',
            'han muc', 'han muc kha dung', 'hạn mức', 'hạn mức khả dụng'
        ]

        transaction_pattern = r'\b(' + '|'.join([re.escape(indicator) for indicator in transaction_indicators]) + r')\b'
        transaction_matches = re.findall(transaction_pattern, text_lower)
        matched_keywords.extend(transaction_matches)

        if matched_keywords:
            return '动账提示', matched_keywords

        # 检查其他银行二级分类
        for category, keywords in SECONDARY_KEYWORDS_MAP.items():
            if category == '动账提示':  # 已检查过
                continue

            # 构建正则表达式模式
            pattern = r'\b(' + '|'.join([re.escape(kw) for kw in keywords]) + r')\b'
            matches = re.findall(pattern, text_lower)

            if matches:
                matched_keywords.extend(matches)
                return category, matched_keywords

    elif primary_category == '运营商':
        # 运营商有专门的分类
        for category, keywords in OPERATOR_CATEGORY_MAP.items():
            # 构建正则表达式模式
            pattern = r'\b(' + '|'.join([re.escape(kw) for kw in keywords]) + r')\b'
            matches = re.findall(pattern, text_lower)

            if matches:
                matched_keywords.extend(matches)
                return category, matched_keywords

    elif primary_category == '贷款机构':
        # 贷款机构的二级分类
        for category, keywords in SECONDARY_KEYWORDS_MAP.items():
            # 构建正则表达式模式
            pattern = r'\b(' + '|'.join([re.escape(kw) for kw in keywords]) + r')\b'
            matches = re.findall(pattern, text_lower)

            if matches:
                matched_keywords.extend(matches)
                return category, matched_keywords

    return '', []

def generate_pattern(text: str, primary_kws: List[str], secondary_kws: List[str]) -> str:
    """生成正则表达式模式"""
    if not text.strip():
        return ""

    # 预处理文本 - 使用改进的预处理函数
    processed_text = preprocess_text(text)
    if not processed_text:
        return ""

    # 构建关键词模式
    pattern_parts = []

    # 添加一级分类关键词
    for kw in primary_kws:
        pattern_parts.append(re.escape(kw.lower()))

    # 添加二级分类关键词
    for kw in secondary_kws:
        pattern_parts.append(re.escape(kw.lower()))

    # 如果没有匹配到关键词，则返回空
    if not pattern_parts:
        return ""

    # 构建最终模式
    unique_patterns = list(set(pattern_parts))  # 去重
    unique_patterns.sort(key=len, reverse=True)  # 按长度排序，优先匹配长的

    # 限制关键词数量在3-15个之间
    if len(unique_patterns) > 15:
        unique_patterns = unique_patterns[:15]

    # 构建正则表达式
    pattern = ".*".join(unique_patterns)

    return pattern


def classify_sms(text: str, sender: str = "") -> Dict[str, str]:
    """分类短信并生成正则表达式模式，考虑发送方"""
    if not text.strip():
        return {"一级分类": "", "二级分类": "", "pattern": ""}

    # 检测一级分类（考虑发送方）
    primary_category, primary_kws = detect_primary_category(text, sender)

    # 检测二级分类（考虑发送方）
    secondary_category, secondary_kws = detect_secondary_category(text, primary_category, sender)
    # print('primary_kws\n',primary_kws)
    # print('secondary_kws\n',secondary_kws)
    # 生成pattern
    pattern = generate_pattern(text, primary_kws, secondary_kws)

    return {
        "一级分类": primary_category,
        "二级分类": secondary_category,
        "pattern": pattern
    }


# %%
###################################################金额函数#####################################
import re
from typing import List, Dict, Any


def extract_amount_with_context(text: str) -> List[Dict[str, Any]]:
    """
    增强版上下文感知金额提取函数（带优先级）
    优化了交易金额识别，特别是银行交易格式
    """
    # ====== 0. 预处理 ======
    if not isinstance(text, str) or not text.strip():
        return []

    orig_text = text
    text = re.sub(r'\s+', ' ', text.strip())
    text_lower = text.lower()

    # ====== 1. 高级噪声过滤 ======
    if re.search(r'[a-z0-9]{8,}', text_lower) and not re.search(r'vnd|đ|tr|k', text_lower):
        return []

    # ====== 2. 文本归一化 ======
    text = re.sub(r'[đd₫]|vnd', 'đ', text, flags=re.IGNORECASE)
    text = re.sub(r'\.\s*đ', '000đ', text)
    text = re.sub(r'(\d)([đdktr])', r'\1 \2', text, flags=re.IGNORECASE)

    # ====== 3. 定义金额基础模式 ======
    # 新的金额基础模式 - 能处理带空格的大额数字和符号
    金额基础模式 = r"([+-]?\s*\d[\d\s.,]*\d)\s*(vnd|vnđ|đồng|dong|triệu|tr|k|ngàn|nghìn|nghin|d)?"

    # 支出金额模式
    支出金额_patterns = [
        r"ps\s*" + 金额基础模式,
        r"chi\s*" + 金额基础模式,
        r"thanh\s*toán\s*" + 金额基础模式,
        r"phi\s*" + 金额基础模式,
        r"vnd\s*-\s*" + 金额基础模式,
        r"thanh\s*toan\s*" + 金额基础模式,
        r"ps\s*-\s*" + 金额基础模式,
        r"ps\s*[+-]\s*" + 金额基础模式,
        r"cước\s*" + 金额基础模式,
        r"giá\s*cước\s*" + 金额基础模式,
        r"trả\s*nợ\s*" + 金额基础模式,
        r"tra\s*no\s*" + 金额基础模式,
        r"tiền\s*" + 金额基础模式,
        r"so\s*tien\s*" + 金额基础模式,
        r"thanh toán\s*" + 金额基础模式,
        r"thu\s*" + 金额基础模式,
        r"TK\s+\d+\s+VND\s+-\s+(\d[\d\s.,]*)\s+SD\s+\d[\d\s.,]*"
    ]

    # 收入金额模式
    收入金额_patterns = [
        r"vnd\s*\+\s*" + 金额基础模式,
        r"nap\s*tien\s*" + 金额基础模式,
        r"nạp\s*tiền\s*" + 金额基础模式,
        r"nhan\s*tien\s*" + 金额基础模式,
        r"nhận\s*tiền\s*" + 金额基础模式,
        r"thu\s*" + 金额基础模式,
        r"vnd\s*\+\s*" + 金额基础模式,
        r"hoan\s*tien\s*" + 金额基础模式,
        r"hoàn\s*tiền\s*" + 金额基础模式,
        r"hoan\s*" + 金额基础模式,
        r"lãi\s*suất\s*" + 金额基础模式,
        r"thưởng\s*" + 金额基础模式,
        r"chuyển\s*khoản\s*" + 金额基础模式,
        r"nạp\s*tiền\s*" + 金额基础模式,
        r"TK\s+\d+\s+VND\s+\+\s+(\d[\d\s.,]*)\s+SD\s+\d[\d\s.,]*",
        r"vào\s*[:]?\s*" + 金额基础模式,
        r"vao\s*[:]?\s*" + 金额基础模式,
    ]

    # 交易金额模式 - 优先级最高
    交易金额_patterns = [
        # 银行交易格式
        # r"mbv\s*[+-]\s*" + 金额基础模式,
        r"mbv\s*" + 金额基础模式,
        r"tk\s+\d+\s*" + 金额基础模式,
        r"gd\s*" + 金额基础模式,
        # r"ps\s*[+-]\s*" + 金额基础模式,
        r"ps\s*" + 金额基础模式,
        # 通用交易格式
        r"mua\s*" + 金额基础模式,
        r"chuyển\s*" + 金额基础模式,
        r"gia\s*" + 金额基础模式,
        r"giá\s*trị\s*" + 金额基础模式,
        r"tri\s*gia\s*" + 金额基础模式,
        r"số\s*tiền\s*" + 金额基础模式,
        r"giao dich\s*" + 金额基础模式,
        r"so\s*tien\s*" + 金额基础模式,
        r"gd\s*" + 金额基础模式,
        r"bán\s*" + 金额基础模式,
        r"TK\s+\d+\s+VND\s+([+-])\s+(\d[\d\s.,]*)\s+SD\s+\d[\d\s.,]*",
        r"BIDV\s*" + 金额基础模式,
    ]

    # 余额模式 - 优先级第二
    余额_patterns = [
        # 标准格式
        r"sd\s*[:]?\s*" + 金额基础模式,
        r"s[oố]\s*dư\s*[:]?\s*" + 金额基础模式,
        r"so\s*du\s*[:]?\s*" + 金额基础模式,
        # r"ps\s*[:]?\s*" + 金额基础模式,
        r"tài\s*khoản\s*[:]?\s*" + 金额基础模式,

        # 银行交易格式
        r"TK\s+\d+\s+VND\s+[+-]\s+\d[\d\s.,]*\s+SD\s+(\d[\d\s.,]*)",

        # 严格格式
        r"(?<!\w)sd\s+" + 金额基础模式,
        r"số\s*dư\s*$" + 金额基础模式,
    ]
    信用额度_patterns = [
        r"hạn\s*mức\s*tín\s*dụng\s*" + 金额基础模式,
        r"credit\s*" + 金额基础模式,
        r"tín\s*dụng\s*" + 金额基础模式,
        r"han\s*muc\s*" + 金额基础模式,
        r"han\s*muc\s*tin\s*dung\s*" + 金额基础模式,
        r"tin dung\s*" + 金额基础模式,
        r"hạn mức\s*" + 金额基础模式,
        r"hạn\s*mức\s*" + 金额基础模式
    ]

    放款金额_patterns = [
        r"khoản\s*vay\s*" + 金额基础模式,
        r"giai\s*ngan\s*" + 金额基础模式,
        r"gn\s*" + 金额基础模式,
        r"giải\s*ngân\s*" + 金额基础模式,
        r"vay\s*" + 金额基础模式,
        r"cho\s*vay\s*" + 金额基础模式,
        r"giải\s*ngân\s*" + 金额基础模式,
        r"khoản\s*vay\s*" + 金额基础模式
    ]

    提款金额_patterns = [
        r"chuyển\s*ra\s*" + 金额基础模式,
        r"rt\s*" + 金额基础模式,
        r"rút\s*tiền\s*" + 金额基础模式,
        r"rút\s*" + 金额基础模式,
        r"chuyển\s*khoản\s*" + 金额基础模式,
        r"rut\s*tien\s*" + 金额基础模式,
        r"rút\s*tiền\s*" + 金额基础模式,
        r"chuyển\s*khoản\s*" + 金额基础模式
    ]

    可用余额_patterns = [
        r"số\s*dư\s*khả\s*dụng\s*" + 金额基础模式,
        r"du\s*kha\s*dung\s*" + 金额基础模式,
        r"sd\s*khả\s*dụng\s*" + 金额基础模式,
        r"so\s*du\s*kha\s*dung\s*" + 金额基础模式,
        r"kha\s*dung\s*" + 金额基础模式,
        r"sd\s*kha\s*dung\s*" + 金额基础模式,
        r"so\s*du.*?kha\s*dung\s*" + 金额基础模式
    ]

    逾期金额_patterns = [
        r"qua\s*han\s*" + 金额基础模式,
        r"nợ\s*quá\s*hạn\s*" + 金额基础模式,
        r"nợ\s*" + 金额基础模式,
        r"no\s*" + 金额基础模式,
        r"no\s*qua\s*han\s*" + 金额基础模式,
        r"quá\s*hạn\s*thanh\s*toán\s*" + 金额基础模式,
        r"qua han\s*" + 金额基础模式,
        r"quá\s*hạn\s*" + 金额基础模式,
        r"trễ\s*hạn\s*" + 金额基础模式,
        r"tre\s*han\s*" + 金额基础模式
    ]

    # 新增的金额类型模式
    充值金额_patterns = [
        r"nap\s*the\s*" + 金额基础模式,
        r"nạp\s*thẻ\s*" + 金额基础模式,
        r"nap\s*tien\s*" + 金额基础模式,
        r"nạp\s*tiền\s*" + 金额基础模式,
        r"recharge\s*" + 金额基础模式
    ]

    流量金额_patterns = [
        r"data\s*" + 金额基础模式,
        r"lưu\s*lượng\s*" + 金额基础模式,
        r"luu\s*luong\s*" + 金额基础模式,
        r"gb\s*" + 金额基础模式,
        r"mb\s*" + 金额基础模式
    ]

    套餐费用_patterns = [
        r"gói\s*cước\s*" + 金额基础模式,
        r"goi\s*cuoc\s*" + 金额基础模式,
        r"cước\s*phí\s*" + 金额基础模式,
        r"cuoc\s*phi\s*" + 金额基础模式
    ]

    手续费_patterns = [
        r"phí\s*dịch\s*vụ\s*" + 金额基础模式,
        r"phi\s*dich\s*vu\s*" + 金额基础模式,
        r"phí\s*giao\s*dịch\s*" + 金额基础模式,
        r"phi\s*giao\s*dich\s*" + 金额基础模式
    ]

    罚金_patterns = [
        r"phạt\s*" + 金额基础模式,
        r"phat\s*" + 金额基础模式,
        r"phí\s*phạt\s*" + 金额基础模式,
        r"phi\s*phat\s*" + 金额基础模式
    ]

    # 金额类型映射
    金额类型到patterns = {
        '支出金额': 支出金额_patterns,
        '收入金额': 收入金额_patterns,
        '交易金额': 交易金额_patterns,
        '信用额度': 信用额度_patterns,
        '放款金额': 放款金额_patterns,
        '提款金额': 提款金额_patterns,
        '可用余额': 可用余额_patterns,
        '逾期金额': 逾期金额_patterns,
        '余额': 余额_patterns,
        '充值金额': 充值金额_patterns,
        '流量金额': 流量金额_patterns,
        '套餐费用': 套餐费用_patterns,
        '手续费': 手续费_patterns,
        '罚金': 罚金_patterns
    }

    # 金额提取优先级
    金额类型优先级 = [
        ('交易金额', 交易金额_patterns),
        ('余额', 余额_patterns),
        ('支出金额', 支出金额_patterns),
        ('收入金额', 收入金额_patterns),
        ('提款金额', 提款金额_patterns),
        ('信用额度', 信用额度_patterns),
        ('放款金额', 放款金额_patterns),
        ('可用余额', 可用余额_patterns),
        ('逾期金额', 逾期金额_patterns),
        ('充值金额', 充值金额_patterns),
        ('流量金额', 流量金额_patterns),
        ('套餐费用', 套餐费用_patterns),
        ('手续费', 手续费_patterns),
        ('罚金', 罚金_patterns)
    ]

    # ====== 5. 金额解析函数（保留符号） ======
    def parse_amount(amount_str: str, unit: str) -> float:
        """解析金额字符串并转换为数值，保留符号"""
        # 检查符号
        sign = 1
        if re.match(r'-\s*\d', amount_str):
            sign = -1
            amount_str = re.sub(r'-\s*', '', amount_str)
        elif re.match(r'\+\s*\d', amount_str):
            amount_str = re.sub(r'\+\s*', '', amount_str)
        else:
            sign = 1

        # 移除分隔符
        amount_str = re.sub(r'[ ,.]', '', amount_str)
        # 单位转换
        multiplier = 1
        if unit in ('k', 'ngàn', 'nghìn', 'nghin'):
            multiplier = 1000
        elif unit in ('tr', 'triệu'):
            multiplier = 1000000

        try:
            return sign * float(amount_str) * multiplier
        except ValueError:
            return 0.0

    # ====== 6. 金额提取 ======
    results = []
    matched_texts = set()

    # 按优先级顺序匹配
    for 金额类型, patterns in 金额类型优先级:
        for pattern in patterns:
            for match in re.finditer(pattern, text_lower, re.IGNORECASE):
                matched_str = match.group(0)
                if matched_str in matched_texts:
                    continue
                # print('match_str',matched_str,'pattern',pattern,'金额类型',金额类型)
                # 提取金额值和单位
                groups = match.groups()
                if len(groups) >= 2:
                    amount_str = groups[0].strip()
                    unit = groups[1].strip() if groups[1] else ""
                else:
                    continue
                # 解析金额
                amount_val = parse_amount(match.group(1), unit)
                if amount_val == 0:  # 允许负值
                    continue

                # 添加上下文片段
                start = max(0, match.start() - 10)
                end = min(len(text_lower), match.end() + 10)
                text_snippet = text_lower[start:end]

                # 添加到结果
                results.append({
                    "amount": amount_val,
                    "unit": "VND",
                    "label": 金额类型,
                    "amount_pattern": pattern,
                    "context": {
                        "text_snippet": text_snippet,
                        "raw_amount": amount_str + (unit if unit else "")
                    }
                })

                # 记录已匹配文本
                matched_texts.add(matched_str)

                # 限制最多5个金额字段
                if len(results) >= 5:
                    break

    # ====== 7. 上下文标签校正 ======
    context_labels = {
        '余额': ['so du', 'số dư', 'sd', 'ps', 'tk', 'sodu'],
        '收入金额': ['vào', 'vao', 'nap tien', 'nạp tiền'],
        '交易金额': ['ps', 'tk', 'mb', 'acb', 'vib', 'chuyen', 'chuyển', 'giao dich', 'mbv', 'gd', 'thanh toan', 'huy thanh toan'],
        '支出金额': ['thanh toan', 'chi', 'phi', 'ps', 'rút', 'rut'],
        '银行账号': ['mb', 'tk', 'acb', 'vcb', 'stk', 'số tài khoản']
    }

    for res in results:
        # 获取当前标签的关键词
        current_label = res["label"]
        current_keywords = context_labels.get(current_label, [])

        # 检查当前标签的关键词是否在上下文片段中出现
        current_label_match = any(
            re.search(kw, res["context"]["text_snippet"])
            for kw in current_keywords
        )

        # 如果当前标签的关键词存在，保留当前标签
        if current_label_match:
            continue

        # 否则，尝试校正为其他标签
        for label, keywords in context_labels.items():
            if label == current_label:
                continue

            if any(re.search(kw, res["context"]["text_snippet"]) for kw in keywords):
                res["label"] = label
                break
    # print(results)
    # 过滤掉银行账号
    results = [res for res in results if res["label"] != "银行账号"]
    # ====== 8. 后处理 ======
    # 定义需要金额范围限制的标签
    restricted_labels = {'交易金额', '收入金额', '支出金额'}

    # 对特定标签添加金额范围过滤 - 舍弃大于99999999或小于100的金额
    filtered_results = []
    for res in results:
        if res["label"] in restricted_labels:
            # 对限制的标签进行金额范围检查
            if 100 <= abs(res['amount']) <= 999999999:
                filtered_results.append(res)
        else:
            # 其他标签的金额不过滤
            filtered_results.append(res)

    # 去重
    unique_results = []
    seen = set()
    for res in filtered_results:
        key = (res["amount"], res["label"])
        if key not in seen:
            unique_results.append(res)
            seen.add(key)

    return unique_results