
from urllib import parse

import webview
#webview.create_window('Hello world', 'https://pywebview.flowrl.com/hello')


# client_id为minecraft在azure的服务名，response_type为返回结果类型，scope为验证服务的类型，redirect_uri为返回的重定向链接。
URL="https://login.live.com/oauth20_authorize.srf"
CLIENT_ID="00000000402b5328"

param={
    "client_id": CLIENT_ID,
    "response_type": "code",
    "grant_type": "authorization_code",
    "redirect_uri": "https://login.live.com/oauth20_desktop.srf",
    "scope": "service::user.auth.xboxlive.com::MBI_SSL"
}
data = parse.urlencode(param)

webview.create_window('登录微软账号', URL + "?" + data)

def get_current_url(window):
    print(window.get_current_url())

webview.start()

