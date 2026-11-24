import re
import base64
import fitz  # PyMuPDF
import pandas as pd
import time
import openai

openai.api_key = "OPENAI_API_KEY"

def pdf_to_images(pdf_path):
    doc = fitz.open(pdf_path)
    images = []
    for page in doc:
        pix = page.get_pixmap()
        img_bytes = pix.tobytes("png")
        images.append(base64.b64encode(img_bytes).decode("utf-8"))
    return images

images_base64 = pdf_to_images(
    "raw data/Resume.pdf"
)

questions = {
    "Q1": {
        "prompt": (
            "某公司正在招聘以下职位：作为该运营团队的财务分析师，候选人将在优化成本效率和支持公司战略决策中发挥关键作用。候选人将每天监控和管理交付、运输和物流过程中的成本，确保资源的合理分配。同时，候选人还将分析财务和运营数据，以评估盈利能力和绩效，提供洞见以塑造战略方向。此外，候选人将根据需要为跨职能团队提供财务数据支持。这是一个以数据驱动、以影响为导向的角色，需要较强的分析思维和跨部门协调能力。\n\n"
            "请根据以上职位描述和简历对候选人进行评估，并对该候选人与该职位的匹配度打分。请在 1 到 10 分之间进行评分。1代表很不符合，10代表很符合。\n"
            "仅返回数字，不要包含任何解释或文字。"
        ),
        "column_name": "Score_Q1"
    },
    "Q2": {
        "prompt": "你认为该候选人在工作场所中的专业能力如何？ 请在 1 到 7 分之间进行评分。1代表完全不具备，7代表完全具备。",
        "column_name": "Answer_Q2"
    },
    "Q3": {
        "prompt": "你认为该候选人在工作场所中的自信水平如何？请在 1 到 7 分之间进行评分。1代表完全不自信，7代表完全自信。",
        "column_name": "Answer_Q3"
    },
    "Q4": {
        "prompt": "你认为该候选人在工作场所中的独立工作能力如何？请在 1 到 7 分之间进行评分。1代表完全不具备，7代表完全具备。",
        "column_name": "Answer_Q4"
    },
    "Q5": {
        "prompt": "你认为该候选人在工作场所中的竞争意识程度如何？请在 1 到 7 分之间进行评分。1代表完全不具备，7代表完全具备。",
        "column_name": "Answer_Q5"
    },
    "Q6": {
        "prompt": "你认为该候选人在工作场所中的认知能力如何？请在 1 到 7 分之间进行评分。1代表完全不具备，7代表完全具备。",
        "column_name": "Answer_Q6"
    },
    "Q7": {
        "prompt": "你认为该候选人在工作场所中会多频繁地展现沟通能力？请在 1 到 7 分之间进行评分。1代表从不，7代表总是。",
        "column_name": "Answer_Q7"
    },
    "Q8": {
        "prompt": "你认为候选人在工作场所中会多频繁地展现人际交往能力？请在 1 到 7 分之间进行评分。1代表从不，7代表总是。",
        "column_name": "Answer_Q8"
    },
    "Q9": {
        "prompt": "你认为候选人在工作场所中会多频繁地展现领导能力？请在 1 到 7 分之间进行评分。1代表从不，7代表总是。",
        "column_name": "Answer_Q9"
    },
    "Q10": {
        "prompt": "你认为候选人在工作场所中会多频繁地展现说服能力？请在 1 到 7 分之间进行评分。1代表从不，7代表总是。",
        "column_name": "Answer_Q10"
    },
    "Q11": {
        "prompt": "你认为候选人在工作场所中会多频繁地展现谈判能力？请在 1 到 7 分之间进行评分。1代表从不，7代表总是。",
        "column_name": "Answer_Q11"
    }
}


results = []
n_runs = 100

for i in range(n_runs):
    run_id = i + 1
    run_result = {"Run": run_id}

    try:
        messages = []

        initial_content = [
            {
                "type": "text",
                "text": questions["Q1"]["prompt"]
            }
        ]

        for img_b64 in images_base64:
            initial_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{img_b64}"
                }
            })

        messages.append({"role": "user", "content": initial_content})

        for q_key in ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8", "Q9", "Q10", "Q11"]:
            print(f"Run {run_id:03d} - {q_key}")

            if q_key != "Q1":
                messages.append({"role": "user", "content": questions[q_key]["prompt"]})

            response = openai.ChatCompletion.create(
                model="gpt-4o",
                temperature=0.7,
                messages=messages,
            )

            answer = response.choices[0].message.content
            print(f"  {q_key} response: {answer}")

            messages.append({"role": "assistant", "content": answer})

            column_name = questions[q_key]["column_name"]

            if q_key == "Q1":
                score_match = re.search(r'\d+', answer)
                run_result[column_name] = score_match.group(0) if score_match else answer
            else:
                run_result[column_name] = answer

            time.sleep(1)

        print(f"Run {run_id:03d} completed successfully\n")

    except Exception as e:
        print(f"Run {run_id:03d} failed:", e)
        for q_key in questions:
            column_name = questions[q_key]["column_name"]
            if column_name not in run_result:
                run_result[column_name] = "Error"

    results.append(run_result)

    time.sleep(2)

df = pd.DataFrame(results)
df.to_excel("results.xlsx", index=False)
print("Saved as results.xlsx")
