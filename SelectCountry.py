import xml.etree.ElementTree as ET
import re
import os
import msvcrt
from fuzzywuzzy import process
from colorama import Fore, Style, init
from xml_Utils import get_text, need_mag_para, open_xml, get_scheme

country_currency_map = {
    '自动AUT':  'AUT' ,
    '混合MIX':  'MIX' ,
    '阿拉伯联合酋长国': 'AED' ,
    '巴基斯坦': 'PKR' ,
    '美国': 'USD' ,
    '欧盟': 'EUR' ,
    '中国': 'CNY' ,
    '英国': 'GBP' ,
    '土耳其':   'TRL' ,
    '埃及': 'EGP' ,
    '墨西哥':   'MXN' ,
    '加纳': 'GHS' ,
    '乌干达':   'UGS' ,
    '印度尼西亚':   'IDR' ,
    '印度': 'INR' ,
    '新加坡':   'SGD' ,
    '马来西亚': 'MYR' ,
    '加拿大':   'CAD' ,
    '韩国': 'KRW' ,
    '秘鲁': 'PEN' ,
    '哥伦比亚': 'COP' ,
    '俄罗斯':   'RUB' ,
    '泰国': 'THB' ,
    '阿曼': 'OMR',
    '阿根廷':   'ARS' ,
    '老挝': 'LAK' ,
    '香港': 'HKD' ,
    '刚果民主共和国':   'CDF' ,
    '日本': 'JPY' ,
    '澳大利亚': 'AUD' ,
    '坦桑尼亚': 'TZS' ,
    '叙利亚':   'SYP' ,
    '瑞士': 'CHF' ,
    '卡塔尔':   'QAR' ,
    '以色列':   'ILS' ,
    '匈牙利':   'HUF' ,
    '波兰': 'PLN' ,
    '捷克共和国':   'CZK' ,
    '约旦': 'JOD' ,
    '沙特阿拉伯':   'SAR' ,
    '斯里兰卡': 'LKR' ,
    '马尔代夫': 'MVR' ,
    '新西兰':   'NZD' ,
    '巴西': 'BRL' ,
    '苏里南':   'SRD' ,
    '缅甸': 'MMK' ,
    '安哥拉':   'AOA' ,
    '保加利亚': 'BGN' ,
    '柬埔寨':   'KHR' ,
    '澳门': 'MOP' ,
    '台湾': 'TWD' ,
    '玻利维亚': 'BOB' ,
    '格鲁吉亚': 'GEL' ,
    '斐济': 'FJD' ,
    '埃塞俄比亚':   'ETB' ,
    '多米尼加共和国':   'DOP' ,
    '哥斯达黎加':   'CRC' ,
    '智利': 'CLP' ,
    '冈比亚':   'GMD' ,
    '几内亚':   'GNF' ,
    '克罗地亚': 'HRK' ,
    '海地': 'HTG' ,
    '科威特':   'KWD' ,
    '黎巴嫩':   'LBP' ,
    '摩洛哥':   'MAD' ,
    '乌兹别克斯坦': 'UZS' ,
    '哈萨克斯坦':   'KZT' ,
    '尼日利亚': 'NGN' ,
    '越南': 'VND' ,
    '菲律宾':   'PHP' ,
    '伊拉克':   'IQD' ,
    '挪威': 'NOK' ,
    '丹麦': 'DKK' ,
    '瑞典': 'SEK' ,
    '文莱': 'BND' ,
    '尼泊尔':   'NPR' ,
    '蒙古': 'MNT' ,
    '南非': 'ZAR' ,
    '毛里求斯': 'MUR' ,
    '阿尔及利亚':   'DZD' ,
    '苏丹': 'SDG' ,
    '突尼斯':   'TND' ,
    '伊朗': 'IRR' ,
    '利比亚':   'LYD' ,
    '孟加拉国': 'BDT' ,
    '朝鲜': 'KPW' ,
    '赞比亚':   'ZMW' ,
    '北马其顿': 'MKD' ,
    '白俄罗斯': 'BYR' ,
    '委内瑞拉': 'VES' ,
    '牙买加':   'JMD' ,
    '西非法郎': 'XOF' ,
    '美元 ': 'USD',
'欧元 ': 'EUR',
'英镑 ': 'GBP',
'加拿大元 ': 'CAD',
'澳大利亚元 ': 'AUD',
'日元 ': 'JPY',
'Cardano ': 'ADA',
'阿联酋迪拉姆 ': 'AED',
'阿富汗尼 ': 'AFN',
'阿尔巴尼列克 ': 'ALL',
'亚美尼亚德拉姆 ': 'AMD',
'荷兰盾 ': 'ANG',
'安哥拉宽扎 ': 'AOA',
'阿根廷比索 ': 'ARS',
'澳大利亚元 ': 'AUD',
'阿鲁巴或荷兰盾 ': 'AWG',
'阿塞拜疆马纳特 ': 'AZN',
'波斯尼亚可兑换马尔卡 ': 'BAM',
'巴巴多斯元 ': 'BBD',
'Bitcoin Cash ': 'BCH',
'孟加拉国塔卡 ': 'BDT',
'保加利亚列弗 ': 'BGN',
'巴林第纳尔 ': 'BHD',
'布隆迪法郎 ': 'BIF',
'百慕大元 ': 'BMD',
'文莱元 ': 'BND',
'玻利维亚诺 ': 'BOB',
'巴西雷亚尔 ': 'BRL',
'巴哈马元 ': 'BSD',
'Bitcoin ': 'BTC',
'不丹努尔特鲁姆 ': 'BTN',
'博茨瓦纳普拉 ': 'BWP',
'白俄罗斯卢布 ': 'BYN',
'白俄罗斯卢布 ': 'BYR',
'伯利兹元 ': 'BZD',
'加拿大元 ': 'CAD',
'刚果法郎 ': 'CDF',
'瑞士法郎 ': 'CHF',
'智利比索 ': 'CLP',
'中国人民币 ': 'CNY',
'哥伦比亚比索 ': 'COP',
'哥斯达黎加科朗 ': 'CRC',
'古巴可兑换比索 ': 'CUC',
'古巴比索 ': 'CUP',
'佛得角埃斯库多 ': 'CVE',
'捷克克朗 ': 'CZK',
'吉布提法郎 ': 'DJF',
'丹麦克朗 ': 'DKK',
'Dogecoin': 'OGE',
'多米尼加比索 ': 'DOP',
'Polkadot ': 'DOT',
'阿尔及利亚第纳尔 ': 'DZD',
'爱沙尼亚克朗 ': 'EEK',
'埃及镑 ': 'EGP',
'厄立特里亚纳克法 ': 'ERN',
'埃塞俄比亚比尔 ': 'ETB',
'Ethereum ': 'ETH',
'欧元 ': 'EUR',
'斐济元 ': 'FJD',
'福克兰群岛镑 ': 'FKP',
'英镑 ': 'GBP',
'格鲁吉亚拉里 ': 'GEL',
'根西岛镑 ': 'GGP',
'加纳塞地 ': 'GHS',
'直布罗陀镑 ': 'GIP',
'冈比亚达拉西 ': 'GMD',
'几内亚法郎 ': 'GNF',
'危地马拉格查尔 ': 'GTQ',
'圭亚那元 ': 'GYD',
'港币 ': 'HKD',
'洪都拉斯伦皮拉 ': 'HNL',
'克罗地亚库纳 ': 'HRK',
'海地古德 ': 'HTG',
'匈牙利福林 ': 'HUF',
'印度尼西亚卢比 ': 'IDR',
'以色列谢克尔 ': 'ILS',
'曼岛镑 ': 'IMP',
'印度卢比 ': 'INR',
'伊拉克第纳尔 ': 'IQD',
'伊朗里亚尔 ': 'IRR',
'冰岛克朗 ': 'ISK',
'泽西岛镑 ': 'JEP',
'牙买加元 ': 'JMD',
'约旦第纳尔 ': 'JOD',
'日元 ': 'JPY',
'肯尼亚先令 ': 'KES',
'吉尔吉斯斯坦索姆 ': 'KGS',
'柬埔寨瑞尔 ': 'KHR',
'科摩罗法郎 ': 'KMF',
'朝鲜元 ': 'KPW',
'韩元 ': 'KRW',
'科威特第纳尔 ': 'KWD',
'开曼元 ': 'KYD',
'哈萨克斯坦坚戈 ': 'KZT',
'老挝基普 ': 'LAK',
'黎巴嫩镑 ': 'LBP',
'Chainlink': 'INK',
'斯里兰卡卢比 ': 'LKR',
'利比里亚元 ': 'LRD',
'巴索托洛蒂 ': 'LSL',
'Litecoin ': 'LTC',
'立陶宛立特 ': 'LTL',
'Terra' : 'UNA',
'拉脱维亚拉特 ': 'LVL',
'利比亚第纳尔 ': 'LYD',
'摩洛哥迪拉姆 ': 'MAD',
'摩尔多瓦列伊 ': 'MDL',
'马尔加什阿里亚 ': 'MGA',
'马其顿第纳尔 ': 'MKD',
'缅元 ': 'MMK',
'蒙古图格里克 ': 'MNT',
'澳门元 ': 'MOP',
'毛里塔尼亚乌吉亚 ': 'MRU',
'毛里求斯卢比 ': 'MUR',
'马尔代夫拉菲亚 ': 'MVR',
'马拉维克瓦查 ': 'MWK',
'墨西哥比索 ': 'MXN',
'马来西亚林吉特 ': 'MYR',
'莫桑比克梅蒂卡尔 ': 'MZN',
'纳米比亚元 ': 'NAD',
'尼日利亚奈拉 ': 'NGN',
'尼加拉瓜科多巴 ': 'NIO',
'挪威克朗 ': 'NOK',
'尼泊尔卢比 ': 'NPR',
'新西兰元 ': 'NZD',
'阿曼里亚尔 ': 'OMR',
'巴拿马巴波亚 ': 'PAB',
'秘鲁索尔 ': 'PEN',
'巴布亚新几内亚基那 ': 'PGK',
'菲律宾比索 ': 'PHP',
'巴基斯坦卢比 ': 'PKR',
'波兰兹罗提 ': 'PLN',
'巴拉圭瓜拉尼 ': 'PYG',
'卡塔尔里亚尔 ': 'QAR',
'罗马尼亚新列伊 ': 'RON',
'塞尔维亚第纳尔 ': 'RSD',
'俄罗斯卢布 ': 'RUB',
'卢旺达法郎 ': 'RWF',
'沙特里亚尔 ': 'SAR',
'所罗门群岛元 ': 'SBD',
'塞舌尔卢比 ': 'SCR',
'苏丹镑 ': 'SDG',
'瑞典克朗 ': 'SEK',
'新加坡元 ': 'SGD',
'圣赫勒拿镑 ': 'SHP',
'塞拉利昂利昂 ': 'SLE',
'塞拉利昂利昂 ': 'SLL',
'索马里先令 ': 'SOS',
'塞波加大公国 Luigino ': 'SPL',
'苏里南元 ': 'SRD',
'圣多美多布拉 ': 'STN',
'萨尔瓦多科朗 ': 'SVC',
'叙利亚镑 ': 'SYP',
'斯威士兰里兰吉尼 ': 'SZL',
'泰铢 ': 'THB',
'塔吉克斯坦索莫尼 ': 'TJS',
'土库曼斯坦马纳特 ': 'TMT',
'突尼斯第纳尔 ': 'TND',
'汤加潘加 ': 'TOP',
'土耳其里拉 ': 'TRY',
'特立尼达元 ': 'TTD',
'图瓦卢元 ': 'TVD',
'新台币 ': 'TWD',
'坦桑尼亚先令 ': 'TZS',
'乌克兰格里夫纳 ': 'UAH',
'乌干达先令 ': 'UGX',
'Uniswap ': 'UNI',
'美元 ': 'USD',
'乌拉圭比索 ': 'UYU',
'乌兹别克斯坦索姆 ': 'VEF',
'委内瑞拉玻利瓦尔 ': 'VES',
'越南盾 ': 'VND',
'瓦努阿图瓦图 ': 'VUV',
'萨摩亚塔拉 ': 'WST',
'中非金融合作法郎 ': 'XAF',
'银（盎司） ': 'XAG',
'金（盎司） ': 'XAU',
'东加勒比元 ': 'XCD',
'国际货币基金组织特别提款权 ': 'XDR',
'Stellar Lumen ': 'XLM',
'CFA 法郎 ': 'XOF',
'钯（盎司） ': 'XPD',
'CFP 法郎 ': 'XPF',
'铂（盎司） ': 'XPT',
'Ripple ': 'XRP',
'也门里亚尔 ': 'YER',
'南非兰特 ': 'ZAR',
'赞比亚克瓦查 ': 'ZMK',
'赞比亚克瓦查 ': 'ZMW',
'津巴布韦元 ': 'ZWD',
'津巴布韦元 ': 'ZWL',
}



def print_red_text(text):
    print(Fore.RED + text + Style.RESET_ALL)

def print_green_text(text):
    print(Fore.GREEN + text + Style.RESET_ALL)

def print_yellow_text(text):
    print(Fore.YELLOW + text + Style.RESET_ALL)

def detect_language(text):
    """ 检测输入的是中文或者英文 """
    for char in text:
        if '\u4e00' <= char <= '\u9fff':
            return 'Zh'
    return 'En'

def fuzz_search(data):
    """ 模糊查询国家名称, 返回查询到的国家名称 """
    return process.extractOne(data, country_currency_map.keys())

error_msg = []

def conver_Country2Code(country_name, threshold=49):
    """ 通过模糊匹配转换国家对应的货币代码 """
    global error_msg

    best_match = fuzz_search(country_name)
    if best_match[1] >= 80:
        print(f"【Info】{country_name} -> {best_match[0]}({country_currency_map[best_match[0]]}), score:{best_match[1]}")
        error_msg.append(f" 【Info】{country_name} -> {best_match[0]}({country_currency_map[best_match[0]]})")
    elif best_match[1] >= threshold:
        print_yellow_text(f"【Warning】{country_name} -> {best_match[0]}({country_currency_map[best_match[0]]}), score:{best_match[1]}")
        error_msg.append(f" 【Warning】{country_name} -> {best_match[0]}({country_currency_map[best_match[0]]})")
    else:
        print_red_text(f"【Error】'{country_name}' Not Found! Pleas check the character")
        error_msg.append(f" 【Error】'{country_name}' Not Found! Pleas check the character")
        return None
    return country_currency_map[best_match[0]]

def validate_country_name_en(cur_code):
    """ 如果输入的是货币代码，检测代码是否长度是否是3位 """

    # if len(cur_code) != 3:
    #     return False
    # for country_code in country_currency_map.values():
    #     if cur_code == country_code:
    #         return True
    return len(cur_code) == 3

def get_priority(currency_order, x):
    try:
        return currency_order.index(x)
    except ValueError as e:
        return 9999

def get_currency_by_folder(remote_folder):
    """ 
    获取指定型号的货币XML文件
    :param remote_folder: 远程文件夹(UN60_XXX, UN200)
    """
    model_code = remote_folder.split("_")          # UN60、UN200、UN220
    model_currency_file = f"{model_code[0]}_currencys.xml"
    origin_cur_path = get_text("local_original_currencys_xml_path")
    currency_path = os.path.join(origin_cur_path, model_currency_file)
    return currency_path

def handle_special_map(input: str):
    """
    处理特殊映射关系，查询特殊关系映射文件。
    - 若有匹配的则返回特殊的映射关系。
    - 若没匹配到则返回None
    :param input: 输入的货币名称或货币代码
    """
    map_file = "./user_config.xml"
    map_tree = open_xml(map_file)

    for e in map_tree.iter("currency_map"):
        map_str = e.text
        if input in map_str:
            print("special map found: ", e.get('redirect')) 
            return e.get('redirect')
        
    return None

def filter_and_sort_countries(root, country_code):
    """
    Filter countries from XML and sort them according to specified order
    :param root: XML root element
    :param country_code: List of country codes in desired order
    :return: Tuple of (sorted country list, missing codes)
    """
    # Get all countries and filter those in country_code
    countries = root.findall('Country')
    filtered_countries = [c for c in countries if c.attrib['tag'] in country_code]
    
    # Sort filtered countries according to country_code order
    filtered_countries.sort(key=lambda x: get_priority(country_code, x.attrib['tag']))
    
    # Sort the denomination elements within each country by face value in descending order
    for country in filtered_countries:
        # Find all denomination elements (denom_1, denom_2, etc.)
        denominations = []
        non_denom_elements = []
        
        # Separate denomination elements from other elements
        for child in country:
            if child.tag.startswith('denom_'):
                denominations.append(child)
            else:
                non_denom_elements.append(child)
        
        if denominations:
            # Sort denominations by face value in descending order
            denominations.sort(key=lambda x: int(x.attrib['val']), reverse=True)
            
            # Store country attributes before clearing
            country_attribs = country.attrib.copy()
            
            # Remove all child elements from country
            country.clear()
            
            # Restore country attributes
            for key, value in country_attribs.items():
                country.set(key, value)
            
            # Re-add denomination elements with new sequential tags (denom_1, denom_2, etc.)
            for i, denom in enumerate(denominations, 1):
                denom.tag = f"denom_{i}"
                country.append(denom)
            
            # Re-add non-denomination elements at the end
            for elem in non_denom_elements:
                country.append(elem)
    
    # Find missing codes
    added_codes = {country.get('tag') for country in filtered_countries}
    missing_codes = set(country_code) - added_codes
    
    return filtered_countries, missing_codes

def select_country(input_str:str, remote_folder:str):
    """ Open selecttion according to  input country 
    :param input_str
    :param remote_folder: 选择的远端目录(UN60D、UN200_XXX), 获取对应的currency文件
    """
    
    """ 1. Get Input Country Name 
    Test Sample
    新加坡，马来西亚，文莱，柬埔寨，菲律宾
    新加坡、马来西亚、文莱、柬埔寨、菲律宾
    新加坡 马来西亚 文莱 柬埔寨 菲律宾
    新加坡, 马来西亚, 文莱, 柬埔寨, 菲律宾
    """
    # input_str = "新加、马来西、文莱、柬埔寨、菲律宾、USD PHP"
    # input_str = input("请输入需要开启的货币代码或国家名称：")
    global error_msg
    error_msg = []
    pattern = r'[,，\s、/|;；]+'
    # input_list = re.split(pattern, input_str)
    input_list = list(filter(None, re.split(pattern, input_str)))
    print(f"【Info】input list: {input_list}")

    country_code = ['AUT','MIX']
    for str in input_list:
        special_str = handle_special_map(str)
        if special_str != None:
            error_msg.append(f" 【Info】{str} -> {special_str}")
            str = special_str
        
        if detect_language(str) == 'En':
            if len(str) == 3:
                country_code.append(str.upper())
            else:
                print_red_text(f"【Error】Invalid value '{str}', the length of the character must be 3!")
                error_msg.append(f" 【Error】Invalid value '{str}', the length of the character must be 3!")
        elif detect_language(str) =='Zh':
            code = conver_Country2Code(str, threshold=49)
            code and country_code.append(code)
    print_green_text(f"【Info】country_code: {country_code}")

    """ 2. Process XML"""
    try:
        currency_path = get_currency_by_folder(remote_folder)
        print(f"Start to Process XML: {currency_path}")
        tree = ET.parse(currency_path)
        # 在这里可以继续处理已解析的XML数据
    except ET.ParseError as e:
        print(f"XML解析错误：{e}")
        input("按任意键退出...")
        exit()
    except IOError as e:
        print(f"文件读取错误：{e}")
        input("按任意键退出...")
        exit()
    root = tree.getroot()
    root_attrib = root.attrib
    # print(f"【info】type(root_attrib) = {type(root_attrib)}")
    """ 过滤币种 & 调整币种顺序 & 获取缺少的币种 """
    sorted_countries, missing_codes = filter_and_sort_countries(root, country_code)

    if missing_codes:
        print_red_text(f"【Error】以下币种在XML文件中不存在： {', '.join(missing_codes)}")
        error_msg.append(f" 【Error】The Follwing Codes are not in XML： {', '.join(missing_codes)}\r\n")
    # 创建新的根元素，并复制根元素的属性
    sorted_root = ET.Element(root.tag)
    for key, value in root_attrib.items():
        sorted_root.set(key, value) 

    # 将排序后的元素添加到新的根元素中
    for country in sorted_countries:
        sorted_root.append(country)

    # 创建新的ElementTree对象
    sorted_tree = ET.ElementTree(sorted_root)
    # 调整缩进
    ET.indent(sorted_tree, space="\t", level=0)

    """ 
    Set all <selecttion> tag's val to N 
    <Country tag="AUT">
    """
    # element.text = 'New text'
    for e in sorted_tree.iter("Country"):
        country_tag = e.get("tag")
        if country_tag in country_code:
            e.find("selecttion").set("val", "Y")
            print(f"Country:{e.get("tag")}")
        else:
            e.find("selecttion").set("val", "N")
        # print(f"attri:{e.attrib}, \ntext:{select.attrib}")

    if not os.path.exists('./new_currencys'):
        os.makedirs('./new_currencys')
    sorted_tree.write('./new_currencys/currencys.xml', encoding="utf-8", xml_declaration=True)

    """
    3. Special Handling for GL18 Scheme
       Check if the scheme is GL18, then check if local_main_rootfs_path has all currency folders
       
       Selected Currency Code: USD PKR
       
       Then check if the following folders exist:
        Ex.: ./WL_GL18_PackProj/rootfs/rootfs_20011b_main/USD
        Ex.: ./WL_GL18_PackProj/rootfs/rootfs_20011b_main/PKR
    """
    scheme = get_scheme(remote_folder)
    print(f"Start to check GL18 rootfs folders for {remote_folder}, scheme={scheme}")
    if (scheme == "GL18"):
        print_green_text("【Info】GL18 Scheme detected")
        main_rootfs_bin_path = get_text("local_main_rootfs_bin_path", scheme="GL18", config_tree="remote_config")
        if not os.path.exists(main_rootfs_bin_path):
            print_red_text(f"【Error】local_main_rootfs_bin_path:{main_rootfs_bin_path} not exists")
            error_msg.append(f" 【Error】local_main_rootfs_bin_path:{main_rootfs_bin_path} not exists")
        else:
            for code in country_code:
                if code in ['AUT','MIX']:
                    continue
                country_folder = f"{code.upper()}"
                country_folder_path = os.path.join(main_rootfs_bin_path, country_folder)
                if not os.path.exists(country_folder_path):
                    print_red_text(f"【Error】{code} Template not exists")
                    error_msg.append(f" 【Error】{code} Template not exists")
                else:
                    print_green_text(f"【Info】{code} Template exists")

    return country_code, error_msg

def __parse_country(country_elem):
    """
    从 <Country> 节点中提取所有 denom_xx 的 val 属性，
    以及内部 mag_sensitivity 的所有属性。
    返回一个按 denom_val 从大到小排序的列表。
    """
    results = []
    for child in country_elem:
        if child.tag.startswith("denom_") and "val" in child.attrib:
            denom_val = child.attrib["val"]
            mag_elem = child.findall("mag_sensitivity")

            print(f"denom_val: {denom_val}, mag_elem: {mag_elem}")
            # 提取 mag_sensitivity 的所有属性
            mag_info = [mag.attrib for mag in mag_elem] if mag_elem else []
            results.append({
                "denom_val": denom_val,
                "mag_sensitivity": mag_info
            })

    # 按 denom_val 从大到小排序
    results.sort(key=lambda x: int(x["denom_val"]), reverse=True)
    print(f"results: {results}")
    return results



def __init_a33_mag_para_elements(parent_element, origin_mag_para):
    """
    为指定的父元素创建默认的 mag_para 配置
    :param parent_element: 父元素，通常是 version 元素
    """
    # 完整的标准 mag_para 配置
    mag_para = [
        {'type': "BM",   'alg_en': "N", 'mag_thred': "210"},
        {'type': "LSM",  'alg_en': "N", 'mag_thred': "222"},
        {'type': "RSM",  'alg_en': "N", 'mag_thred': "223"},
        {'type': "LSM1", 'alg_en': "N", 'mag_thred': "224"},
        {'type': "RSM1", 'alg_en': "N", 'mag_thred': "213"},
        {'type': "LSM2", 'alg_en': "N", 'mag_thred': "254"},
        {'type': "RSM2", 'alg_en': "N", 'mag_thred': "244"},
        {'type': "HD",   'alg_en': "N", 'mag_thred': "111"}
    ]
    for para_config in mag_para:
        para_elem = ET.Element('para', attrib=para_config)
        
        if para_elem.get('type') == 'BM' and origin_mag_para:
            para_elem.set('alg_en', origin_mag_para['bm_en'])
            para_elem.set('mag_thred', origin_mag_para['bm_thred'])
        elif (para_elem.get('type') == 'LSM' or para_elem.get('type') == 'RSM') and origin_mag_para:
            para_elem.set('alg_en', origin_mag_para['sm_en'])
            # para_elem.set('mag_thred', origin_mag_para['sm_thred'])
            
        parent_element.append(para_elem)
    return parent_element

def __init_gl20multi_mag_para_elements(parent_element: ET.Element, origin_mag_para):
    """
    为指定的父元素创建 GL20MULTI 的 mag_para 配置
    :param parent_element: 父元素，通常是 version 元素
    """
    # 完整的标准 mag_para 配置
    # <para type="BM" alg_en="N" peak_level="3" peak_max="4" peak_min="0" l_range="60" r_range="113" location_en="N" />
    mag_para = [
        {'type': "BM",   'alg_en': "N", 'peak_level': "3", 'peak_max': "4", 'peak_min': "0", 'l_range': "0", 'r_range': "0", 'location_en': "N"},
        {'type': "LSM",  'alg_en': "N", 'peak_level': "3", 'peak_max': "4", 'peak_min': "0", 'l_range': "0", 'r_range': "0", 'location_en': "N"},
        {'type': "RSM",  'alg_en': "N", 'peak_level': "3", 'peak_max': "4", 'peak_min': "0", 'l_range': "0", 'r_range': "0", 'location_en': "N"},
        # {'type': "LSM1", 'alg_en': "N", 'peak_level': "3", 'peak_max': "4", 'peak_min': "0", 'l_range': "0", 'r_range': "0", 'location_en': "N"},
        # {'type': "RSM1", 'alg_en': "N", 'peak_level': "3", 'peak_max': "4", 'peak_min': "0", 'l_range': "0", 'r_range': "0", 'location_en': "N"},
        # {'type': "LSM2", 'alg_en': "N", 'peak_level': "3", 'peak_max': "4", 'peak_min': "0", 'l_range': "0", 'r_range': "0", 'location_en': "N"},
        # {'type': "RSM2", 'alg_en': "N", 'peak_level': "3", 'peak_max': "4", 'peak_min': "0", 'l_range': "0", 'r_range': "0", 'location_en': "N"},
        # {'type': "HD",   'alg_en': "N", 'peak_level': "3", 'peak_max': "4", 'peak_min': "0", 'l_range': "0", 'r_range': "0", 'location_en': "N"}
    ]
        
    for para_config in mag_para:
        para_elem = ET.Element('para', attrib=para_config)
        
        if para_elem.get('type') == 'BM' and origin_mag_para:
            para_elem.set('alg_en', origin_mag_para['bm_en'])
            para_elem.set('peak_level', origin_mag_para['bm_level'])
            para_elem.set('peak_max', origin_mag_para['bm_max'])
            para_elem.set('peak_min', origin_mag_para['bm_min'])
        elif (para_elem.get('type') == 'LSM' or para_elem.get('type') == 'RSM') and origin_mag_para:
            para_elem.set('alg_en', origin_mag_para['sm_en'])
            para_elem.set('peak_level', origin_mag_para['sm_level'])
            para_elem.set('peak_max', origin_mag_para['sm_max'])
            para_elem.set('peak_min', origin_mag_para['sm_min'])

        parent_element.append(para_elem)
    return parent_element


def check_mag_para(currency_code_list: list, remote_folder: str):
    """
    Check if mag_para.xml contains the correct tags for the currency codes in currency_code_list
    1. If a currency code from currency_code_list is not found in mag_para.xml:
        then add a new <currency tag="XXX">...</currency> section with denominations that match currencys.xml
        
    2. Resort the <currency tag="XXX">...</currency> sections in mag_para.xml according to the order in currency_code_list
    
    3. Resort the <denom val="xxx">...<denom val="xxx"> elements within each <currency> section
    
    4. Save the modified mag_para.xml
    """
    scheme = get_scheme(remote_folder)
    print(f"Start to check mag_para.xml for {remote_folder}, scheme={scheme}")
    
    if ( need_mag_para(remote_folder) == False ):
        print_yellow_text(f"【Warning】check_mag_para Unsupported scheme: {scheme}. Only A33 and GL20MULTI are supported in mag_para.xml.")
        return

    local_mag_xml_file_path = get_text("local_mag_xml_file_path", scheme=scheme, config_tree="remote_config")
    local_currencys_xml_path = get_text("local_currencys_xml_path")
    local_currencys_xml_file_path = get_text("local_currencys_xml_path") + "/currencys.xml"
    mag_xml_tree = open_xml(local_mag_xml_file_path)
    currencys_xml_tree = open_xml(local_currencys_xml_file_path)
    
    if mag_xml_tree is None or currencys_xml_tree is None:
        print_red_text("【Error】Failed to open mag_para.xml or currencys.xml")
        return
    
    mag_xml_root = mag_xml_tree.getroot()
    currencys_xml_root = currencys_xml_tree.getroot()
    
    # Step 1: Check and add missing currency sections
    existing_currency_tags = {currency.get('tag') for currency in mag_xml_root.findall('Country')}
    for code in currency_code_list:
        if code in ['AUT','MIX']:
            continue
        if code not in existing_currency_tags:
            # Find the corresponding country in currencys.xml
            country_elem = currencys_xml_root.find(f".//Country[@tag='{code}']")
            if country_elem is not None:
                # Create a new currency element
                new_currency_elem = ET.Element('Country', attrib={'tag': code})
                
                if scheme == "GL20MULTI":
                    # <sample mm_thred="70" lsm_thred="70" rsm_thred="70" lsm1_thred="70" rsm1_thred="70" lsm2_thred="70" rsm2_thred="70" HD_thred="70" />
                    sample_config = {'mm_thred': "70",   'lsm_thred': "70",  'rsm_thred': "70",  \
                                     'lsm1_thred': "70", 'rsm1_thred': "70", 'lsm2_thred': "70", \
                                     'rsm2_thred': "70", 'HD_thred': "70"}
                    new_currency_elem.append(ET.Element('sample', attrib=sample_config))

                # Add denomination elements
                for denom in __parse_country(country_elem):
                    new_denom_elem = ET.Element('denom', attrib={'val': denom["denom_val"]})
                    # print(f"denom: {denom['denom_val']}, mag_para: {denom['mag_sensitivity']}")
                    for mag_para in denom["mag_sensitivity"]:
                        # print(f"Adding mag_para for {code} denom {denom['denom_val']}: {mag_para}")
                        new_ver_elem = ET.Element('version', attrib={'val': mag_para["ver"]})
                        if ( scheme == "A33" ):
                            new_ver_elem = __init_a33_mag_para_elements(new_ver_elem, mag_para)
                        elif ( scheme == "GL20MULTI" ):
                            new_ver_elem = __init_gl20multi_mag_para_elements(new_ver_elem, mag_para)

                        #TODO: Set alg_en and mag_thred, according to mag_para attributes
                        new_denom_elem.append(new_ver_elem)
                    new_currency_elem.append(new_denom_elem)
                
                # Append the new currency element to mag_para.xml root
                mag_xml_root.append(new_currency_elem)
                print_green_text(f"【Info】Added missing currency section for {code}")
            else:
                print_red_text(f"【Error】Currency code {code} not found in currencys.xml")
    
    # Step 2: Resort currency sections in mag_para.xml
    mag_xml_root[:] = sorted(mag_xml_root, key=lambda x: get_priority(currency_code_list, x.get('tag')))
    
    # Step 3: Resort denomination elements within each currency section
    for currency in mag_xml_root.findall('Country'):
        if ( existing_currency_tags.__contains__(currency.get('tag')) == False ):
            continue
        
        denominations = [denom for denom in currency if denom.tag == 'denom']
        denominations.sort(key=lambda x: int(x.get('val')), reverse=True)
        
        # Clear existing denomination elements
        for denom in currency.findall('denom'):
            currency.remove(denom)
        
        # Re-add sorted denomination elements
        for denom in denominations:
            currency.append(denom)
    

    # save after adding missing sections
    new_mag_xml_path = os.path.join(os.path.dirname(local_currencys_xml_path), "mag_para.xml")
    ET.indent(mag_xml_tree, space="\t", level=0)
    
    mag_xml_tree.write(new_mag_xml_path, encoding="utf-8", xml_declaration=True)


def press_any_key_to_continue():
    print("按任意键继续, 按q键退出...")
    user_input = msvcrt.getch().decode()  # 获取用户按键的输入
    if user_input.lower() == 'q':
        exit()


if __name__ == "__main__":
    
    while True:
        init()
        # select_country("USD EUR KES BWP MGA", "UN60M")
        # check_A33_mag_para(['BWP'], "UN220")
        check_mag_para(['KES', 'USD', 'EUR'], "UN60D")

        press_any_key_to_continue()
        # input("Press Any Key")
        # # 监听键盘按键释放事件
        # keyboard.on_release(on_key_release)

        # print("按下任意键继续执行，按回车键退出程序...")
        # keyboard.wait()
        # key = keyboard.read_key()
        # # 取消注册的键盘事件
        # keyboard.unhook_all()
        # print("继续执行程序...")

""" Query an element """
# element = root.find('Country')
# print(element)

""" Modify an element """
# element = root.find('Country')
# element.set("tag", "xxx")
# element.text = "xxxx"

""" Add a new element """
# new_element = ET.Element('new_element')
# parent_element = root.find('parent_element')
# parent_element.append(new_element)

""" Recursion node"""
# for e in root.iter("Country"):

""" Save changes """
# tree.write('./currencys.xml')
