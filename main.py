import os
import sys
from flask import Flask, jsonify, escape, request
from flask_cors import CORS
from google.cloud import firestore

app = Flask(__name__)
CORS(app)

@app.route("/", methods=["GET"])
def metrics():
    try:
        uid = request.headers.get('X-UID')
        accounts = request.args.get('accounts')
        """ 
            Recupera as campanhas pelo accounts e campaign_id 
            - uid e accounts serão usados futuramente para validar se a campanha
            pertence de fato ao usuário
        """

        campaigns = request.args.get('accounts').split(',')
        firestore_client = firestore.Client()
        campaigns_ref = firestore_client.collection('campaigns').where(u'id', u'in', campaigns).stream()

        clicks = 0
        ctr = 0
        impressions =0
        conversions = 0
        conversions_rate = 0
        cost_per_conversion = 0
        click_cost = 0
        cpm_average = 0
        cpc_average = 0
        reach = 0
        views = 0
        number_of_campaigns = 0
        for doc in campaigns_ref:
            campaign = doc.to_dict()
            reach += float(campaign.get('reach'))
            cost_per_conversion += float(campaign.get('spend'))
            impressions += float(campaign.get('impressions'))
            for action in campaign.get('actions'):
                if action.get('action_type') == "link_click":
                    clicks += int(action.get('value'))

                if action.get('action_type') == "view_content":
                    views += int(action.get('value'))

            for cost_per_action in campaign.get('cost_per_action_type'):
                if cost_per_action.get('action_type') == "link_click":
                    click_cost += float(cost_per_action.get('value'))

            number_of_campaigns += 1

        response = {
            "clicks": clicks,
            "ctr": impressions/clicks if clicks else 0,
            "impressions": impressions,
            "conversions": conversions,
            "conversions_rate": conversions_rate,
            "cost_per_conversion": cost_per_conversion,
            "click_cost": click_cost,
            "cpm_average": (click_cost/impressions * 1000) / number_of_campaigns if number_of_campaigns else 0,
            "cpc_average": (click_cost/clicks) / number_of_campaigns if number_of_campaigns else 0,
            "reach": reach,
            "views": views,
        }
        return jsonify(response), 200
    except Exception as e:
        exception_type, exception_object, exception_traceback = sys.exc_info()
        line_number = exception_traceback.tb_lineno

        return f"An Error Occured: {e}, line: {line_number}"

if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0',port=os.environ.get('PORT', 80))

