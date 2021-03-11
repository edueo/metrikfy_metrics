import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from google.cloud import firestore
from datetime import datetime, timedelta
import sys
import pandas as pd

app = Flask(__name__)
CORS(app)

db = firestore.Client()


def clean_campaign(campaign):
    clicks = 0
    views = 0
    conversions = 0
    click_cost = 0

    if campaign.get('actions'):
        for action in campaign.get('actions'):
            if "click" in action.get('action_type'):
                clicks = action.get('value')

            if "view" in action.get('action_type'):
                views = action.get('value')

            if action.get("action_type") == "complete_registration" \
                    or "purchase" in action.get('action_type'):
                conversions = action.get("value")

    if campaign.get('cost_per_action_type'):
        for cost_per_action in campaign.get('cost_per_action_type'):
            if "click" in cost_per_action.get('action_type'):
                click_cost = cost_per_action.get('value')
    spend = float(campaign.get("spend"))
    clicks = int(clicks)
    views = int(views)
    impressions = float(campaign.get('impressions'))
    conversions = float(conversions)
    click_cost = float(click_cost)
    return {
        "clicks": clicks,
        "ctr": clicks / views if views else 0,
        "conversions_rate": (conversions / impressions) * 100 if impressions else 0,
        "cost_per_conversion": spend / conversions if conversions else 0,
        "click_cost": click_cost / clicks if clicks else 0,
        "cpm_average": (click_cost / impressions * 1000),
        "cpc_average": (click_cost / clicks if clicks else 0),
        "views": int(views),
        "conversions": float(conversions),
        "reach": float(campaign.get('reach')),
        "spend": spend,
        "impressions": float(campaign.get('impressions')),
        "frequency": float(campaign.get('frequency')),
    }


@app.route("/", methods=["GET"])
def metrics():
    try:

        uid = request.headers.get('X-UID')

        if request.args.get('campaigns'):
            campaigns = request.args.get('campaigns').split(',')
        else:
            campaigns = None

        if request.args.get('start_date'):
            start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d')
        else:
            start_date = datetime.strptime(datetime.today().strftime("%Y-%m-%d"), '%Y-%m-%d')

        if request.args.get('end_date'):
            end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d')
        else:
            end_date = datetime.strptime(datetime.today().strftime("%Y-%m-%d"), '%Y-%m-%d')

        delta = timedelta(days=1)
        result = []
        raw_campaigns = []

        while start_date <= end_date:
            print(start_date)
            if request.args.get('accounts'):
                accounts = request.args.get('accounts').split(',')
                for account in accounts:
                    facebookads = db.collection(u'facebookads').document(account).collection(
                        start_date.date().strftime("%Y-%m-%d")).stream()
                    for doc in facebookads:
                        campaign = doc.to_dict()
                        if campaigns:
                            if campaign.get('uid') == uid and campaign.get('campaign_id') in campaigns:
                                raw_campaigns.append(clean_campaign(campaign))
                        else:
                            if campaign.get('uid') == uid:
                                raw_campaigns.append(clean_campaign(campaign))
            else:
                accounts = db.collection('ad_accounts').where(u'uid', u'==', uid).stream()
                for doc_1 in accounts:
                    account = doc_1.to_dict()
                    account_id = f'act_{account.get("account_id")}'
                    facebookads = db.collection(u'facebookads').document(account_id).collection(
                        start_date.date().strftime("%Y-%m-%d")).stream()
                    for doc in facebookads:
                        campaign = doc.to_dict()
                        if campaigns:
                            if campaign.get('uid') == uid and campaign.get('campaign_id') in campaigns:
                                raw_campaigns.append(clean_campaign(campaign))
                        else:
                            if campaign.get('uid') == uid:
                                raw_campaigns.append(clean_campaign(campaign))

            start_date += delta
        if raw_campaigns:
            df = pd.DataFrame.from_records(raw_campaigns)
            aggregate = {
                "clicks": int(df['clicks'].sum()),
                "ctr": float(df['ctr'].mean()),
                "conversions_rate": float(df['conversions_rate'].mean()),
                "conversions": int(df['conversions'].sum()),
                "cost_per_conversion": float(df['cost_per_conversion'].mean()),
                "cpc_average": float(df['cpc_average'].mean()),
                "cpm_average": float(df['cpm_average'].mean()),
                "frequency": float(df['frequency'].mean()),
                "impressions": int(df['impressions'].sum()),
                "reach": float(df['reach'].sum()),
                "spend": float(df['spend'].sum()),
                "views": int(df['views'].sum())
            }
        else:
            aggregate = {
                "clicks": 0,
                "ctr": 0,
                "conversions_rate": 0,
                "conversions": 0,
                "cost_per_conversion": 0,
                "cpc_average": 0,
                "cpm_average": 0,
                "frequency": 0,
                "impressions": 0,
                "reach": 0,
                "spend": 0,
                "views": 0
            }
        result.append(aggregate)
        return jsonify(result), 200

    except Exception as e:
        exception_type, exception_object, exception_traceback = sys.exc_info()
        line_number = exception_traceback.tb_lineno
        return f"An Error Occured: {e}, line: {line_number}"


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=os.environ.get('PORT', 80))
