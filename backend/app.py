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
import base64  # 用于图片编码

# 加载.env文件中的环境变量
load_dotenv()
# 初始化Flask应用
app = Flask(__name__)
# 启用CORS，允许前端跨域访问
CORS(app)

# 读取腾讯云API密钥（从环境变量中获取）
TENCENT_SECRET_ID = os.getenv("TENCENT_SECRET_ID")
TENCENT_SECRET_KEY = os.getenv("TENCENT_SECRET_KEY")

def generate_3d_model_with_hunyuan(prompt, image_data=None):
    """
    调用腾讯云混元3D生成API，提交任务并轮询查询结果，返回模型和预览图URL。
    :param prompt: 用户输入的文本描述
    :param image_data: 用户上传的图片数据（可选）
    :return: dict，包含modelUrl和previewImageUrl，或None（失败）
    """
    print(f"正在准备调用混元AI，指令: {prompt or '无文本输入'}")
    
    try:
        # 1. 创建腾讯云鉴权对象
        cred = credential.Credential(TENCENT_SECRET_ID, TENCENT_SECRET_KEY)
        # 检查凭证是否有效（避免直接访问SecretId和SecretKey属性）
        if not TENCENT_SECRET_ID or not TENCENT_SECRET_KEY:
            print("错误：腾讯云凭证未配置或无效")
            return None
            
        # 2. 创建3D生成客户端
        client = ai3d_client.Ai3dClient(cred, "ap-guangzhou")
        
        # 3. 构造提交任务的请求
        req_submit = models.SubmitHunyuanTo3DJobRequest()
        
        # 根据是否有图片数据选择不同的API参数
        if image_data:
            # 图生模型模式 - Prompt必须为空字符串，只传ImageBase64
            params_submit = {
                "ImageBase64": image_data,
                "ResultFormat": "GLB",
                "EnablePBR": True
            }
            print(f"使用图生模型模式生成3D模型，Prompt: '', 图片数据大小: {len(image_data)} 字符")
        else:
            # 文生模型模式 - 只传Prompt，不传图片
            if not prompt or not prompt.strip():
                print("错误：文生模型模式需要提供有效的文本描述")
                return None
                
            params_submit = {
                "Prompt": prompt, 
                "ResultFormat": "GLB",
                "EnablePBR": True
            }
            print(f"使用文生模型模式生成3D模型，Prompt: {prompt}")
            
        # 4. 提交生成任务
        req_submit.from_json_string(json.dumps(params_submit))
        resp_submit = client.SubmitHunyuanTo3DJob(req_submit)
        
        if not resp_submit:
            print("错误：未能收到腾讯云API的有效响应")
            return None
            
        submit_result = json.loads(resp_submit.to_json_string())
        job_id = submit_result.get("JobId")

        if not job_id:
            error_code = submit_result.get('ErrorCode', 'Unknown')
            error_message = submit_result.get('ErrorMessage', '未知错误')
            print(f"错误：提交任务后未能获取到JobId。错误码: {error_code}, 原因: {error_message}")
            return None

        print(f"成功提交任务，获得 JobId: {job_id}。现在开始轮询查询结果...")

        # 5. 轮询查询任务状态
        max_retries = 60
        retry_count = 0
        start_time = time.time()

        while retry_count < max_retries:
            print(f"等待5秒后查询任务状态... (第 {retry_count + 1} 次尝试)")
            time.sleep(5)

            req_query = models.QueryHunyuanTo3DJobRequest()
            params_query = {"JobId": job_id}
            req_query.from_json_string(json.dumps(params_query))
            
            resp_query = client.QueryHunyuanTo3DJob(req_query)
            if not resp_query:
                print("错误：查询任务状态时未能收到有效响应")
                continue
                
            query_result = json.loads(resp_query.to_json_string())
            print(f"当前任务状态: {query_result.get('Status', '未知')}")

            if query_result.get("Status") == "DONE":
                # 任务完成，获取模型和预览图URL
                result_files = query_result.get("ResultFile3Ds", [])
                if not result_files:
                    print("错误：任务完成但未生成任何文件")
                    return None
                    
                model_url = result_files[0].get("Url")
                preview_image_url = result_files[0].get("PreviewImageUrl")
                
                if not model_url:
                    print("错误：任务完成但未找到模型URL")
                    return None
                    
                print(f"任务成功完成！模型URL: {model_url}, 预览图URL: {preview_image_url}")
                print(f"总耗时: {int(time.time() - start_time)} 秒")
                
                return {
                    "modelUrl": model_url,
                    "previewImageUrl": preview_image_url
                }
                
            elif query_result.get("Status") == "FAILED":
                # 任务失败，打印错误信息
                error_code = query_result.get('ErrorCode', 'Unknown')
                error_message = query_result.get('ErrorMessage', '未知错误')
                print(f"任务生成失败！错误码: {error_code}, 原因: {error_message}")
                return None
                
            elif query_result.get("Status") in ["WAIT", "RUN"]:
                # 任务仍在处理中，继续轮询
                retry_count += 1
                continue
                
            else:
                # 未知状态
                print(f"未知的任务状态: {query_result.get('Status', '空值')}")
                retry_count += 1
                continue

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
    支持两种模式：
    1. 文生模型：只提交text字段
    2. 图生模型：只提交image文件
    注意：不能同时提交text和image
    """
    print("========================================")
    print("接收到新的生成请求！")
    text_input = request.form.get('text')
    image_file = request.files.get('image')

    print(f"接收到的文本参数: {text_input}")
    print(f"接收到的图片参数: {image_file is not None}")
    
    if image_file:
        print(f"图片文件名: {image_file.filename}")
        print(f"图片MIME类型: {image_file.content_type}")
        # 使用seek和tell获取准确的文件大小
        image_file.seek(0, 2)  # 移动到文件末尾
        file_size = image_file.tell()  # 获取文件大小
        image_file.seek(0)  # 重置文件指针到开始位置
        print(f"图片大小: {file_size} 字节")

    # 验证输入参数
    if not text_input and not image_file:
        print("错误：未提供文本或图片参数")
        return jsonify({"status": "error", "message": "请输入文本或上传图片。"}), 400
    
    if text_input and image_file:
        print("错误：同时提供了文本和图片参数")
        return jsonify({"status": "error", "message": "不能同时提交文本和图片，请只选择其中一种方式生成3D模型。"}), 400

    # 处理输入数据
    image_data = None
    final_prompt = ""  # 初始化为空字符串
    
    if image_file:
        # 图生模型模式
        # 使用seek和tell获取准确的文件大小
        image_file.seek(0, 2)  # 移动到文件末尾
        file_size = image_file.tell()  # 获取文件大小
        image_file.seek(0)  # 重置文件指针到开始位置
        print(f"接收到图片文件: {image_file.filename}, 大小: {file_size} 字节")
        # 将图片文件转换为base64编码
        image_data = base64.b64encode(image_file.read()).decode('utf-8')
        print(f"图片数据大小: {len(image_data)} 字符")
        print(f"图片数据预览（前100字符）: {image_data[:100]}")
        # 图生模型模式下Prompt必须为空字符串
        final_prompt = ""
    elif text_input:
        # 文生模型模式
        final_prompt = text_input
        print(f"使用文生模型模式，Prompt: {final_prompt}")

    print("最终整合的指令(Prompt):", final_prompt)
    print("是否有图片数据:", bool(image_data))
    print("使用的模式:", "图生模型" if image_data else "文生模型")
    print("========================================")

    # 调用核心生成函数
    result_data = generate_3d_model_with_hunyuan(final_prompt, image_data)
    if result_data and result_data.get("modelUrl"):
        # 成功，返回模型和预览图URL
        print("模型生成成功，返回结果给前端")
        return jsonify({
            "status": "success",
            "message": "模型生成成功！",
            "modelUrl": result_data.get("modelUrl"),
            "previewImageUrl": result_data.get("previewImageUrl")
        })
    else:
        # 失败，返回错误
        print("模型生成失败")
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
    app.run(host='0.0.0.0', port=5000, debug=False)