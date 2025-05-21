from flask import Flask, jsonify
from flask_cors import CORS
import requests
import os
from collections import Counter

app = Flask(__name__)
CORS(app)

def convert(entry):
    side = '좌' if entry['start_point'] == 'LEFT' else '우'
    count = str(entry['line_count'])
    oe = '짝' if entry['odd_even'] == 'EVEN' else '홀'
    return f"{side}{count}{oe}"

def get_full_mirror_name(name):
    side = '우' if '좌' in name else '좌'
    count = name[1]
    oe = '홀' if '짝' in name else '짝'
    return f"{side}{count}{oe}"

def extract_predictions(data, transform_func=None):
    predictions = []
    for size in range(2, 6):
        if len(data) < size:
            continue

        block = [convert(entry) for entry in data[-size:]]
        if transform_func:
            block = [transform_func(b) for b in block]
        pattern = '>'.join(block)

        for i in reversed(range(len(data) - size)):
            past_block = [convert(entry) for entry in data[i:i + size]]
            if pattern == '>'.join(past_block):
                if i > 0:
                    predictions.append(convert(data[i - 1]))
                if i + size < len(data):
                    predictions.append(convert(data[i + size]))
    return predictions

def top3_result(predictions):
    counter = Counter(predictions)
    top3_raw = counter.most_common(3)
    result = [{"value": val, "count": cnt} for val, cnt in top3_raw]
    while len(result) < 3:
        result.append({"value": "❌ 없음", "count": 0})
    return result

@app.route("/predict", methods=["GET"])
def predict():
    try:
        url = "https://ntry.com/data/json/games/power_ladder/recent_result.json"
        response = requests.get(url)
        raw_data = response.json()

        if not isinstance(raw_data, list):
            return jsonify({"error": "Invalid data format"})

        data = raw_data[-288:]
        round_num = int(raw_data[-1]["date_round"])

        original_preds = extract_predictions(data)
        mirror_preds = extract_predictions(data, transform_func=get_full_mirror_name)

        return jsonify({
            "예측회차": round_num,
            "원본 Top3": top3_result(original_preds),
            "대칭 Top3": top3_result(mirror_preds)
        })

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
