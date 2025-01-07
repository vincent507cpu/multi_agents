# 加载环境变量
import os
import requests
import json
from datetime import datetime, timedelta, timezone

import openai
from colorama import init, Fore, Back, Style
# from crewai import Agent, Task, Crew, LLM, Flow
# from crewai.tools import tool
# from crewai.flow.flow import listen, start, and_, or_, router
# from pydantic import BaseModel, Field
init()  # 初始化colorama，确保在不同平台都能正常使用颜色

from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())
amap_key = os.getenv('GAODE_MAP_API_KEY')
zhipu_api_key = os.getenv('ZHIPU_API_KEY')

def instruct(instruction):
    client = openai.OpenAI(
        api_key=zhipu_api_key,
        base_url='https://open.bigmodel.cn/api/paas/v4'
    )
    response = client.chat.completions.create(
        model='glm-4-plus',
        messages=[
            {"role": "user", "content": instruction},
        ],
        temperature=0.9,
        max_tokens=1024,
    )
    return response.choices[0].message.content

# class RecommandActivity(BaseModel):
#     activity: str = Field(..., description='活动名称')
#     location: str = Field(..., description='活动地点')

def get_city_loc():
    url = "http://httpbin.org/ip" # 也可以直接在浏览器访问这个地址
    res = requests.get(url)
    ip = json.loads(res.text)["origin"] # 取其中某个字段的值
    
    # 其中fields字段为定义接受返回参数，可不传；lang为设置语言，zh-CN为中文，可以传
    url = f'http://ip-api.com/json/{ip}?fields=status,country,regionName,city&lang=zh-CN'
    res = requests.get(url)
    data = json.loads(res.text)
    
    loc = data['regionName'] + data['city']
    print(Fore.GREEN + f"当前城市：{loc}" + Style.RESET_ALL)
    
    return loc

def get_beijing_hour():
    breakfast, lunch, supper = False, False, False
    
    # 创建一个UTC+8的时区对象
    beijing_tz = timezone(timedelta(hours=8))
    
    # 获取当前的UTC时间并转换为北京时间
    beijing_time = datetime.now(tz=beijing_tz)
    
    # 格式化小时为字符串
    hour = int(beijing_time.strftime("%H"))
    
    if hour in [6, 7, 8]:
        res = input(Fore.GREEN + f" - 现在是吃早饭的时间，要吃饭吗？" + Style.RESET_ALL)
        if res in ['y', 'yes', '是']:
            breakfast = True
    if hour in [11, 12, 13]:
        res = input(Fore.GREEN + f" - 现在是吃午餐的时间，要吃饭吗？" + Style.RESET_ALL)
        if res in ['y', 'yes', '是']:
            lunch = True
    if hour in [16, 17, 18]:
        res = input(Fore.GREEN + f" - 现在是吃晚饭的时间，要吃饭吗？" + Style.RESET_ALL)
        if res in ['y', 'yes', '是']:
            supper = True
    
    return breakfast, lunch, supper

def get_geocodes(city):
    current_location = input(Fore.GREEN + " - 请输入你的当前位置：" + Style.RESET_ALL)
    '''
    获取高德地图上的经纬度'''
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
    print(f"在判断 {current_location} 是否是住宅小区的名称。")
    
    res = instruct(instruction)
    if res == '是':
        print(Fore.YELLOW + f" - {current_location} 是住宅小区" + Style.RESET_ALL)
        return True
    else:
        print(Fore.YELLOW + f" - {current_location} 不是住宅小区" + Style.RESET_ALL)
        return False

friend = Agent(
    role='用户的好朋友',
    goal='热心地为用户提供各种建议',
    backstory='作为用户最好的朋友，你总是热心地帮助用户，解决他的各种问题。现在，用户觉得很无聊，希望可以顺便做一些事情打发时间。他现在在 {location}，现在请你根据他的情况和需求，提供一些建议。',
    llm=llm,
    allow_delegation=False
)

recomand_activity = Task(
    description='现在，用户觉得很无聊，希望可以随便做一些事情打发时间。他现在在{location}，现在请你根据他的地点，提供一些可以在附近完成的活动（如跳舞、钓鱼、写日记等日常常见行为），并指出可以合理完成该行为的一个地点（像舞蹈教室、河边、家等）。',
    expected_output='10 个不同建议',
    agent=friend
)

crew = Crew(
    agents=[friend],
    tasks=[recomand_activity],
    verbose=True
)

if __name__ == '__main__':
    city = get_city_loc()
    current_time = get_beijing_hour()
    current_location = input(Back.YELLOW + "请输入你的当前位置：" + Style.RESET_ALL)
    current_geocode = get_geocodes(current_location, city)
    print(current_geocode)
    crew.kickoff({'location': current_location})