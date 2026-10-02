#!/usr/bin/env python3
"""统一身份认证（Wisedu CAS）登录，并换取 Coremail 邮箱的 sid —— 只用于首次引导。

日常收发信**不需要**这个脚本：有了客户端专用密码就能直接走 IMAP/SMTP（见 mail.py）。
只有当邮箱里还没有专用密码、又必须进网页邮箱生成一条时才用它；
注意不要反复登录 CAS —— 短时间高频登录会触发统一身份认证风控甚至冻结账号。

用法：
    CSU_MAIL_ADDR=学号@csu.edu.cn CSU_CAS_USER=学号 CSU_CAS_PASS=密码 \
        python cas_login.py [--out mail_session.json] [--service <SSO 地址>]

产出：JSON（sid + cookies，权限 600），可直接喂给 create_apppw.mjs。
"""
import argparse
import base64
import json
import os
import random
import re
import sys

import requests
from bs4 import BeautifulSoup
from Crypto.Cipher import AES

CAS = os.environ.get("CSU_CAS_URL", "https://ca.csu.edu.cn/authserver/login")
SERVICE = os.environ.get("CSU_MAIL_SSO", "https://mail.csu.edu.cn/coremail/cmcu_addon/sso.jsp")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
CHARS = "ABCDEFGHJKMNPQRSTWXYZabcdefhijkmnprstwxyz2345678"


def _rand(n: int) -> str:
    return "".join(random.choice(CHARS) for _ in range(n))


def encrypt_password(password: str, salt: str) -> str:
    """与 CAS 页面 static/common/encrypt.js 的 encryptAES 一致：
    明文 = 64 位随机串 + 密码，AES-CBC（key = pwdEncryptSalt，iv = 16 位随机串），PKCS7，Base64。"""
    text = _rand(64) + password
    pad_len = AES.block_size - len(text) % AES.block_size
    text += pad_len * chr(pad_len)
    cipher = AES.new(salt.encode(), AES.MODE_CBC, _rand(16).encode())
    return base64.b64encode(cipher.encrypt(text.encode())).decode()


def cas_login(user: str, password: str, service: str = SERVICE) -> requests.Session:
    s = requests.Session()
    s.headers["User-Agent"] = UA
    page = s.get(CAS, params={"service": service}, timeout=20)
    div = BeautifulSoup(page.text, "lxml").find(id="pwdLoginDiv")
    if div is None:
        raise RuntimeError("CAS 页面结构变化，取不到 pwdLoginDiv（可能要求验证码）")
    resp = s.post(CAS, params={"service": service}, timeout=25, data={
        "username": user,
        "password": encrypt_password(password, div.find(id="pwdEncryptSalt")["value"]),
        "passwordText": "", "_eventId": "submit", "cllt": "userNameLogin",
        "dllt": "generalLogin", "lt": "",
        "execution": div.find(id="execution")["value"], "rmShown": "1",
    })
    if "/authserver/login" in resp.url and "ticket" not in resp.url:
        raise RuntimeError("统一身份认证登录失败（账号或密码错误，或触发风控/需要验证码）")
    return s


def mail_sid(s: requests.Session, resp) -> str:
    m = re.search(r"sid=([A-Za-z0-9_\-]+)", resp.url)
    if not m:
        r = s.get("https://mail.csu.edu.cn/coremail/XT5/index.jsp", allow_redirects=True, timeout=25)
        m = (re.search(r"sid=([A-Za-z0-9_\-]+)", r.url)
             or re.search(r'name="sid"\s+value="([^"]+)"', r.text))
    if not m:
        raise RuntimeError("SSO 回调里没有 sid")
    return m.group(1)


def main():
    ap = argparse.ArgumentParser(description="CAS 登录换邮箱 sid（仅引导时使用）")
    ap.add_argument("--user", default=os.environ.get("CSU_CAS_USER", ""))
    ap.add_argument("--password", default=os.environ.get("CSU_CAS_PASS", ""))
    ap.add_argument("--service", default=SERVICE)
    ap.add_argument("--out", default="mail_session.json")
    a = ap.parse_args()
    if not a.user or not a.password:
        sys.exit("需要 CSU_CAS_USER / CSU_CAS_PASS（或用 --user/--password）")

    s = cas_login(a.user, a.password, a.service)
    resp = s.get(a.service, timeout=25)
    sid = mail_sid(s, resp)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump({"sid": sid, "cookies": s.cookies.get_dict()}, f)
    os.chmod(a.out, 0o600)
    print(f"sid 已写入 {a.out}（{sid[:4]}…{sid[-4:]}），接下来可用 create_apppw.mjs 生成客户端专用密码")


if __name__ == "__main__":
    main()
