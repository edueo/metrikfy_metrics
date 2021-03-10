import os
import sys
from flask import Flask, jsonify, escape, request
from flask_cors import CORS
from google.cloud import firestore
import requests
import pandas as pd

app = Flask(__name__)
CORS(app)

db = firestore.Client()

def clean_campaign(campaign):
    print(campaign)
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
        "reach" : float(campaign.get('reach')),
        "spend" : spend,
        "impressions" : float(campaign.get('impressions')),
        "frequency" : float(campaign.get('frequency')),
    }

@app.route("/", methods=["GET"])
def metrics():
    try:
        uid = request.headers.get('X-UID')
        accounts = request.args.get('accounts')

        campaigns = request.args.get('campaigns')

        if accounts:
            clean_accounts = []
            for account in accounts.split(','):
                clean_accounts.append(account.partition('_')[2])
            accounts = db.collection(u'ad_accounts').where(u'uid', u'==', uid).where(u'account_id', u'in', clean_accounts).stream()
        else:
            accounts = db.collection(u'ad_accounts').where(u'uid', u'==', uid).stream()


        raw_campaigns = []
        for doc in accounts:
            account = doc.to_dict()
            uid = account.get('uid')
            profile_id = account.get('profile_id')
            account_id = account.get('account_id')

            url = f'https://us-east1-etus-metrikfy-prod.cloudfunctions.net/metrikfy-facebookads-dev-getData?user_id={uid}&profile_id={profile_id}&account_id=act_{account_id}&level=campaign'
            requests.get(url)
            res = requests.get(url)
            if res.status_code == 200:
                for campaign in res.json():
                    campaign_id = campaign.get('campaign_id')
                    if campaigns:
                        if campaign_id in campaigns.split(','):
                            raw_campaigns.append(clean_campaign(campaign))
                    else:
                        raw_campaigns.append(clean_campaign(campaign))
        df = pd.DataFrame.from_records(raw_campaigns)
        return jsonify({
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
        }), 200

    except Exception as e:
        exception_type, exception_object, exception_traceback = sys.exc_info()
        line_number = exception_traceback.tb_lineno

        return f"An Error Occured: {e}, line: {line_number}"

if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0',port=os.environ.get('PORT', 80))

