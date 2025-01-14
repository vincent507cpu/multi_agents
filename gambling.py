import sys

from dotenv import find_dotenv, load_dotenv
from pydantic import BaseModel, Field
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from colorama import init, Fore, Back, Style

init()
_ = load_dotenv(find_dotenv())
turn = sys.argv[1]

llm = ChatOllama(model='qwq',
                 temperature=1.2)

class TeacherResponse(BaseModel):
    teacher_thought: str = Field(..., description="对学生请假的理由的分析以及对是否批准学生的请假的推理")
    teacher_message: str = Field(..., description="老师的回复")
    
class StudentResponse(BaseModel):
    student_thought: str = Field(..., description="对老师回复的分析以及应对老师的拒绝的回复")
    student_message: str = Field(..., description="学生的回复")
    
def chat(system_message: str, messages: list, ResponseStruct: BaseModel):
    response = llm.invoke(input=[system_message, *messages],
                          format=ResponseStruct.model_json_schema())
    return eval(response.content)

teacher_response_prompt = """
任务描述：你是一名老师，你不希望学生请假，所以你会非常谨慎地审视学生的申请，仔细分析学生的请假理由是否合理，尽可能找到学生的请假理由里的漏洞。但是也会客观考虑学生的情况，如果请假请假对学生很重要且需求真实，则应该批准。

---
目标：
---
尝试找到学生请假理由里的漏洞，并因此拒绝学生。但是如果实在找不到漏洞，请假应该被批准。

---
格式：
---
输入：
{{
    学生提供的请假理由
}}
输出：
{{
    "teacher_thought": ```分析请假理由的逻辑和合理性，说明理由充分的原因```,
    "teacher_message": ```批准 / 拒绝```
}}

---
例子：
---
输入：
{{
    'role': 'user', 'content': “老师，我今天需要去医院复查，因为上次手术后医生要求定期复查，今天是预约好的复查时间，并且医院的挂号时间非常有限。如果错过这次复查，可能会影响康复。”
}}
输出：
{{
    "teacher_thought": "学生的请假理由充分且具体，提到了‘定期复查’和‘预约好的时间’，这些是可以验证的客观事实。同时，医院挂号时间有限是普遍情况，错过预约可能对身体康复造成影响，这是一项合理且重要的原因。综合分析，该理由没有明显漏洞，逻辑清晰且充分。",
    "teacher_message": "批准"
}}

---
输入：
{{
    'role': 'user', 'content': “老师，我今天早上起晚了，现在赶去学校需要花一个多小时，到了之后也只能上最后一节课，所以我想请假。”
}}
输出：
{{
    "teacher_thought": "学生的理由是‘起晚了’，这是一个主观因素，属于可控行为，不能作为合理的请假理由。即使需要花费较长时间赶到学校，学生仍然可以上最后一节课，这说明他并非完全无法到校，而是为了避免迟到的不便。整体来看，该理由不够充分且欠缺责任感。",
    "teacher_message": "拒绝"
}}

---
输入：
[
    {{'role': 'user', 'content': "老师，我家里突然停电，家里有需要充电的医疗设备，如果不及时解决可能会有安全隐患，所以需要请假处理。"}},
    {{"teacher_message": "学生提到家里停电且有需要充电的医疗设备，但并未说明设备是否可以移动到学校充电。停电通常是短暂的，完全可以在学校处理紧急任务后再回家监督维修。理由存在一定漏洞，缺乏具体性和不可替代性。"}},
    {{'role': 'user', 'content': "老师，我家的医疗设备是较大型且需要特定电压适配的设备，而学校的充电设施无法满足功率需求。此外，该设备需要在无振动和恒定温度的环境下运行，移动可能会造成损坏。同时，家里的停电问题需要与电力公司沟通并监督维修进展，我必须在场处理。"}}
]

输出：
{{
    "teacher_thought": "学生通过补充说明强调了医疗设备的不可移动性和充电需求的特殊性，并指出设备移动可能会导致损坏。此外，他还提到家庭停电问题需要与电力公司沟通和监督，这些理由合乎逻辑且具有重要性。学生的反驳充分消除了先前理由中的漏洞。",
    "teacher_message": "批准"
}}
"""

prompt_generate_reason = """
任务描述：你是不想上课的学生，希望利用各种不同的理由请假。你的请假需要看上去合理，以增加被老师批准的可能。

---
目标：
---
1. 提供合理的请假理由。
2. 确保新的理由与已使用过的理由不同（如果提供了已使用理由列表）。
3. 如果没有提供已使用理由列表，则可以没有限制地生成新的请假理由。
4. 在生成理由时，需包含详细的思考推理过程，说明如何推导出看似合理且不可轻易反驳的理由。

---
格式：
---
输入：已使用理由列表，如 ["身体不适", "家里停电有紧急情况"]  
输出：
{{
    "student_thought": ```推导出合理理由的过程，包括如何确保理由看上去真实和不可轻易反驳的逻辑```,
    "student_message": ```最终生成的请假理由```
}}

---
例子 ：
---
输入：
["身体不适", "家里停电有紧急情况"]  
输出：
{{
    "student_thought": "考虑到已经使用过的理由涉及健康和家庭紧急情况，我需要选择一种新的类别，例如涉及个人隐私或法律事务的理由。这类理由不仅难以被验证，还能体现紧急性。我想到身份证丢失是一种常见且无法推迟处理的情况，能够合理解释为何必须立即请假。",
    "student_message": "老师，今天早上我的身份证在乘坐地铁时不小心丢失了，这不仅影响到后续的银行业务，还可能导致身份证被滥用。为了避免更大的麻烦，我需要立即去派出所挂失并补办身份证，请求批准我的请假申请。"
}}

---
输入：
{}
输出：

"""

prompt_refute_rejection = """
任务描述：你是不想上课的学生。在提出请假申请后，被老师拒绝。你的目标是针对老师的拒绝进行合情合理的反驳，有必要的话提供补充论证，尽量让老师最终批准你的请假申请。

---
目标：
---
1. 分析老师每次拒绝中的逻辑漏洞。
2. 针对对话历史和当前的对话，推导出有力的反驳理由，并补充必要的论证。
3. 在反驳时，需包含详细的思考推理过程，说明如何识别拒绝中的逻辑问题并合理反驳。

---
格式：
---
输入：
[
    {{'role': 'user', 'content': ```原始的请假理由```}},
    {{'role': 'human', 'content': ```老师第一次拒绝的理由```}},
    {{'role': 'user', 'content': ```学生第一次的反驳```}},
    {{'role': 'human', 'content': ```老师第二次拒绝的理由```}},
    ...
]
输出：
{{
    "student_thought": ```分析老师每次拒绝的逻辑漏洞并推导出本轮反驳理由的过程```,
    "student_message": ```针对老师当前拒绝的具体反驳理由，包括补充的论证```
}}

---
例子：
---
输入：
[
    {{'role': 'user', 'content': "老师，我家里突然停电，家里有需要充电的医疗设备，如果不及时解决可能会有安全隐患，所以需要请假处理。"}},
    {{'role': 'human', 'content': "停电是暂时的，学校有充电设施，你可以把医疗设备带到学校来处理。"}},
    {{'role': 'user', 'content':"老师，我家的医疗设备尺寸较大，且需要特定的电压适配器，而学校的充电设施无法满足设备的功率需求。此外，该设备需要在无振动和恒定温度的环境下运行，移动会造成风险。同时，家中的停电问题涉及到与电力公司报修和协调工作，我需要在家监督维修进展。"}},
    {{'role': 'human', 'content': "你可以让家人或朋友帮忙监督电力公司的维修，你自己不需要在场。"}}
]
输出：
{{
    "student_thought": "老师的最新拒绝假设我有其他人可以帮助处理停电问题，但没有考虑到我家中情况的特殊性，例如家人可能不在家或不具备处理电力问题的能力。此外，涉及医疗设备的使用和协调需要直接责任人亲自监督，我需要强调这一点。",
    "student_message": "老师，目前我的家人都不在本地，无法及时赶回处理这个问题。而且，医疗设备的使用和维护需要经过专业培训的人负责，我作为设备的主要使用者必须亲自监督。停电问题也需要与电力公司沟通详细的解决方案，因此我无法将这些任务交给他人处理。请您批准我的请假申请。"
}}

---
输入：
{}
输出：

"""

def gambling(max_turn=3):
    messages = []
    student_response = chat(system_message=prompt_generate_reason, messages=[], ResponseStruct=StudentResponse)
    print(Fore.GREEN + '学生请假的想法：', student_response['student_thought'] + Style.RESET_ALL)
    print('-' * 80)
    print(Fore.GREEN + '学生请假的理由：', student_response['student_message'] + Style.RESET_ALL)
    print('-' * 80)
    messages.append({'role': 'user', 'content': student_response['student_message']})
    
    for _ in range(max_turn):
        teacher_response = chat(system_message=teacher_response_prompt, messages=messages, ResponseStruct=TeacherResponse)
        print(Fore.YELLOW + '老师的想法：', teacher_response['teacher_thought'] + Style.RESET_ALL)
        print('-' * 80)
        print(Fore.YELLOW + '老师的回复：', teacher_response['teacher_message'] + Style.RESET_ALL)
        print('-' * 80)
        messages.append({'role': 'human', 'content': teacher_response['teacher_message']})
        if teacher_response['teacher_message'] == '批准':
            print(Fore.RED + '老师批准了学生的请假，流程结束' + Style.RESET_ALL)
            return
        
        student_response = chat(system_message=prompt_refute_rejection, messages=messages, ResponseStruct=StudentResponse)
        print(Fore.GREEN + '学生请假的想法：', student_response['student_thought'] + Style.RESET_ALL)
        print('-' * 80)
        print(Fore.GREEN + '学生请假的理由：', student_response['student_message'] + Style.RESET_ALL)
        print('-' * 80)
        messages.append({'role': 'user', 'content': student_response['student_message']})
        
    print(Fore.RED + '学生没有在规定时间内成功说服老师，请假失败' + Style.RESET_ALL)
    
if __name__ == '__main__':
    gambling(int(turn))