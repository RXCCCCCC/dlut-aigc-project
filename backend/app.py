# 导入所有依赖库
from flask import Response  # 用于自定义HTTP响应（如流式返回大文件）
import requests  # 用于后端代理请求外部资源
from flask import Flask, request, jsonify  # Flask核心功能
from openai import OpenAI  # 用于调用 SiliconFlow deepseek-r1
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

# 新增：数据库与认证相关
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import datetime

# 速率限制
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# 腾讯COS SDK（可选，如果未配置则使用本地存储）
try:
    from qcloud_cos import CosConfig, CosS3Client
    HAS_COS = True
except Exception:
    HAS_COS = False
    CosConfig = None
    CosS3Client = None

# 加载.env文件中的环境变量
load_dotenv()
# 初始化Flask应用
app = Flask(__name__)
# 启用CORS，允许前端跨域访问
FRONTEND_ORIGIN = os.getenv('FRONTEND_ORIGIN')
if FRONTEND_ORIGIN:
    CORS(app, origins=FRONTEND_ORIGIN, supports_credentials=False)
else:
    CORS(app)

# 配置数据库（默认使用项目内 sqlite），可通过环境变量覆盖
# 在阿里云或其他 Linux 服务器上，建议使用绝对路径，或在环境变量中设置 `DATABASE_URL` 或 `SQLITE_FILE`
project_root = os.path.abspath(os.path.dirname(__file__))
# SQLITE_FILE 指定具体 db 文件路径（例如 /var/www/app/data.db），优先使用 DATABASE_URL
default_db_file = os.getenv('SQLITE_FILE', os.path.join(project_root, 'data.db'))
db_uri = os.getenv('DATABASE_URL', f"sqlite:///{default_db_file}")
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# 对于 SQLite，当在多线程/多进程环境中使用，需要设置 connect_args
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'connect_args': { 'check_same_thread': False },
    'pool_pre_ping': True
}

# 确保数据库目录存在并且可写（在阿里云上常见问题是权限或目录缺失）
db_dir = os.path.dirname(default_db_file)
if db_dir and not os.path.exists(db_dir):
    try:
        os.makedirs(db_dir, exist_ok=True)
    except Exception as e:
        print(f"无法创建数据库目录 {db_dir}: {e}")

print(f"Using database URI: {app.config.get('SQLALCHEMY_DATABASE_URI')}")

# JWT 配置
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'change-me-in-prod')

# 初始化扩展
db = SQLAlchemy(app)
jwt = JWTManager(app)

# 初始化速率限制器（针对IP）
limiter = Limiter(key_func=get_remote_address, app=app, default_limits=["200 per day", "50 per hour"])


# 模型定义：用户和生成历史
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class History(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    prompt = db.Column(db.Text)
    # 存储方式：provider='local' 或 'cos'，存储路径为 storage_path
    storage_provider = db.Column(db.String(40), default='local')
    storage_path = db.Column(db.Text)
    preview_path = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# 在启动时创建表（如果不存在）
with app.app_context():
    db.create_all()

# 存储相关配置（本地或腾讯 COS）
STORAGE_PROVIDER = os.getenv('STORAGE_PROVIDER', 'local')  # 'local' or 'cos'
LOCAL_STORAGE_DIR = os.getenv('LOCAL_STORAGE_DIR', './storage')
if not os.path.exists(LOCAL_STORAGE_DIR):
    os.makedirs(LOCAL_STORAGE_DIR, exist_ok=True)

# COS 配置（如果使用）
COS_SECRET_ID = os.getenv('COS_SECRET_ID')
COS_SECRET_KEY = os.getenv('COS_SECRET_KEY')
COS_REGION = os.getenv('COS_REGION', 'ap-guangzhou')
COS_BUCKET = os.getenv('COS_BUCKET')

cos_client = None
if STORAGE_PROVIDER == 'cos' and HAS_COS:
    if COS_SECRET_ID and COS_SECRET_KEY and COS_BUCKET:
        cos_config = CosConfig(Region=COS_REGION, SecretId=COS_SECRET_ID, SecretKey=COS_SECRET_KEY)
        cos_client = CosS3Client(cos_config)
    else:
        print('COS 配置不完整，回退到本地存储')
        STORAGE_PROVIDER = 'local'


# ---------- 认证接口 (注册 / 登录) ----------
@app.route('/api/auth/register', methods=['POST'])
def register():
    # 输入校验：简单规则，用户名长度 3-32，密码最少 6 位
    data = request.get_json() or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    if not username or not password:
        return jsonify({'msg': 'username and password required'}), 400
    if len(username) < 3 or len(username) > 32:
        return jsonify({'msg': 'username length must be 3-32'}), 400
    if len(password) < 6:
        return jsonify({'msg': 'password too short (min 6)'}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({'msg': 'username already exists'}), 409
    user = User(username=username, password_hash=generate_password_hash(password))
    db.session.add(user)
    db.session.commit()
    return jsonify({'msg': 'registered'}), 201


@limiter.limit("10 per 10 minutes")
@app.route('/api/auth/login', methods=['POST'])
def login():
    # 限制登录频率：每个IP 10 次 / 10 分钟（通过装饰器在后面配置）
    data = request.get_json() or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    if not username or not password:
        return jsonify({'msg': 'username and password required'}), 400
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({'msg': 'invalid credentials'}), 401
    access_token = create_access_token(identity=user.id)
    return jsonify({'access_token': access_token, 'username': user.username}), 200


# ---------- 历史记录接口 ----------
@app.route('/api/history', methods=['GET'])
@jwt_required()
def list_history():
    user_id = get_jwt_identity()
    records = History.query.filter_by(user_id=user_id).order_by(History.created_at.desc()).all()
    return jsonify([{
        'id': r.id,
        'prompt': r.prompt,
        'storage_provider': r.storage_provider,
        'storage_path': r.storage_path,
        'preview_path': r.preview_path,
        'created_at': r.created_at.isoformat()
    } for r in records])


@app.route('/api/history', methods=['POST'])
@jwt_required()
def create_history():
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    prompt = data.get('prompt')
    storage_provider = data.get('storage_provider', 'local')
    storage_path = data.get('storage_path')
    preview_path = data.get('preview_path')
    h = History(user_id=user_id, prompt=prompt, storage_provider=storage_provider, storage_path=storage_path, preview_path=preview_path)
    db.session.add(h)
    db.session.commit()
    return jsonify({'id': h.id}), 201


@app.route('/api/history/<int:hid>', methods=['DELETE'])
@jwt_required()
def delete_history(hid):
    user_id = get_jwt_identity()
    h = History.query.get_or_404(hid)
    if h.user_id != user_id:
        return jsonify({'msg': 'forbidden'}), 403
    db.session.delete(h)
    db.session.commit()
    return jsonify({'msg': 'deleted'})


@app.route('/api/history/download/<int:hid>')
@jwt_required()
def download_history(hid):
    user_id = get_jwt_identity()
    h = History.query.get_or_404(hid)
    if h.user_id != user_id:
        return jsonify({'msg': 'forbidden'}), 403
    # 根据存储提供者获取并返回文件
    if not h.storage_path:
        return jsonify({'msg': 'no model stored'}), 404
    try:
        if h.storage_provider == 'local' or STORAGE_PROVIDER == 'local':
            file_path = h.storage_path
            if not os.path.isabs(file_path):
                file_path = os.path.join(LOCAL_STORAGE_DIR, file_path)
            if not os.path.exists(file_path):
                return jsonify({'msg': 'file not found'}), 404
            def generate():
                with open(file_path, 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b''):
                        yield chunk
            return Response(generate(), content_type='application/octet-stream')
        elif h.storage_provider == 'cos' and cos_client:
            # 从 COS 获取对象并流式返回
            key = h.storage_path
            resp = cos_client.get_object(Bucket=COS_BUCKET, Key=key)
            body = resp['Body'].get_raw_stream()
            return Response(body, content_type=resp.get('ContentType', 'application/octet-stream'))
        else:
            return jsonify({'msg': 'unsupported storage provider'}), 500
    except Exception as e:
        print('download proxy error', e)
        return jsonify({'msg': 'error fetching model'}), 500

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


def _download_file_to_local(url, dest_path, max_bytes=None):
    try:
        r = requests.get(url, stream=True, timeout=30)
        if r.status_code != 200:
            return False, f'status {r.status_code}'
        total = 0
        with open(dest_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    total += len(chunk)
                    if max_bytes and total > max_bytes:
                        return False, 'file too large'
        return True, None
    except Exception as e:
        return False, str(e)


def save_model_to_storage(model_url, preview_url=None):
    """下载 model_url（和 preview_url 可选），并保存到 STORAGE_PROVIDER 指定的位置。
    返回 (provider, storage_path, preview_path)
    """
    # 生成文件名基于时间戳
    ts = int(time.time())
    model_filename = f'model_{ts}.glb'
    preview_filename = f'preview_{ts}.jpg'

    if STORAGE_PROVIDER == 'local' or not cos_client:
        model_rel = model_filename
        model_path = os.path.join(LOCAL_STORAGE_DIR, model_rel)
        ok, err = _download_file_to_local(model_url, model_path, max_bytes=200*1024*1024)
        if not ok:
            return 'local', None, None
        preview_rel = None
        if preview_url:
            preview_rel = preview_filename
            preview_path = os.path.join(LOCAL_STORAGE_DIR, preview_rel)
            _download_file_to_local(preview_url, preview_path, max_bytes=5*1024*1024)
        return 'local', model_rel, (preview_rel or None)
    else:
        # 上传到 COS
        try:
            # 下载到临时本地文件，然后上传
            tmp_model = os.path.join(LOCAL_STORAGE_DIR, model_filename)
            ok, err = _download_file_to_local(model_url, tmp_model, max_bytes=500*1024*1024)
            if not ok:
                return 'cos', None, None
            key = f'uploads/{model_filename}'
            with open(tmp_model, 'rb') as f:
                cos_client.put_object(Bucket=COS_BUCKET, Body=f, Key=key)
            preview_key = None
            if preview_url:
                tmp_preview = os.path.join(LOCAL_STORAGE_DIR, preview_filename)
                _download_file_to_local(preview_url, tmp_preview, max_bytes=10*1024*1024)
                with open(tmp_preview, 'rb') as pf:
                    preview_key = f'uploads/{preview_filename}'
                    cos_client.put_object(Bucket=COS_BUCKET, Body=pf, Key=preview_key)
            # 清理临时文件
            try:
                os.remove(tmp_model)
                if preview_url:
                    os.remove(tmp_preview)
            except Exception:
                pass
            return 'cos', key, (preview_key or None)
        except Exception as e:
            print('cos upload failed', e)
            return 'cos', None, None


# 处理前端生成请求的API路由（需要登录）
@app.route('/api/generate', methods=['POST'])
@jwt_required()
@limiter.limit("5 per 10 minutes")
def handle_generation_request():
    print("========================================")
    print("接收到新的生成请求！")
    text_input = request.form.get('text')
    image_file = request.files.get('image')

    print(f"接收到的文本参数: {text_input}")
    print(f"接收到的图片参数: {image_file is not None}")

    if image_file:
        print(f"图片文件名: {image_file.filename}")
        print(f"图片MIME类型: {image_file.content_type}")
        image_file.seek(0, 2)
        file_size = image_file.tell()
        image_file.seek(0)
        print(f"图片大小: {file_size} 字节")

    if not text_input and not image_file:
        print("错误：未提供文本或图片参数")
        return jsonify({"status": "error", "message": "请输入文本或上传图片。"}), 400
    if text_input and image_file:
        print("错误：同时提供了文本和图片参数")
        return jsonify({"status": "error", "message": "不能同时提交文本和图片，请只选择其中一种方式生成3D模型。"}), 400

    image_data = None
    final_prompt = ""
    if image_file:
        image_file.seek(0, 2)
        file_size = image_file.tell()
        image_file.seek(0)
        image_data = base64.b64encode(image_file.read()).decode('utf-8')
        final_prompt = ""
    elif text_input:
        # 文生模型模式，先用 deepseek-r1 处理
        try:
            # 初始化 SiliconFlow 客户端
            client = OpenAI(
                api_key=os.getenv('SILICONFLOW_API_KEY'),
                base_url='https://api.siliconflow.cn/v1'
            )
            
            # 构造更明确的 deepseek-r1 指令
            system_prompt = (
                "你是一个3D模型生成助手。请对用户输入的原始文本进行语义纠错和丰富性加工，生成更适合用于3D模型生成的描述性文字。"
                "要求："
                "1. 保持原始意图"
                "2. 增加细节描述，使描述更具体"
                "3. 使用适合3D建模的术语"
                "4. 避免使用过于抽象的术语"
                "5. 只输出交给混元ai进行文生3D模型的描述性文本，避免输出任何多余内容而影响模型生成"
            )
            user_prompt = f"原始文本：{text_input}\n请将上述文本优化为适合3D模型生成的描述性文字。注意只输出交给混元ai进行文生3D模型的描述性文本，避免输出任何多余内容而影响模型生成"

            # 调用 SiliconFlow API
            response = client.chat.completions.create(
                model="deepseek-ai/DeepSeek-R1",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7
            )
            
            processed_text = response.choices[0].message.content
            final_prompt = processed_text
            print(f"经过 deepseek-r1 处理后的描述: {final_prompt}")
        except Exception as e:
            print(f"SiliconFlow deepseek-r1 处理失败: {e}")
            # 即使文本增强失败，也继续使用原始文本
            final_prompt = text_input
            print(f"使用原始文本: {final_prompt}")

    print("最终整合的指令(Prompt):", final_prompt)
    print("是否有图片数据:", bool(image_data))
    print("使用的模式:", "图生模型" if image_data else "文生模型")
    print("========================================")

    # 调用核心生成函数
    result_data = generate_3d_model_with_hunyuan(final_prompt, image_data)
    if result_data and result_data.get("modelUrl"):
        print("模型生成成功，返回结果给前端")
        # 将模型下载并转存到配置的存储
        try:
            provider, storage_path, preview_path = save_model_to_storage(result_data.get('modelUrl'), result_data.get('previewImageUrl'))
            user_id = None
            try:
                user_id = get_jwt_identity()
            except Exception:
                user_id = None
            h = History(user_id=user_id or None, prompt=(final_prompt or text_input or ''), storage_provider=provider, storage_path=(storage_path or result_data.get('modelUrl')), preview_path=(preview_path or result_data.get('previewImageUrl')))
            db.session.add(h)
            db.session.commit()
        except Exception as e:
            print("保存历史记录失败:", e)
        # 返回前端原始的临时URL（前端仍通过代理加载）
        return jsonify({
            "status": "success",
            "message": "模型生成成功！",
            "modelUrl": result_data.get("modelUrl"),
            "previewImageUrl": result_data.get("previewImageUrl")
        })
    else:
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