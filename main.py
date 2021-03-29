import json
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
batch = db.batch()

# https://developers.facebook.com/docs/marketing-api/reference/ads-action-stats/
action_type = [
    'app_custom_event.fb_mobile_achievement_unlocked',
    'app_custom_event.fb_mobile_activate_app',
    'app_custom_event.fb_mobile_add_payment_info',
    'app_custom_event.fb_mobile_add_to_cart',
    'app_custom_event.fb_mobile_add_to_wishlist',
    'app_custom_event.fb_mobile_complete_registration',
    'app_custom_event.fb_mobile_content_view',
    'app_custom_event.fb_mobile_initiated_checkout',
    'app_custom_event.fb_mobile_level_achieved',
    'app_custom_event.fb_mobile_purchase',
    'app_custom_event.fb_mobile_rate',
    'app_custom_event.fb_mobile_search',
    'app_custom_event.fb_mobile_spent_credits',
    'app_custom_event.fb_mobile_tutorial_completion',
    'app_custom_event.other',
    'app_install',
    'app_use',
    'checkin',
    'comment',
    'credit_spent',
    'games.plays',
    'landing_page_view',
    'like',
    'link_click',
    'mobile_app_install',
    'offsite_conversion.fb_pixel_add_payment_info',
    'offsite_conversion.fb_pixel_add_to_cart',
    'offsite_conversion.fb_pixel_add_to_wishlist',
    'offsite_conversion.fb_pixel_complete_registration',
    'offsite_conversion.fb_pixel_custom',
    'offsite_conversion.fb_pixel_initiate_checkout',
    'offsite_conversion.fb_pixel_lead',
    'offsite_conversion.fb_pixel_purchase',
    'offsite_conversion.fb_pixel_search',
    'offsite_conversion.fb_pixel_view_content',
    'onsite_conversion.flow_complete',
    'onsite_conversion.messaging_block',
    'onsite_conversion.messaging_conversation_started_7d',
    'onsite_conversion.messaging_first_reply',
    'onsite_conversion.post_save',
    'onsite_conversion.purchase',
    'purchase',
    'outbound_click',
    'photo_view',
    'post',
    'post_reaction',
    'video_view',
    'contact_total',
    'contact_website',
    'contact_mobile_app',
    'contact_offline',
    'customize_product_total',
    'customize_product_website',
    'customize_product_mobile_app',
    'customize_product_offline',
    'donate_total',
    'donate_website',
    'donate_on_facebook',
    'donate_mobile_app',
    'donate_offline',
    'find_location_total',
    'find_location_website',
    'find_location_mobile_app',
    'find_location_offline',
    'schedule_total',
    'schedule_website',
    'schedule_mobile_app',
    'schedule_offline',
    'start_trial_total',
    'start_trial_website',
    'start_trial_mobile_app',
    'start_trial_offline',
    'submit_application_total',
    'submit_application_website',
    'submit_application_mobile_app',
    'submit_application_offline',
    'submit_application_on_facebook',
    'subscribe_total',
    'subscribe_website',
    'subscribe_mobile_app',
    'subscribe_offline',
    'recurring_subscription_payment_total',
    'recurring_subscription_payment_website',
    'recurring_subscription_payment_mobile_app',
    'recurring_subscription_payment_offline',
    'cancel_subscription_total',
    'cancel_subscription_website',
    'cancel_subscription_mobile_app',
    'cancel_subscription_offline',
    'ad_click_mobile_app',
    'ad_impression_mobile_app',
    'click_to_call_call_confirm',
    'page_engagement',
    'post_engagement',
    'onsite_conversion.lead_grouped',
    'lead',
    'leadgen_grouped',
    'omni_app_install',
    'omni_purchase',
    'omni_add_to_cart',
    'omni_complete_registration',
    'omni_view_content',
    'omni_search',
    'omni_initiated_checkout',
    'omni_achievement_unlocked',
    'omni_activate_app',
    'omni_level_achieved',
    'omni_rate',
    'omni_spend_credits',
    'omni_tutorial_completion',
    'omni_custom'
]


def format_metrics(records):

    df = pd.DataFrame.from_records(records)

    for action in action_type:
        if action in df.columns:
            df[action] = df[action].astype(float)
        cost_per = f'cost_per_{action}'
        if cost_per in df.columns:
            df[cost_per] = df[cost_per].astype(float)

    return df.agg(['sum', 'min', 'mean', 'median']).to_json(orient='columns')


@app.route("/", methods=["GET"])
def metrics():
    try:
        uid = request.headers.get('X-UID')
        if not uid:
            return jsonify("BAD REQUEST"), 400
        accounts = request.args.get('accounts').split(',') if request.args.get('accounts') is not None else None
        campaigns = request.args.get('campaigns').split(',') if request.args.get('campaigns') is not None else None
        start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d') if request.args.get(
            'start_date') else datetime.strptime(datetime.today().strftime("%Y-%m-%d"), '%Y-%m-%d')
        end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d') if request.args.get(
            'end_date') else datetime.strptime(datetime.today().strftime("%Y-%m-%d"), '%Y-%m-%d')

        if start_date == end_date:
            start_date = end_date - timedelta(days=6)

        delta = timedelta(days=1)
        accounts_ref = db.collection(u'metrikfy_accounts').document(uid).collection('facebookads').get()
        result = []

        while start_date <= end_date:
            now = start_date.date().strftime("%Y-%m-%d")
            for account in accounts_ref:
                account_id = account.id
                if accounts and account_id not in accounts:
                    continue

                campaigns_ref = db.collection('metrikfy_accounts').document(uid).collection('facebookads').document(
                    account_id).collection('campaigns').get()

                for campaign in campaigns_ref:
                    campaign_id = campaign.id

                    if campaigns and campaign_id not in campaigns:
                        continue

                    metrics_ref = db.collection('metrikfy_accounts').document(uid).collection(
                        'facebookads').document(account_id).collection('campaigns').document(
                        campaign_id).collection('metrics').document(now).get()

                    metrics_dict = metrics_ref.to_dict()

                    if metrics_dict is not None:
                        result.append(metrics_dict)
            start_date += delta
        output = json.loads(format_metrics(result)) if result else result
        return jsonify(output), 200

    except Exception as e:
        exception_type, exception_object, exception_traceback = sys.exc_info()
        line_number = exception_traceback.tb_lineno
        return f"An Error Occured: {e}, line: {line_number}"


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=os.environ.get('PORT', 80))
