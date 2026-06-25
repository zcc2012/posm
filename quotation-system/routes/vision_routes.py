import base64
import json
import mimetypes
import os
import re
import urllib.error
import urllib.request
from difflib import SequenceMatcher

from flask import Blueprint, jsonify, request

from database import get_db_connection

bp = Blueprint('vision_api', __name__)

MAX_UPLOAD_MB = int(os.environ.get('VISION_MAX_UPLOAD_MB', '8'))
DEFAULT_OPENAI_MODEL = os.environ.get('OPENAI_VISION_MODEL', 'gpt-5.5')
DEFAULT_OPENCLAW_MODEL = os.environ.get('OPENCLAW_MODEL', 'minimax3')
DEFAULT_MINIMAX_MODEL = os.environ.get('MINIMAX_VISION_MODEL', 'MiniMax-M3')


class VisionProviderError(RuntimeError):
    pass


def get_vision_provider():
    configured_provider = os.environ.get('VISION_PROVIDER', '').strip().lower()
    if configured_provider:
        return configured_provider
    if get_minimax_api_key():
        return 'minimax'
    if os.environ.get('OPENCLAW_API_BASE'):
        return 'openclaw'
    if os.environ.get('OPENAI_API_KEY'):
        return 'openai'
    return 'mock'


def get_minimax_api_key():
    return (
        os.environ.get('MINIMAX_VISION_API_KEY')
        or os.environ.get('MINIMAX_API_KEY')
        or os.environ.get('MINIMAX_CN_API_KEY')
        or ''
    ).strip()


def get_minimax_base_url():
    configured = (
        os.environ.get('MINIMAX_VISION_API_BASE')
        or os.environ.get('MINIMAX_OPENAI_BASE_URL')
        or os.environ.get('MINIMAX_API_BASE')
        or ''
    ).strip().rstrip('/')
    if configured:
        return configured

    cn_base = (os.environ.get('MINIMAX_CN_BASE_URL') or '').strip().rstrip('/')
    if cn_base:
        if cn_base.endswith('/anthropic'):
            return f'{cn_base[:-10]}/v1'
        if cn_base.endswith('/v1'):
            return cn_base
        return f'{cn_base}/v1'

    return 'https://api.minimax.io/v1'


def normalize_minimax_model(model):
    value = (model or '').strip()
    if value.lower() in ('minimax3', 'minimax-m3', 'minimax_m3', 'm3'):
        return 'MiniMax-M3'
    return value or 'MiniMax-M3'


def load_quote_candidates():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT m.id, m.name, m.specification, m.category_id, c.name AS category_name
        FROM materials m
        LEFT JOIN material_categories c ON m.category_id = c.id
        ORDER BY c.name, m.name
    ''')
    materials = [{
        'id': row[0],
        'name': row[1] or '',
        'specification': row[2] or '',
        'category_id': row[3],
        'category_name': row[4] or ''
    } for row in cursor.fetchall()]

    cursor.execute('SELECT id, name FROM material_categories ORDER BY name')
    categories = [{'id': row[0], 'name': row[1] or ''} for row in cursor.fetchall()]

    cursor.execute('SELECT id, name FROM processes ORDER BY name')
    processes = [{'id': row[0], 'name': row[1] or ''} for row in cursor.fetchall()]

    conn.close()
    return materials, categories, processes


def compact_candidates(items, fields, limit=80):
    values = []
    for item in items[:limit]:
        values.append({field: item.get(field) for field in fields})
    return values


def build_prompt(materials, categories, processes, hint):
    return f'''
你是“明邦图纸识别员”，唯一任务是识别展示道具、POSM物料、印刷品和结构图纸，并把图片内容转换成后续报价表可直接填充的结构化部件数据。

你的工作边界：
1. 只做图片类型判断、图纸文字/OCR理解、部件名称提取、长宽尺寸提取、数量提取、材料和工艺猜测。
2. 不聊天，不生成营销文案，不直接给最终价格。
3. 不确定的信息必须留空或填 0，并写入 warnings，不能编造尺寸。

请只返回一个 JSON 对象，不要 markdown，不要解释文字。JSON 字段必须为：
{{
  "image_type": "产品照片/图纸/CAD截图/材料照片/未知",
  "confidence": 0.0,
  "parts": [
    {{
      "name": "部件名称，无法识别则填部件1",
      "length_mm": 0,
      "width_mm": 0,
      "quantity": 1,
      "material_category": "尽量从候选分类里选择",
      "material_name": "尽量从候选材料里选择",
      "process_name": "尽量从候选工艺里选择",
      "notes": "识别依据或不确定点",
      "confidence": 0.0
    }}
  ],
  "warnings": ["需要人工确认的事项"]
}}

规则：
1. 只有图纸或图片上明确出现尺寸时，才填写 length_mm 和 width_mm；无法确定就填 0。
2. 尺寸统一换算为毫米，输出数字，不要带单位。
3. 如果一个项目有多个零件，请拆成多个 parts。
4. 材料、分类、工艺尽量匹配候选列表；不确定时可留空，但要在 warnings 说明。
5. 这不是最终报价，所有识别结果都需要人工确认。

候选材料分类：
{json.dumps(compact_candidates(categories, ['id', 'name'], 80), ensure_ascii=False)}

候选材料：
{json.dumps(compact_candidates(materials, ['id', 'name', 'specification', 'category_name'], 120), ensure_ascii=False)}

候选工艺：
{json.dumps(compact_candidates(processes, ['id', 'name'], 120), ensure_ascii=False)}

用户补充说明：
{hint or '无'}
'''.strip()


def normalize_text(value):
    return re.sub(r'[\s\-_（）()【】\[\]{}、，,。.:：/]+', '', str(value or '').lower())


def match_candidate(value, candidates, fields, min_score=0.48):
    needle = normalize_text(value)
    if not needle:
        return None, 0

    best_item = None
    best_score = 0
    for item in candidates:
        haystacks = [normalize_text(item.get(field)) for field in fields]
        for haystack in haystacks:
            if not haystack:
                continue
            if needle == haystack:
                score = 1
            elif needle in haystack or haystack in needle:
                score = 0.86
            else:
                score = SequenceMatcher(None, needle, haystack).ratio()
            if score > best_score:
                best_score = score
                best_item = item

    if best_score < min_score:
        return None, best_score
    return best_item, best_score


def coerce_number(value, default=0):
    try:
        if value is None or value == '':
            return default
        return round(float(value), 2)
    except (TypeError, ValueError):
        return default


def coerce_quantity(value):
    try:
        quantity = int(float(value))
        return max(quantity, 1)
    except (TypeError, ValueError):
        return 1


def normalize_ai_result(result, materials, categories, processes, provider, configured=True):
    parts = result.get('parts') if isinstance(result, dict) else []
    if not isinstance(parts, list):
        parts = []

    normalized_parts = []
    for index, part in enumerate(parts, start=1):
        if not isinstance(part, dict):
            continue

        category_match, category_score = match_candidate(
            part.get('material_category'), categories, ['name']
        )
        material_match, material_score = match_candidate(
            part.get('material_name'), materials, ['name', 'specification']
        )
        process_match, process_score = match_candidate(
            part.get('process_name'), processes, ['name']
        )

        category_name = part.get('material_category') or ''
        category_id = category_match.get('id') if category_match else None
        if material_match:
            category_name = material_match.get('category_name') or category_name
            category_id = material_match.get('category_id') or category_id

        material_name = part.get('material_name') or ''
        if material_match:
            material_name = material_match.get('name') or material_name
            if material_match.get('specification'):
                material_name = f"{material_name}（{material_match.get('specification')}）"

        process_name = part.get('process_name') or ''
        if process_match:
            process_name = process_match.get('name') or process_name

        normalized_parts.append({
            'name': str(part.get('name') or f'部件{index}').strip(),
            'length_mm': coerce_number(part.get('length_mm')),
            'width_mm': coerce_number(part.get('width_mm')),
            'quantity': coerce_quantity(part.get('quantity')),
            'material_category': category_name,
            'material_name': material_name,
            'process_name': process_name,
            'matched_category_id': category_id,
            'matched_material_id': material_match.get('id') if material_match else None,
            'matched_process_id': process_match.get('id') if process_match else None,
            'match_scores': {
                'category': round(category_score, 2),
                'material': round(material_score, 2),
                'process': round(process_score, 2)
            },
            'notes': str(part.get('notes') or '').strip(),
            'confidence': coerce_number(part.get('confidence'), 0)
        })

    warnings = result.get('warnings', []) if isinstance(result, dict) else []
    if not isinstance(warnings, list):
        warnings = [str(warnings)]

    return {
        'success': True,
        'configured': configured,
        'provider': provider,
        'image_type': str(result.get('image_type') or '未知') if isinstance(result, dict) else '未知',
        'confidence': coerce_number(result.get('confidence'), 0) if isinstance(result, dict) else 0,
        'parts': normalized_parts,
        'warnings': [str(item) for item in warnings if str(item).strip()]
    }


def parse_json_object(text):
    content = str(text or '').strip()
    content = re.sub(r'^```(?:json)?\s*', '', content)
    content = re.sub(r'\s*```$', '', content)
    if not content.startswith('{'):
        start = content.find('{')
        end = content.rfind('}')
        if start >= 0 and end > start:
            content = content[start:end + 1]
    return json.loads(content)


def http_json(url, payload, api_key=None, timeout=90):
    headers = {'Content-Type': 'application/json'}
    if api_key:
        headers['Authorization'] = f'Bearer {api_key}'

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers=headers,
        method='POST'
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as error:
        body = error.read().decode('utf-8', errors='replace')
        raise VisionProviderError(f'HTTP {error.code}: {body[:800]}') from error


def extract_response_text(response):
    if response.get('output_text'):
        return response['output_text']

    chunks = []
    for output in response.get('output', []):
        for content in output.get('content', []):
            text = content.get('text') or content.get('value')
            if text:
                chunks.append(text)
    return '\n'.join(chunks)


def extract_chat_text(response):
    choices = response.get('choices') or []
    if not choices:
        return ''
    content = choices[0].get('message', {}).get('content', '')
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return '\n'.join(item.get('text', '') for item in content if isinstance(item, dict))
    return str(content or '')


def recognize_with_openai(prompt, image_data_url):
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise RuntimeError('OPENAI_API_KEY 未配置')

    payload = {
        'model': DEFAULT_OPENAI_MODEL,
        'input': [{
            'role': 'user',
            'content': [
                {'type': 'input_text', 'text': prompt},
                {'type': 'input_image', 'image_url': image_data_url}
            ]
        }],
        'max_output_tokens': 1800
    }
    response = http_json('https://api.openai.com/v1/responses', payload, api_key=api_key)
    return parse_json_object(extract_response_text(response))


def recognize_with_openclaw(prompt, image_data_url):
    base_url = os.environ.get('OPENCLAW_API_BASE', '').strip().rstrip('/')
    if not base_url:
        raise RuntimeError('OPENCLAW_API_BASE 未配置')

    api_key = os.environ.get('OPENCLAW_API_KEY') or os.environ.get('OPENAI_API_KEY')
    model = os.environ.get('OPENCLAW_MODEL', DEFAULT_OPENCLAW_MODEL)
    payload = {
        'model': model,
        'messages': [{
            'role': 'user',
            'content': [
                {'type': 'text', 'text': prompt},
                {'type': 'image_url', 'image_url': {'url': image_data_url}}
            ]
        }],
        'temperature': 0.1,
        'max_tokens': 1800
    }
    response = http_json(f'{base_url}/chat/completions', payload, api_key=api_key)
    return parse_json_object(extract_chat_text(response))


def recognize_with_minimax(prompt, image_data_url):
    api_key = get_minimax_api_key()
    if not api_key:
        raise RuntimeError('MINIMAX_VISION_API_KEY 或 MINIMAX_CN_API_KEY 未配置')

    base_url = get_minimax_base_url()
    model = normalize_minimax_model(
        os.environ.get('MINIMAX_VISION_MODEL') or os.environ.get('OPENCLAW_MODEL') or DEFAULT_MINIMAX_MODEL
    )
    payload = {
        'model': model,
        'messages': [{
            'role': 'user',
            'content': [
                {'type': 'text', 'text': prompt},
                {
                    'type': 'image_url',
                    'image_url': {
                        'url': image_data_url,
                        'detail': 'high'
                    }
                }
            ]
        }],
        'thinking': {'type': 'disabled'},
        'temperature': 0.1,
        'max_completion_tokens': 1800
    }
    response = http_json(f'{base_url}/chat/completions', payload, api_key=api_key)
    return parse_json_object(extract_chat_text(response))


def demo_result():
    return {
        'image_type': '图纸演示',
        'confidence': 0.1,
        'parts': [{
            'name': '演示侧板',
            'length_mm': 1200,
            'width_mm': 600,
            'quantity': 1,
            'material_category': '',
            'material_name': '',
            'process_name': '',
            'notes': '当前为演示结果：服务器还没有配置真实 AI 接口。',
            'confidence': 0.1
        }],
        'warnings': [
            '这是演示数据，不是真实识别结果。',
            '请在服务器配置 OPENCLAW_API_BASE 或 OPENAI_API_KEY 后再用于实际报价。'
        ]
    }


@bp.route('/api/vision/config', methods=['GET'])
def api_vision_config():
    provider = get_vision_provider()
    if provider == 'minimax':
        model = normalize_minimax_model(
            os.environ.get('MINIMAX_VISION_MODEL') or os.environ.get('OPENCLAW_MODEL') or DEFAULT_MINIMAX_MODEL
        )
        configured = bool(get_minimax_api_key())
    elif provider in ('openclaw', 'openai_compatible', 'mock'):
        model = DEFAULT_OPENCLAW_MODEL
        configured = provider != 'mock'
    else:
        model = DEFAULT_OPENAI_MODEL
        configured = provider != 'mock'

    return jsonify({
        'provider': provider,
        'configured': configured,
        'model': model,
        'max_upload_mb': MAX_UPLOAD_MB
    })


def guess_image_mimetype(filename, uploaded_mimetype):
    mimetype = uploaded_mimetype or ''
    if mimetype.startswith('image/'):
        return mimetype

    guessed = mimetypes.guess_type(filename or '')[0] or ''
    if guessed.startswith('image/'):
        return guessed

    return ''


@bp.route('/api/vision/recognize', methods=['POST'])
def api_vision_recognize():
    max_bytes = MAX_UPLOAD_MB * 1024 * 1024
    if request.content_length and request.content_length > max_bytes:
        return jsonify({'success': False, 'message': f'图片不能超过 {MAX_UPLOAD_MB}MB'}), 413

    image = request.files.get('image')
    if not image:
        return jsonify({'success': False, 'message': '请上传 image 文件'}), 400

    image_bytes = image.read()
    if not image_bytes:
        return jsonify({'success': False, 'message': '图片文件为空'}), 400
    if len(image_bytes) > max_bytes:
        return jsonify({'success': False, 'message': f'图片不能超过 {MAX_UPLOAD_MB}MB'}), 413

    mimetype = guess_image_mimetype(image.filename, image.mimetype)
    if not mimetype:
        return jsonify({'success': False, 'message': '只支持图片文件'}), 400

    provider = get_vision_provider()
    materials, categories, processes = load_quote_candidates()
    prompt = build_prompt(materials, categories, processes, request.form.get('hint', ''))
    image_data_url = f'data:{mimetype};base64,{base64.b64encode(image_bytes).decode("ascii")}'

    try:
        if provider == 'openai':
            result = recognize_with_openai(prompt, image_data_url)
            return jsonify(normalize_ai_result(result, materials, categories, processes, provider))
        if provider == 'minimax':
            result = recognize_with_minimax(prompt, image_data_url)
            return jsonify(normalize_ai_result(result, materials, categories, processes, provider))
        if provider in ('openclaw', 'openai_compatible'):
            result = recognize_with_openclaw(prompt, image_data_url)
            return jsonify(normalize_ai_result(result, materials, categories, processes, provider))

        result = demo_result()
        return jsonify(normalize_ai_result(result, materials, categories, processes, 'mock', configured=False))
    except (urllib.error.URLError, TimeoutError) as error:
        return jsonify({
            'success': False,
            'configured': True,
            'provider': provider,
            'message': f'AI 服务连接失败：{error}'
        }), 502
    except VisionProviderError as error:
        return jsonify({
            'success': False,
            'configured': True,
            'provider': provider,
            'message': f'AI 服务返回错误：{error}'
        }), 502
    except (json.JSONDecodeError, ValueError) as error:
        return jsonify({
            'success': False,
            'configured': True,
            'provider': provider,
            'message': f'AI 返回内容不是有效 JSON：{error}'
        }), 502
    except RuntimeError as error:
        return jsonify({
            'success': False,
            'configured': False,
            'provider': provider,
            'message': str(error)
        }), 503
