# app.py

from flask import Flask,jsonify,redirect,request
import os
import json

def load_config():
    with open('config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

config = load_config()
app = Flask(__name__)
app.config["SECRET_KEY"] = config['app']['secret_key']


@app.errorhandler(404)
async def error_404(error):
    return "頁面不存在",404

@app.errorhandler(400)
async def error_400(error):
    return jsonify({"code":400,"message":"資料有誤"}),400

@app.errorhandler(500)
async def error_500(error):
    return "發生了點錯誤，請稍後再試，或重新整理頁面。<br><a href='/logout'>登出</a>", 500

print("> 正在註冊檔案")
views_dir = os.path.join(os.path.dirname(__file__), 'views')
for filename in os.listdir(views_dir):
    if filename.endswith('.py') and filename != '__init__.py':
        module_name = filename[:-3]
        module = __import__(f'views.{module_name}', fromlist=['*'])
        print(f"  L {module_name}.py")
        if hasattr(module, 'home'):
            app.register_blueprint(module.home)
print("> 已註冊檔案")

print(app.url_map)

if __name__ == "__main__":
    app.run(host=config['app']['host'], port=config['app']['port'], debug=config['app']['debug'])