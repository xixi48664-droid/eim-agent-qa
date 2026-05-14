import time
import requests
from config import HEADERS, REQUEST_DELAY, RETRY_TIMES

def fetch(url, params=None, method="GET", retry=RETRY_TIMES):
    """带重试和延迟的请求"""
    time.sleep(REQUEST_DELAY)
    for i in range(retry):
        try:
            if method.upper() == "GET":
                resp = requests.get(url, params=params, headers=HEADERS, timeout=30)
            else:
                resp = requests.post(url, data=params, headers=HEADERS, timeout=30)
            if resp.status_code == 200:
                return resp
        except Exception as e:
            print(f"请求失败 ({i+1}/{retry}): {e}")
    return None