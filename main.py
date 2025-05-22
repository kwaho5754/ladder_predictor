# ⬇️ main.py — 역방향 흐름 점수제 (Top3 형식 출력)

from flask import Flask, jsonify
from flask_cors import CORS
import requests
import os
from collections import defaultdict

app = Flask(__name__)
CORS(app)

def parse_block(block):
    return block[0], block[1], block[2]  # (시작, 줄수, 홀짝)

def convert(entry):
    side = '좌' if entry['start_point'] == 'LEFT' else '우'
    count = str(entry['line_count'])
    oe = '짝' if entry['odd_even'] == 'EVEN' else '홀'
    return f"{side}{count}{oe}"

def flip_start(s):
    return '우' if s == '좌' else '좌'

def flip_oe(o):
    return '짝' if o == '홀' else '홀'

def generate_variants_for_block(block):
    variants = {"원본": block, "대칭시작": [], "대칭홀짝": [], "대칭둘다": []}
    for b in block:
        s, c, o = parse_block(b)
        variants["대칭시작"].append(f"{flip_start(s)}{c}{o}")
        variants["대칭홀짝"].append(f"{s}{c}{flip_oe(o)}")
        variants["대칭둘다"].append(f"{flip_start(s)}{c}{flip_oe(o)}")
    return variants

def match_blocks(data, size):
    reversed_data = list(reversed(data))
    recent = [convert(d) for d in reversed_data[:size]]
    variants = generate_variants_for_block(recent)
    all_data = [convert(d) for d in reversed_data]

    scores = defaultdict(lambda: {"score": 0, "detail": defaultdict(int)})

    for i in range(len(all_data) - size):
        past_block = all_data[i:i+size]
        if past_block == variants['원본']:
            target = reversed_data[i+size] if i + size < len(reversed_data) else None
            if target:
                val = convert(target)
                scores[val]["score"] += 3
                scores[val]["detail"]["원본반복"] += 1
        if past_block == variants['대칭시작']:
            target = reversed_data[i+size] if i + size < len(reversed_data) else None
            if target:
                val = convert(target)
                scores[val]["score"] += 2
                scores[val]["detail"]["시작대칭"] += 1
        if past_block == variants['대칭홀짝']:
            target = reversed_data[i+size] if i + size < len(reversed_data) else None
            if target:
                val = convert(target)
                scores[val]["score"] += 2
                scores[val]["detail"]["홀짝대칭"] += 1
        if past_block == variants['대칭둘다']:
            target = reversed_data[i+size] if i + size < len(reversed_data) else None
            if target:
                val = convert(target)
                scores[val]["score"] += 1
                scores[val]["detail"]["시작+홀짝대칭"] += 1

    return scores

@app.route("/predict")
def predict():
    try:
        url = "https://ntry.com/data/json/games/power_ladder/recent_result.json"
        raw = requests.get(url).json()
        data = raw[-288:]
        round_num = int(raw[-1]['date_round']) + 1

        all_scores = defaultdict(lambda: {"score": 0, "detail": defaultdict(int)})
        for size in range(3, 8):  # 3~7줄 블럭
            scores = match_blocks(data, size)
            for key, val in scores.items():
                all_scores[key]["score"] += val["score"]
                for k, v in val["detail"].items():
                    all_scores[key]["detail"][k] += v

        sorted_result = sorted(all_scores.items(), key=lambda x: x[1]['score'], reverse=True)
        top3 = []
        for i in range(3):
            if i < len(sorted_result):
                name, info = sorted_result[i]
                top3.append({"값": name, "점수": info["score"], "근거": dict(info["detail"])})
            else:
                top3.append({"값": "❌ 없음", "점수": 0, "근거": {}})

        return jsonify({"예측회차": round_num, "Top3": top3})

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
