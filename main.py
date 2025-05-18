from flask import Flask, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

# 블럭 코드 생성
def convert(entry):
    start = 'L' if entry['start_point'] == 'LEFT' else 'R'
    count = str(entry['line_count'])
    oe = 'E' if entry['odd_even'] == 'EVEN' else 'O'
    return f"{start}{count}{oe}"

# 한글 변환
def to_korean(block_code):
    if block_code == "❌ 없음":
        return "❌ 없음"
    start = "좌" if block_code[0] == "L" else "우"
    count = block_code[1]
    oe = "짝" if block_code[2] == "E" else "홀"
    return f"{start}{count}{oe}"

# 완전한 뒤 기준 예측
def predict_backward(data):
    recent = data[-288:]
    total = len(recent)
    predictions = []

    for size in range(2, 7):
        if total <= size:
            continue
        recent_block = ''.join([convert(entry)[-2:] for entry in recent[-size:]])
        for i in range(total - size):
            past_block = ''.join([convert(entry)[-2:] for entry in recent[i:i + size]])
            if recent_block == past_block:
                # 뒤 기준: 블럭 다음 줄(i + size)이 존재하면 예측값으로 사용
                if i + size < total:
                    result = convert(recent[i + size])
                    predictions.append(result)
                else:
                    predictions.append("❌ 없음")
                break
        else:
            predictions.append("❌ 없음")

    return predictions[:5]

@app.route("/predict", methods=["GET"])
def predict():
    try:
        url = "https://ntry.com/data/json/games/power_ladder/recent_result.json"
        response = requests.get(url)
        raw_data = response.json()

        if not isinstance(raw_data, list):
            return jsonify({"error": "Invalid data format"})

        predictions = predict_backward(raw_data)
        round_number = int(raw_data[-1]["date_round"]) + 1  # 예측 회차는 다음 회차

        return jsonify({
            "예측회차": round_number,
            "뒤기준 예측값": [to_korean(p) for p in predictions]
        })

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
