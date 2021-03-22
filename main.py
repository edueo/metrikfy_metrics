import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from google.cloud import firestore
from datetime import datetime, timedelta
import sys
import pandas as pd
import requests

app = Flask(__name__)
CORS(app)

db = firestore.Client()
batch = db.batch()


def format_metrics(raw_campaigns):
    if not raw_campaigns:
        return {}

    df = pd.DataFrame.from_records(raw_campaigns)
    return {
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


def get_accounts(uid, accounts=None):
    result = []
    accounts_ref = db.collection('contas_metrikfy').document(uid).collection('contas_facebook').stream()
    for doc in accounts_ref:
        account = doc.to_dict()
        if accounts:
            if account.get('id') in accounts:
                result.append(account)
        else:
            result.append(account)
    return result


@app.route("/", methods=["GET"])
def metrics():
    try:
        uid = request.headers.get('X-UID')
        accounts = get_accounts(uid, request.args.get('accounts'))
        campaigns = request.args.get('campaigns').split(',') if request.args.get('campaigns') else None
        start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d') if request.args.get(
            'start_date') else datetime.strptime(datetime.today().strftime("%Y-%m-%d"), '%Y-%m-%d')
        end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d') if request.args.get(
            'end_date') else datetime.strptime(datetime.today().strftime("%Y-%m-%d"), '%Y-%m-%d')
        raw_campaigns = []

        uid_ref = db.collection(u'contas_metrikfy').document(uid)
        if start_date == end_date:
            start_date = end_date - timedelta(days=6)

        delta = timedelta(days=1)

        while start_date <= end_date:
            for account in accounts:
                account_ref = uid_ref.collection('contas_facebook').document(account.get('id'))
                now = start_date.date().strftime("%Y-%m-%d")
                url = f'https://us-east1-etus-metrikfy-prod.cloudfunctions.net/metrikfy-facebookads-dev-getData?user_id={uid}&profile_id={account.get("profile_id")}&account_id={account.get("id")}&level=campaign&date={now}'
                res = requests.get(url)
                if res.status_code == 200:
                    for campaign in res.json():
                        if campaigns:
                            if campaign.get('campaign_id') in campaigns:
                                metrics_ref = account_ref.collection('metricas').document(
                                    campaign.get('campaign_id'))
                                result_ref = metrics_ref.collection('consolidado').document(now)
                                batch.set(result_ref, clean_campaign(campaign))
                                raw_campaigns.append(clean_campaign(campaign))
                        else:
                            metrics_ref = account_ref.collection('metricas').document(campaign.get('campaign_id'))
                            result_ref = metrics_ref.collection('consolidado').document(now)
                            batch.set(result_ref, clean_campaign(campaign))
                            raw_campaigns.append(clean_campaign(campaign))
            start_date += delta
        batch.commit()
        result = format_metrics(raw_campaigns)
        return jsonify(result), 200

    except Exception as e:
        exception_type, exception_object, exception_traceback = sys.exc_info()
        line_number = exception_traceback.tb_lineno
        return f"An Error Occured: {e}, line: {line_number}"


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=os.environ.get('PORT', 80))
