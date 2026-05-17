import json
import os
import sys
import urllib.request
import urllib.error

from _weread.constants import API_URL, SKILL_VERSION


class WereadAPI:
    def __init__(self):
        self.key = os.environ.get("WEREAD_API_KEY", "")
        if not self.key:
            # Try .env file
            for env_path in [
                os.path.join(os.getcwd(), ".env"),
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"),
            ]:
                if os.path.isfile(env_path):
                    with open(env_path) as f:
                        for line in f:
                            line = line.strip()
                            if line.startswith("WEREAD_API_KEY="):
                                self.key = line.split("=", 1)[1].strip()
                                break
                    if self.key:
                        break
        if not self.key:
            print("错误: WEREAD_API_KEY 未设置，请 export WEREAD_API_KEY=***", file=sys.stderr)
            sys.exit(1)

    def call(self, api_name, **params):
        """调用 API，自动处理 errcode 和 upgrade_info。"""
        body = {"api_name": api_name, "skill_version": SKILL_VERSION, **params}
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(API_URL, data=data, headers={
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
        })
        try:
            resp = urllib.request.urlopen(req, timeout=30)
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            print(f"HTTP {e.code}: {err_body}", file=sys.stderr)
            sys.exit(1)
        except urllib.error.URLError as e:
            print(f"网络错误: {e.reason}", file=sys.stderr)
            sys.exit(1)

        result = json.loads(resp.read())

        if "upgrade_info" in result:
            msg = result.get("upgrade_info", {}).get("message", "技能版本需升级")
            print(f"⚠️  {msg}", file=sys.stderr)
            print("请根据指引升级 weread skill 后重试。", file=sys.stderr)
            sys.exit(2)

        errcode = result.get("errcode", 0)
        if errcode != 0:
            errmsg = result.get("errmsg", "未知错误")
            print(f"API 错误 (errcode={errcode}): {errmsg}", file=sys.stderr)
            sys.exit(1)

        return result
