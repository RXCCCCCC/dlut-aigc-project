# 导入所有依赖库
from flask import Response  # 用于自定义HTTP响应（如流式返回大文件）
import requests  # 用于后端代理请求外部资源
from flask import Flask, request, jsonify  # Flask核心功能
from flask_cors import CORS  # 解决跨域问题
import os  # 读取环境变量
import json  # 处理JSON数据，腾讯云SDK需要
import time  # 用于轮询等待
from tencentcloud.common import credential  # 腾讯云鉴权
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException  # 腾讯云SDK异常
from tencentcloud.hunyuan.v20230901 import hunyuan_client, models  # 旧版混元接口（暂未用到）
from dotenv import load_dotenv  # 加载.env环境变量
from tencentcloud.ai3d.v20250513 import ai3d_client, models  # 新版3D生成接口

# 加载.env文件中的环境变量
load_dotenv()
# 初始化Flask应用
app = Flask(__name__)
# 启用CORS，允许前端跨域访问
CORS(app)

# 读取腾讯云API密钥（从环境变量中获取）
TENCENT_SECRET_ID = os.getenv("TENCENT_SECRET_ID")
TENCENT_SECRET_KEY = os.getenv("TENCENT_SECRET_KEY")

# 生成3D模型的核心函数，集成了任务提交和轮询查询
def generate_3d_model_with_hunyuan(prompt):
    """
    调用腾讯云混元3D生成API，提交任务并轮询查询结果，返回模型和预览图URL。
    :param prompt: 用户输入的文本描述
    :return: dict，包含modelUrl和previewImageUrl，或None（失败）
    """
    print(f"正在准备调用混元AI，指令: {prompt}")
    try:
        # 1. 创建腾讯云鉴权对象
        cred = credential.Credential(TENCENT_SECRET_ID, TENCENT_SECRET_KEY)
        # 2. 创建3D生成客户端
        client = ai3d_client.Ai3dClient(cred, "ap-guangzhou")
        # 3. 构造提交任务的请求
        req_submit = models.SubmitHunyuanTo3DJobRequest()
        params_submit = {"Prompt": prompt, "ResultFormat": "GLB"}
        req_submit.from_json_string(json.dumps(params_submit))
        # 4. 提交生成任务
        resp_submit = client.SubmitHunyuanTo3DJob(req_submit)
        submit_result = json.loads(resp_submit.to_json_string())
        job_id = submit_result.get("JobId")

        if not job_id:
            print(f"错误：提交任务后未能获取到JobId。收到的响应: {submit_result}")
            return None

        print(f"成功提交任务，获得 JobId: {job_id}。现在开始轮询查询结果...")

        # 5. 轮询查询任务状态，最多重试30次，每次间隔10秒
        max_retries = 30
        retry_count = 0

        while retry_count < max_retries:
            print(f"等待10秒后查询任务状态... (尝试次数: {retry_count + 1})")
            time.sleep(10)

            req_query = models.QueryHunyuanTo3DJobRequest()
            params_query = {"JobId": job_id}
            req_query.from_json_string(json.dumps(params_query))
            resp_query = client.QueryHunyuanTo3DJob(req_query)
            query_result = json.loads(resp_query.to_json_string())

            print("查询任务状态返回的完整JSON响应：")
            print(json.dumps(query_result, indent=4, ensure_ascii=False))
            # 直接从最外层获取任务状态
            job_status = query_result.get("Status")
            
            print(f"当前任务状态: {job_status}")
            
            if job_status == "DONE":
                # 任务完成，获取模型和预览图URL
                result_files = query_result.get("ResultFile3Ds", [])
                model_url = None
                preview_image_url = None
                if result_files:
                    model_url = result_files[0].get("Url")
                    preview_image_url = result_files[0].get("PreviewImageUrl")
                print(f"任务成功完成！模型URL: {model_url}, 预览图URL: {preview_image_url}")
                return {
                    "modelUrl": model_url,
                    "previewImageUrl": preview_image_url
                }
            elif job_status == "FAILED":
                # 任务失败，打印错误信息
                error_message = query_result.get('ErrorMessage', '未知错误')
                print(f"任务生成失败！原因: {error_message}")
                return None
            
            retry_count += 1

        print("任务查询超时，请稍后前往腾讯云控制台查看结果。")
        return None

    except TencentCloudSDKException as err:
        print(f"调用混元API时发生SDK错误: {err}")
        return None
    except Exception as e:
        print(f"发生未知错误: {e}")
        return None

# 处理前端生成请求的API路由
@app.route('/api/generate', methods=['POST'])
def handle_generation_request():
    """
    接收前端的文本和图片，整合为prompt，调用3D生成函数，返回模型和预览图URL。
    """
    print("接收到新的生成请求！")
    text_input = request.form.get('text')
    image_file = request.files.get('image')
    # audio_file = request.files.get('audio') # 暂不处理语音

    if not text_input and not image_file:
        return jsonify({"status": "error", "message": "请输入文本或上传图片。"}), 400

    # 整合prompt（如有图片可扩展为多模态）
    final_prompt = text_input or "一座美丽的城堡"
    if image_file:
        # 未来可用图片理解模型丰富prompt
        image_description = f"请参考上传的图片'{image_file.filename}'的风格和内容。"
        final_prompt += f" {image_description}"
    
    print("最终整合的指令(Prompt):", final_prompt)

    # 调用核心生成函数
    result_data = generate_3d_model_with_hunyuan(final_prompt)
    if result_data and result_data.get("modelUrl"):
        # 成功，返回模型和预览图URL
        return jsonify({
            "status": "success",
            "message": "模型生成成功！",
            "modelUrl": result_data.get("modelUrl"),
            "previewImageUrl": result_data.get("previewImageUrl")
        })
    else:
        # 失败，返回错误
        return jsonify({
            "status": "error",
            "message": "模型生成失败，请查看后端控制台日志获取详细信息。"
        }), 500

# 3D模型文件代理API，解决前端跨域和临时URL失效问题
@app.route('/api/model-proxy')
def model_proxy():
    """
    代理腾讯云模型文件URL，前端通过本地接口访问，解决跨域和安全问题。
    """
    # 获取真实模型URL
    real_url = request.args.get('url')
    if not real_url:
        return "URL parameter is missing.", 400

    print(f"后端正在作为代理，请求真实URL: {real_url}")

    try:
        # 代理请求腾讯云临时URL，流式传输大文件
        res = requests.get(real_url, stream=True)
        if res.status_code != 200:
            print(f"代理请求失败，状态码: {res.status_code}")
            return f"Failed to fetch model from source, status: {res.status_code}", 502

        # 保留原始Content-Type，流式返回内容
        return Response(res.iter_content(chunk_size=1024), content_type=res.headers.get('Content-Type'))

    except Exception as e:
        print(f"代理请求时发生错误: {e}")
        return "Error during proxy request.", 500

# 主程序入口，开发模式下启动Flask服务
if __name__ == '__main__':
    app.run(debug=True)