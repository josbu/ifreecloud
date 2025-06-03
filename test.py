import os
import cloudscraper
import logging
from typing import Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# 从环境变量读取账号信息
USERNAME = os.getenv("FC_USERNAME")
#USERNAME="FFF"
PASSWORD = os.getenv("FC_PASSWORD")
MACHINE_ID = os.getenv("FC_MACHINE_ID")

# 参数校验
if not all([USERNAME, PASSWORD, MACHINE_ID]):
    logging.error("环境变量 FC_USERNAME / FC_PASSWORD / FC_MACHINE_ID 缺失，请配置后重试。")
    exit(1)

# URL 定义
LOGIN_URL = "https://freecloud.ltd/login"
CONSOLE_URL = "https://freecloud.ltd/member/index"
RENEW_URL = f"https://freecloud.ltd/server/detail/{MACHINE_ID}/renew"

# 公共请求头
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/122.0.0.0 Safari/537.36",
    "Referer": "https://freecloud.ltd/login",
    "Origin": "https://freecloud.ltd",
    "Content-Type": "application/x-www-form-urlencoded"
}

# 登录表单数据
LOGIN_PAYLOAD = {
    "username": USERNAME,
    "password": PASSWORD,
    "mobile": "",
    "captcha": "",
    "verify_code": "",
    "agree": "1",
    "login_type": "PASS",
    "submit": "1",
}

# 续费表单数据
RENEW_PAYLOAD = {
    "month": "1",         # 默认续费 1 个月
    "submit": "1",
    "coupon_id": 0        # 无优惠券
}


def login_session() -> Optional[cloudscraper.CloudScraper]:
    """
    使用 cloudscraper 模拟登录并返回会话对象
    """
    logging.info("🚀 正在尝试登录 FreeCloud...")
    scraper = cloudscraper.create_scraper(browser={"browser": "chrome", "platform": "windows", "mobile": False})

    try:
        resp = scraper.post(LOGIN_URL, data=LOGIN_PAYLOAD, headers=HEADERS, allow_redirects=True)
        resp.raise_for_status()

        if "退出登录" not in resp.text and "member/index" not in resp.text:
            logging.error("❌ 登录失败，请检查用户名或密码是否正确。")
            #raise RuntimeError("❌ 登录失败，请检查用户名或密码是否正确。")
            return None

        # 访问控制台主页以保持 session
        console_resp = scraper.get(CONSOLE_URL)
        console_resp.raise_for_status()
        logging.info("✅ 登录成功！")
        return scraper

    except Exception as e:
        logging.exception("❌ 登录过程中发生错误：")
        return None


def renew_server(session: cloudscraper.CloudScraper) -> None:
    """
    使用已登录的 session 发起续费请求
    """
    logging.info(f"🔄 正在尝试为服务器 {MACHINE_ID} 续费...")
    try:
        response = session.post(RENEW_URL, data=RENEW_PAYLOAD, headers=HEADERS)
        response.raise_for_status()

        try:
            data = response.json()
            message = data.get("msg", "")
            if message=='请在到期前3天后再续费':
                logging.warning(f"⚠️ 续费请求返回：{message}")
            else:
                logging.info(f"✅ 续费成功：{message}")         
        except Exception:
            logging.warning("⚠️ 返回内容不是 JSON，原始响应如下：")
            logging.warning(response.text)

    except Exception as e:
        logging.exception("❌ 续费请求失败：")


if __name__ == "__main__":
    session = login_session()
    if session:
        renew_server(session)
