from flask import Flask,request
from bleach import clean
from PIL import Image, ImageDraw, ImageFont
from base64 import b64encode
import random
import string
import json
import redis
app = Flask(__name__)
with open("msgbox.json") as f:
    config=json.load(f)
    rds = redis.StrictRedis(host=config["redis"]["ip"], port=config["redis"]["port"],
                        db=config["redis"]["db"], password=config["redis"]["password"])



@app.route('/api/')
def index():
    return json.dumps({'status': 'ok', 'message': 'Hello World!'}, ensure_ascii=False)


@app.route('/api/welcome/<string:name>')
def hello(name):
    return json.dumps({'status': 'ok', 'message': 'Hello ' + name}, ensure_ascii=False)


#POST /api/comment_s
@app.route('/api/comment_s', methods=['POST',"GET"])
def comment_s():
    try:
        comment_content=clean(request.json['content'],tags=["strong","em","mark","del","u","a","img","blockquote"],strip=True)
        cid="comment_"+("".join([random.choice(string.ascii_letters+string.digits) for i in range(random.randint(10,48))]))
        while rds.exists(cid):
            cid="comment_"+("".join([random.choice(string.ascii_letters+string.digits) for i in range(random.randint(10,48))]))
        rds[cid]=comment_content
        return json.dumps({'status': 'ok', 'message': 'Comment Commited', 'id':cid}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({'status': 'error', 'message': str(e)}, ensure_ascii=False)


@app.route('/api/comment_g/<string:id>')
def get_comment(id):
    if rds.exists(id):
        return json.dumps({'status': 'ok', 'message': 'Comment found', 'content': rds[id].decode(encoding="utf-8")}, ensure_ascii=False)
    else:
        return json.dumps({'status': 'error', 'message': 'Comment not found'}, ensure_ascii=False)

@app.route('/api/comment_d/<string:id>')
def delete_comment(id):
    if rds.exists(id):
        rds.delete(id)
        return json.dumps({'status': 'ok', 'message': 'Comment deleted'}, ensure_ascii=False)
    else:
        return json.dumps({'status': 'error', 'message': 'Comment not found'}, ensure_ascii=False)

@app.route('/api/data')
def get_data():
    ret = {}
    for a in rds.keys():
        ret[a.decode()]=rds[a.decode()].decode()
    return json.dumps({'status': 'ok', 'message': 'Data found', 'data': ret}, ensure_ascii=False)

@app.route('/api/clear_db/if_you_know_what_you_are_doing/<string:password>')
def clear_db(password):
    if password!="fuckUnvidia":
        return json.dumps({'status': 'error', 'message': 'Wrong password'}, ensure_ascii=False)
    for a in rds.keys():
        rds.delete(a)
    return json.dumps({'status': 'ok', 'message': 'Data cleared'}, ensure_ascii=False)

#验证码及图片生成
@app.route('/api/captcha/<string:id>')
def captcha(id):
    id=id+"_captcha"
    if rds.exists(id):
        return json.dumps({'status': 'error', 'message': 'Captcha already exists'}, ensure_ascii=False)
    captcha_content="".join([random.choice(string.ascii_letters+string.digits) for i in range(random.randint(4,8))])
    rds[id]=captcha_content
    img = Image.new('RGB', (200, 50), (255, 255, 255))
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 40)
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), captcha_content, (0, 0, 0), font=font)
    img.save('/tmp/captcha.png')
    return json.dumps({'status': 'ok', 'message': 'Captcha created', 'captcha': b64encode(open('/tmp/captcha.png', 'rb').read()).decode()}, ensure_ascii=False)

#验证码验证
@app.route('/api/captcha_check/<string:id>/<string:captcha>')
def captcha_check(id,captcha):
    id=id+"_captcha"
    if rds.exists(id):
        if rds[id].decode()==captcha:
            return json.dumps({'status': 'ok', 'message': 'Captcha correct'}, ensure_ascii=False)
        else:
            return json.dumps({'status': 'error', 'message': 'Captcha incorrect'}, ensure_ascii=False)
    else:
        return json.dumps({'status': 'error', 'message': 'Captcha not found'}, ensure_ascii=False)

if __name__ == "__main__":
    app.run(debug=True)
