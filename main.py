from flask import Flask, jsonify
from flask_cors import CORS
import requests
import os
from collections import Counter

app = Flask(__name__)
CORS(app)

# 블럭을 한글 문자열로 변환
def convert(entry):
    side = '좌' if entry['start_point'] == 'LEFT' else '우'
    count = str(entry['line_count'])
    oe = '짝' if entry['odd_even'] == 'EVEN' else '홀'
    return f"{side}{count}{oe}"

# 블럭 문자열 대칭 변환
def mirror(block):
    result = []
    for b in block.split('>'):
        side = '우' if b[0] == '좌' else '좌'
        oe = '짝' if b[2] == '홀' else '홀'
        result.append(f"{side}{b[1]}{oe}")
    return '>'.join(result)

# 최근 블럭 리스트 생성 (2~5줄)
def generate_blocks(data):
    blocks = []
    for size in range(2, 6):
        if len(data) < size:
            continue
        block = '>'.join([convert(entry) for entry in data[-size:]])
        blocks.append((size, block))
    return blocks

# 예측값 추출 함수
def find_predictions(data, blocks):
    total = len(data)
    predictions = []

    for size, block in blocks:
        for use_block in [block, mirror(block)]:
            for i in reversed(range(total - size)):  # 최근 → 과거
                compare = '>'.join([convert(entry) for entry in data[i:i+size]])
                if compare == use_block:
                    if i > 0:
                        predictions.append(convert(data[i - 1]))  # 상단
                    if i + size < total:
                        predictions.append(convert(data[i + size]))  # 하단

    if not predictions:
        return [{"value": "❌ 없음", "count": 0} for _ in range(3)]

    counter = Counter(predictions)
    top3_raw = counter.most_common(3)
    top3 = [{"value": item, "count": count} for item, count in top3_raw]

    while len(top3) < 3:
        top3.append({"value": "❌ 없음", "count": 0})

    return top3

@app.route("/predict", methods=["GET"])
def predict():
    try:
        url = "https://ntry.com/data/json/games/power_ladder/recent_result.json"
        response = requests.get(url)
        raw_data = response.json()

        if not isinstance(raw_data, list):
            return jsonify({"error": "Invalid data format"})

        recent = raw_data[-288:]
        blocks = generate_blocks(recent)
        top3 = find_predictions(recent, blocks)

        return jsonify({
            "예측회차": int(raw_data[-1]["date_round"]),
            "Top3 예측값": top3
        })

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
