from flask import (
    Blueprint,
    Flask,
    request,
    url_for,
)

from jinja2 import Template

text = """
<h1>{{ ctx }}</h1>
"""

def create_blueprint(prefix):
    bp = Blueprint('main', __name__, url_prefix=prefix)
    
    @bp.route('/')
    def index():
        print(f"{request.path=}\n{request.full_path=}")
        u = url_for('.hello')
        print(f"{u}")
        re_url = u.removeprefix("/")
        print(f"{type(re_url)=} {re_url=}")
        temp = Template(text)
        return temp.render(ctx=re_url)

    @bp.route('/hello')
    def hello():
        return f'地这里返回首页：{url_for("/")}'
    
    return bp




app = Flask(__name__)

app.register_blueprint(create_blueprint("/totp"))

app.run()

