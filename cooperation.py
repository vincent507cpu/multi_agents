# 加载环境变量
import json
import os
import sys
import random
from datetime import datetime, timedelta, timezone

import openai
import requests
from colorama import Back, Fore, Style, init
from dotenv import find_dotenv, load_dotenv

init()

_ = load_dotenv(find_dotenv())
amap_key = os.getenv('GAODE_MAP_API_KEY')
zhipu_api_key = os.getenv('ZHIPU_API_KEY')

def instruct(system_prompt, instruction):
    client = openai.OpenAI(
        api_key=zhipu_api_key,
        base_url='https://open.bigmodel.cn/api/paas/v4'
    )
    if system_prompt:
        response = client.chat.completions.create(
            model='glm-4-plus',
            messages=[
                {'role': 'system', 'content': system_prompt},
                {"role": "user", "content": instruction},
            ],
            temperature=0.9,
            max_tokens=1024,
        )
    else:
        response = client.chat.completions.create(
            model='glm-4-plus',
            messages=[
                {"role": "user", "content": instruction},
            ],
            temperature=0.9,
            max_tokens=1024,
        )
    return response.choices[0].message.content

def get_city_loc():
    url = "http://httpbin.org/ip" # 也可以直接在浏览器访问这个地址
    res = requests.get(url)
    ip = json.loads(res.text)["origin"] # 取其中某个字段的值
    
    # 其中fields字段为定义接受返回参数，可不传；lang为设置语言，zh-CN为中文，可以传
    url = f'http://ip-api.com/json/{ip}?fields=status,country,regionName,city&lang=zh-CN'
    res = requests.get(url)
    data = json.loads(res.text)
    
    loc = data['regionName'] + data['city']
    print(Fore.GREEN + f"- 当前城市：{loc}" + Style.RESET_ALL)
    
    return loc

# def get_beijing_hour():
def get_food():
    # breakfast, lunch, supper = False, False, False
    # food = False
    
    # 创建一个UTC+8的时区对象
    beijing_tz = timezone(timedelta(hours=8))
    
    # 获取当前的UTC时间并转换为北京时间
    beijing_time = datetime.now(tz=beijing_tz)
    
    # 格式化小时为字符串
    hour = int(beijing_time.strftime("%H"))
    
    if hour in [6, 7, 8, 11, 12, 13, 16, 17, 18]:
        res = input(Fore.YELLOW + f"- 现在是吃饭的时间，要吃饭吗？" + Style.RESET_ALL)
        if res in ['y', 'yes', '是']:
            return True
        else:
            return False
            
    # return food
    # if hour in [6, 7, 8]:
    #     res = input(Fore.GREEN + f" - 现在是吃早饭的时间，要吃饭吗？" + Style.RESET_ALL)
    #     if res in ['y', 'yes', '是']:
    #         breakfast = True
    # if hour in [11, 12, 13]:
    #     res = input(Fore.GREEN + f" - 现在是吃午餐的时间，要吃饭吗？" + Style.RESET_ALL)
    #     if res in ['y', 'yes', '是']:
    #         lunch = True
    # if hour in [16, 17, 18]:
    #     res = input(Fore.GREEN + f" - 现在是吃晚饭的时间，要吃饭吗？" + Style.RESET_ALL)
    #     if res in ['y', 'yes', '是']:
    #         supper = True
    
    # return breakfast, lunch, supper

def get_geocodes(current_location, city):
    '''
    获取高德地图上的经纬度
    '''
    while True:
        url = f"https://restapi.amap.com/v3/geocode/geo?key={amap_key}&address={current_location}&city={city}&output=json"
        res = requests.get(url)
        data = res.json()
        
        if 'geocodes' in data:
            return data["geocodes"][0]["location"]
        else:
            current_location = input(Fore.RED + Back.LIGHTBLUE_EX + "没有查到这个地方，输入一个不同地点试一下吧：" + Style.RESET_ALL)
            continue
    
def is_residency(current_location):
    '''
    判断是否是住宅
    '''
    instruction = f"判断 '{current_location}' 是否是住宅小区的名称，是的话输出 `是`，不是的话输出 `不是`。只输出你的结论。"
    print(Fore.GREEN + f"在判断 {current_location} 是否是住宅小区的名称：" + Style.RESET_ALL)
    
    res = instruct('', instruction)
    if res == '是':
        print(Fore.GREEN + f"- {current_location} 是住宅小区" + Style.RESET_ALL)
        return True
    else:
        print(Fore.GREEN + f"- {current_location} 不是住宅小区" + Style.RESET_ALL)
        return False

def recommand_activity(city, location):
    action_recommandation_instruction = '''
    当前地点：{city} {location}

    你需要随机生成 10 组数据字符串，字符串的第一个值为人类日常行为（如跳舞、钓鱼、写日记等日常常见行为），字符串的第二个值为日前可以合理完成该行为的一个地点（像舞蹈教室、河边、家等）。此外，如果 {location} 是住宅小区的名字，则意味着现在在家，10 条输出中需要有一半数据是在家里的活动，例如：```看电视 家```、```看书 家``` 等，如果不是则不要有在家做的活动。确保行为多样化且具有日常性，地点与行为相匹配，精准对应人们通常会去做这件事的实际场所。不要出现外卖。同一组中的两个值使用空格分隔，不同组之间使用逗号分隔，示例如下：
    ```跳舞 舞蹈教室,看电视 家,...```
    '''.strip ()
    
    recommendated_actions = instruct('', action_recommandation_instruction.format(city=city, location=location)).replace('`', '')
    recommendated_actions = [pair.split() for pair in recommendated_actions.split(',')]
    return recommendated_actions

def choose_activity(recommendated_actions):
    def get_single_sentence(action, place):
        if place == '家':
            return f'在{place}{action}'
        else:
            return f'去{place}{action}'
    for i, (action, place) in enumerate(recommendated_actions):
        print(f'{i+1}\t{get_single_sentence(action, place)}')
        
    choose = input(Fore.YELLOW + '请输入选择的序号（或故意输入非法字符进入手动选择）：' + Style.RESET_ALL)
    
    try:
        return recommendated_actions[int(choose)-1]
    except:
        print(Fore.RED + '输入错误，随机选择一个' + Style.RESET_ALL)
        num = random.randint(0, len(recommendated_actions)-1)
        return recommendated_actions[num]
    
def get_destination(attraction, coord, city):
    loc = f'https://restapi.amap.com/v3/assistant/inputtips?key={amap_key}&keywords={attraction}&types=050301&location={coord}&city={city}&datatype=all'
    res = requests.get(loc).json()
    
    if 'tips' in res:
        return [(r['name'], r['location'], r['address']) for r in res['tips'] if r['location']]
    else:
        return []
    
def get_route(origin, destination):
    walk = f'https://restapi.amap.com/v3/direction/walking?key={amap_key}&origin={origin}&destination={destination}'
    routes = requests.get(walk).json()
    
    return (routes['route']['paths'][0]['distance'], 
            '，'.join([r['instruction'] for r in routes['route']['paths'][0]['steps']]))
    
if __name__ == '__main__':
    city = get_city_loc()
    # get_food = get_food()
    current_location = input(Fore.YELLOW + "- 请输入你的当前位置：" + Style.RESET_ALL)
    current_geocode = get_geocodes(current_location, city)
    # print(current_geocode)
    # print(is_residency(current_location))
    recommendated_actions = recommand_activity(city, current_location)
    action, place = choose_activity(recommendated_actions)
    
    if place == '家':
        print(Fore.GREEN + f"- 你选择接下来在家{action}，享受一段美好时光吧！" + Style.RESET_ALL)
        sys.exit(0)
        
    destinations = get_destination(place, current_geocode, city)
    
    print(Fore.GREEN + f"- {place} 的地点有：" + Style.RESET_ALL)
    for i, (name, _, address) in enumerate(destinations):
        print(f'{i+1}\t{name}，{address}')
    index = input(Fore.YELLOW + '请输入选择的序号：' + Style.RESET_ALL)
    while True:
        try:
            selected_destination = destinations[int(index)-1]
            break
        except:
            index = input(Fore.RED + '输入错误，请重新输入序号：' + Style.RESET_ALL)
            
    distance, route = get_route(current_geocode, selected_destination[1])
    print(Fore.GREEN + f"- 你选择接下来{action}：\n从{current_location}到{selected_destination[0]}的距离是：{distance} 米\n路线是：{route}" + Style.RESET_ALL)
    