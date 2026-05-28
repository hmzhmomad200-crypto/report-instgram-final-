import aiohttp
import re
from typing import Optional, Dict
from utils.logger import logger

REPORT_TYPES = {
    "1": {"name": "Suicide or Self Injury", "selected_tag_types": '["suicide_or_self_harm_concern-suicide_or_self_injury"]', "jazoest": "22738"},
    "2": {"name": "Spam", "selected_tag_types": '["ig_spam_v3"]', "jazoest": "22738"},
    "3": {"name": "I Don't Like It", "selected_tag_types": '["ig_i_dont_like_it_v3"]', "jazoest": "22738"},
    "4": {"name": "Threat to Share Nude Images (U18)", "selected_tag_types": '["adult_content-threat_to_share_nude_images-u18-yes"]', "jazoest": "22738"},
    "5": {"name": "Harassment or Abuse (Me, U18)", "selected_tag_types": '["harrassment_or_abuse-harassment-me-u18-yes"]', "jazoest": "22738"},
    "6": {"name": "Annoying or Spam (Misleading)", "selected_tag_types": '["misleading_annoying_or_scam-annoying_or_spam"]', "jazoest": "22738"},
    "7": {"name": "Eating Disorder", "selected_tag_types": '["suicide_or_self_harm_concern-eating_disorder"]', "jazoest": "22738"},
    "8": {"name": "Credible Threat (Violence)", "selected_tag_types": '["violent_hateful_or_disturbing-credible_threat"]', "jazoest": "22738"},
    "9": {"name": "Terrorism or Organized Crime", "selected_tag_types": '["violent_hateful_or_disturbing-terrorism_or_organized_crime"]', "jazoest": "22738"},
    "10": {"name": "Human Trafficking", "selected_tag_types": '["human_trafficking"]', "jazoest": "22738"},
    "11": {"name": "Sexual Exploitation (Under 18)", "selected_tag_types": '["violence_hate_or_exploitation-sexual_exploitation-yes"]', "jazoest": "22738"},
    "12": {"name": "Hate Speech or Symbols", "selected_tag_types": '["violent_hateful_or_disturbing-promotes_hate-hate_speech_or_symbols"]', "jazoest": "22738"},
    "13": {"name": "Violence", "selected_tag_types": '["violent_hateful_or_disturbing-violence"]', "jazoest": "22738"},
    "14": {"name": "Animal Abuse", "selected_tag_types": '["violent_hateful_or_disturbing-animal_abuse"]', "jazoest": "22738"},
    "15": {"name": "Violence - Death or Severe Injury", "selected_tag_types": '["violent_hateful_or_disturbing-violence_death_or_severe_injury"]', "jazoest": "22738"},
    "16": {"name": "High Risk Drugs", "selected_tag_types": '["selling_or_promoting_restricted_items-drugs-high-risk"]', "jazoest": "22738"},
    "17": {"name": "Prescription Drugs", "selected_tag_types": '["selling_or_promoting_restricted_items-drugs-prescription"]', "jazoest": "22738"},
    "18": {"name": "Other Drugs", "selected_tag_types": '["selling_or_promoting_restricted_items-drugs-other"]', "jazoest": "22738"},
    "19": {"name": "Weapons Sales", "selected_tag_types": '["selling_or_promoting_restricted_items-weapons"]', "jazoest": "22738"},
    "20": {"name": "Animal Sales", "selected_tag_types": '["selling_or_promoting_restricted_items-animals"]', "jazoest": "22738"},
    "21": {"name": "Gambling", "selected_tag_types": '["ig_gambling"]', "jazoest": "22738"},
    "22": {"name": "Tobacco", "selected_tag_types": '["ig_tobacco"]', "jazoest": "22738"},
    "23": {"name": "Alcohol", "selected_tag_types": '["ig_alcohol"]', "jazoest": "22738"},
    "24": {"name": "Threat to Share Nude Images (U18) Path2", "selected_tag_types": '["adult_content-threat_to_share_nude_images-u18-yes"]', "jazoest": "22738"},
    "25": {"name": "Prostitution", "selected_tag_types": '["adult_content-prostitution"]', "jazoest": "22738"},
    "26": {"name": "Sexual Exploitation (Under 18) Path2", "selected_tag_types": '["violence_hate_or_exploitation-sexual_exploitation-yes"]', "jazoest": "22738"},
    "27": {"name": "Nudity or Sexual Activity", "selected_tag_types": '["adult_content-nudity_or_sexual_activity"]', "jazoest": "22738"},
    "28": {"name": "Financial Scam or Investment Fraud", "selected_tag_types": '["ig_scam_financial_investment"]', "jazoest": "22738"},
    "29": {"name": "Identity Theft Scam", "selected_tag_types": '["ig_scam_identity_theft"]', "jazoest": "22738"},
    "30": {"name": "Fake Goods/Services Scam", "selected_tag_types": '["ig_scam_fake_goods_services"]', "jazoest": "22738"},
    "31": {"name": "Physical Threats Scam", "selected_tag_types": '["ig_scam_physical_threats"]', "jazoest": "22738"},
    "32": {"name": "Suspicious Contact Scam", "selected_tag_types": '["ig_suspicious_contact"]', "jazoest": "22738"},
    "33": {"name": "Suspicious Links", "selected_tag_types": '["ig_suspicious_links"]', "jazoest": "22738"},
    "34": {"name": "Impersonation (Me)", "selected_tag_types": '["ig_user_impersonation_me"]', "action_type": "2", "jazoest": "22738"},
}

class InstagramReporter:
    def __init__(self):
        self.base_url = "https://www.instagram.com"
        self.api_path = "/api/v1/web/reports/get_frx_prompt/"
        self.headers = {
            "Host": "www.instagram.com",
            "X-ASBD-ID": "359341",
            "Accept": "*/*",
            "X-Requested-With": "XMLHttpRequest",
            "Sec-Fetch-Site": "same-origin",
            "X-IG-Max-Touch-Points": "5",
            "X-IG-App-ID": "1217981644879628",
            "X-Instagram-AJAX": "1038695294",
            "Sec-Fetch-Mode": "cors",
            "Origin": "https://www.instagram.com",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.3 Mobile/15E148 Safari/604.1",
            "Sec-Fetch-Dest": "empty",
            "Accept-Language": "ar",
            "Priority": "u=3, i",
            "Accept-Encoding": "identity",
            "Connection": "keep-alive"
        }

    async def validate_session(self, session_id: str) -> Optional[str]:
        if not session_id:
            return None
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                cookies = {'sessionid': session_id}
                async with session.get(self.base_url + '/', headers=self.headers, cookies=cookies) as resp:
                    if resp.status != 200:
                        return None
                    text = await resp.text()
                    csrf_token = None
                    match = re.search(r'"csrf_token":"([^"]+)"', text)
                    if match:
                        csrf_token = match.group(1)
                    match = re.search(r'"username":"([^"]+)"', text)
                    if match:
                        return match.group(1)
                    match = re.search(r'{"username":"([^"]+)"', text)
                    if match:
                        return match.group(1)
                    if csrf_token:
                        headers2 = self.headers.copy()
                        headers2["X-CSRFToken"] = csrf_token
                        headers2["Referer"] = self.base_url + "/"
                        async with session.get(f"{self.base_url}/api/v1/accounts/current_user/?edit=true", headers=headers2, cookies=cookies) as api_resp:
                            if api_resp.status == 200:
                                data = await api_resp.json()
                                if 'user' in data and data.get('status') == 'ok':
                                    return data['user'].get('username')
                    return None
        except Exception as e:
            logger.error(f"Validate session error: {e}")
            return None

    async def get_user_id(self, username: str, session_id: str = None) -> Optional[str]:
        try:
            timeout = aiohttp.ClientTimeout(total=15)
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                cookies = {'sessionid': session_id} if session_id else {}
                headers = {
                    "User-Agent": self.headers["User-Agent"],
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "ar",
                    "Accept-Encoding": "identity"
                }
                # Try API first
                api_headers = headers.copy()
                api_headers["X-IG-App-ID"] = "1217981644879628"
                async with session.get(f"https://i.instagram.com/api/v1/users/web_profile_info/?username={username}", headers=api_headers, cookies=cookies) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if 'data' in data and 'user' in data['data']:
                            return str(data['data']['user']['id'])
                # Fallback to web scraping
                async with session.get(f"https://www.instagram.com/{username}/", headers=headers, cookies=cookies) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        match = re.search(r'"profilePage_(\d+)"', text)
                        if match:
                            return match.group(1)
                        match = re.search(r'"id":"(\d+)"', text)
                        if match:
                            return match.group(1)
                return None
        except Exception as e:
            logger.error(f"Get user ID error: {e}")
            return None

    async def report(self, target_user_id: str, session_id: str, report_type: Dict) -> bool:
        if not session_id or not target_user_id:
            return False
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                cookies = {'sessionid': session_id}
                # get csrf
                async with session.get(self.base_url + '/', headers=self.headers, cookies=cookies) as home_resp:
                    if home_resp.status != 200:
                        return False
                    text = await home_resp.text()
                    csrf_token = None
                    match = re.search(r'"csrf_token":"([^"]+)"', text)
                    if match:
                        csrf_token = match.group(1)
                    else:
                        return False
                headers = self.headers.copy()
                headers["X-CSRFToken"] = csrf_token
                headers["Referer"] = self.base_url + "/"
                headers["Content-Type"] = "application/x-www-form-urlencoded"
                # get context
                data_ctx = {
                    'container_module': 'profilePage',
                    'entry_point': '1',
                    'location': '2',
                    'object_id': target_user_id,
                    'object_type': '5',
                    'frx_prompt_request_type': '1',
                }
                async with session.post(self.base_url + self.api_path, data=data_ctx, headers=headers, cookies=cookies) as ctx_resp:
                    if ctx_resp.status != 200:
                        return False
                    j = await ctx_resp.json()
                    context = None
                    if 'response' in j and 'context' in j['response']:
                        context = j['response']['context']
                    elif 'context' in j:
                        context = j['context']
                    if not context:
                        return False
                final_data = {
                    'container_module': 'profilePage',
                    'entry_point': '1',
                    'location': '2',
                    'object_id': target_user_id,
                    'object_type': '5',
                    'context': context,
                    'selected_tag_types': report_type['selected_tag_types'],
                    'frx_prompt_request_type': '2',
                    'jazoest': report_type['jazoest']
                }
                if 'action_type' in report_type:
                    final_data['action_type'] = report_type['action_type']
                async with session.post(self.base_url + self.api_path, data=final_data, headers=headers, cookies=cookies) as final_resp:
                    if final_resp.status == 200:
                        result = await final_resp.json()
                        return result.get('status') == 'ok'
                    return False
        except Exception as e:
            logger.error(f"Report error: {e}")
            return False