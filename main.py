import os
from flask import Flask, jsonify, escape, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/", methods=["GET"])
def metrics():
    try:
        uid = request.headers.get('X-UID')
        account_id = request.headers.get('X-ACCOUNT-ID')
        campaigns = request.args.get('campaings')

        response = {
            "clicks": 173,
            "ctr": 0.15,
            "impressions": 1582,
            "conversions": 45,
            "conversions_rate": 45/1582,
            "cost_per_conversion": 30.20,
            "click_cost": 7.82,
            "cpm_average": 4.2,
            "cpm_average": 1.3,
            "reach": 1579,
            "views": 300,
        }
        return jsonify(response), 200
    except Exception as e:
        return f"An Error Occured: {e}"

if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0',port=os.environ.get('PORT', 80))

