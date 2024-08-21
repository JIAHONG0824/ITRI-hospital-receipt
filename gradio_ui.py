import openai
import gradio as gr
import base64
import requests


def openai_api(prompt, key):
    openai.api_key = key
    completion = openai.chat.completions.create(
        model="gpt-4o", messages=[{"role": "user", "content": prompt}]
    )
    return completion.choices[0].message.content


# Function to encode the image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def get_image_content(base64_image, api_key):
    api_url = "https://api.openai.com/v1/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """
                        扮演影像識別專家，幫我把所有的細節都識別出來。
                        請找出醫院的名字，患者姓名，以及收費時間和列印時間。
                        """,
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                    },
                ],
            }
        ],
    }

    try:
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()  # 如果發生HTTP錯誤，則會引發HTTPError異常
        image_content = response.json()["choices"][0]["message"]["content"]
        return image_content
    except Exception as err:
        print(f"Other error occurred: {err}")
        return get_image_content(base64_image)


def image_recognition(image, api_key):
    base64_image = encode_image(image)
    image_content = get_image_content(base64_image, api_key)
    prompt = (
        """
        扮演文字處理專家，幫我把逐字稿整理成格式：\
        原則2：輸出格式(但不用出現本句)：$hospital:| 醫院名字 $name:| 患者姓名 $time:| 收費時間及列印時間 $none:| none\
        原則3：Let's work this out in a step-by-step way to be sure we have the right answer.\
        原則4：以繁體中文來命題。逐字稿： 
        """
        + image_content
    )
    result = openai_api(prompt, api_key)
    print(result)
    qname = result.split("$hospital:|")[1].split("$name:|")[0].strip()
    qfee = result.split("$name:|")[1].split("$time:|")[0].strip()
    qdate = result.split("$time:|")[1].split("$none:|")[0].strip()

    return qname, qfee, qdate


with gr.Blocks() as demo:
    gr.Markdown("醫院收據")
    with gr.Tab("請依順序操作"):
        with gr.Row():
            file_input = gr.File(label="第一步：請上傳檔案")
            api_key_input = gr.Textbox(
                label="第二步：請輸入OpenAI API金鑰", placeholder="OpenAI API Key"
            )
            submit_button = gr.Button("第三步：開始識別")
        with gr.Row():
            qname = gr.Textbox(label="醫院名字", value="")
            qfee = gr.Textbox(label="患者名稱", value="")
            qdate = gr.Textbox(label="時間", value="")

    submit_button.click(
        image_recognition,
        inputs=[file_input, api_key_input],
        outputs=[qname, qfee, qdate],
    )
