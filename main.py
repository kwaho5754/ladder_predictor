from flask import Flask, render_template_string
import requests

app = Flask(__name__)

URL = "https://ntry.com/data/json/games/power_ladder/recent_result.json"

def fetch_latest_data():
    try:
        res = requests.get(URL)
        res.encoding = 'utf-8'
        data = res.json()
        rows = data['rows']
        return [row['result'] for row in rows][-288:]  # 최근 288줄
    except Exception as e:
        print("Error fetching data:", e)
        return []

def make_back_block(lines):
    return ''.join([line[-2:] for line in lines])

def get_back_predictions(data):
    predictions = []
    for size in range(2, 7):
        if len(data) < size + 1:
            continue
        target_block = make_back_block(data[-size:])
        for i in range(len(data) - size):
            block = make_back_block(data[i:i+size])
            if block == target_block:
                pred = data[i - 1] if i - 1 >= 0 else '❌ 없음'
                predictions.append(pred)
                break
        if len(predictions) >= 5:
            break
    while len(predictions) < 5:
        predictions.append('❌ 없음')
    return predictions

@app.route('/predict')
def predict():
    data = fetch_latest_data()
    if not data:
        return "데이터 불러오기 실패"
    back_preds = get_back_predictions(data)
    html = """
    <h2>사다리 예측 시스템 - 뒤 기준 (역방향)</h2>
    <ul>
    {% for i, pred in enumerate(preds) %}
        <li>Top {{ i+1 }} : {{ pred }}</li>
    {% endfor %}
    </ul>
    """
    return render_template_string(html, preds=back_preds)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
