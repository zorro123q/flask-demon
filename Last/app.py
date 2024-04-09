from datetime import datetime

from flask import Flask, render_template, request, session, make_response
import re
import random
import logging

import orms
from get_captcha import get_captcha_code_and_content
from db import Database
import config
from extensions import register_extension, db
from orms import StudentORM
app = Flask(__name__)
app.secret_key = 'notes.zhengxinonly.com'
app.config.from_object(config)
register_extension(app)

@app.route('/')
def index_view():
    return render_template('index.html')


@app.route('/register')
def register_view():
    return render_template('register.html')


@app.route('/login')
def login_view():
    return render_template('login.html')

@app.post('/api/send_register_sms')
def send_register_sms():
    # 1. 解析前端传递过来的数据
    data = request.get_json()
    mobile = data['mobile']
    # 2. 校验手机号码
    pattern = r'^1[3-9]\d{9}$'
    ret = re.match(pattern, mobile)
    if not ret:
        return {
            'message': '电话号码不符合格式',
            'code': -1
        }

    # 3. 发送短信验证码，并记录
    session['mobile'] = mobile
    # 3.1 生成随机验证码
    code = random.choices('123456789', k=6)
    session['code'] = ''.join(code)
    logging.warning(''.join(code))
    return {
        'message': '发送短信成功',
        'code': 0
    }
@app.post('/api/register')
def register_api():
    # 1. 解析前端传递过来的数据
    data = request.get_json()
    vercode = data['vercode']
    vercode2 = session['code']
    if vercode != vercode2:
        return {
            'message': '短信验证码错误',
            'code': -1
        }

    nickname = data['nickname']
    mobile = data['mobile']
    password = data['password']
    if not all([nickname, mobile, password]):
        return {
            'message': '数据缺失',
            'code': -1
        }
    Database().insert(nickname, mobile, password)
    return {
        'message': '注册用户成功',
        'code': 0
    }
@app.get('/get_captcha')
def get_captcha_view():
    # 1. 获取参数
    captcha_uuid = request.args.get("captcha_uuid")
    # 2. 生成验证码
    code, content = get_captcha_code_and_content()

    # 3. 记录数据到数据库（用session代替）
    session['code'] = code
    resp = make_response(content)  # 读取图片的二进制数据做成响应体
    resp.content_type = "image/png"
    # 4. 错误处理

    # 5. 响应返回
    return resp

@app.post('/api/login')
def login_api():
    data = request.get_json()
    ret = Database().search(data['mobile'])
    code = session['code']
    if code != data['captcha']:
        return {
            'message': '验证码错误',
            'code': -1
        }
    if not ret:
        return {
            'message': '用户不存在',
            'code': -1
        }
    pwd = ret[0]
    if pwd != data['password']:
        return {
            'message': '用户密码错误',
            'code': -1
        }
    session['is_login'] = True  # 记录用户登录
    return {
        'message': '用户登录成功',
        'code': 0
    }
############
@app.cli.command()
def create():
    db.drop_all()
    db.create_all()
    from faker import Faker
    import random

    faker = Faker(locale="zh-CN")

    for i in range(100):
        student = orms.StudentORM()
        info = faker.simple_profile()
        student.name = info['name']
        student.gender = info['sex']
        student.mobile = faker.phone_number()
        student.address = info['address']
        student.class_name = random.choice(['一班', '二班', '三班'])
        student.save()


@app.route('/api/student')
def student_view():
    page = request.args.get('page', type=int, default=1)
    per_page = request.args.get('per_page', type=int, default=10)
    name = request.args.get('name')

    # 假设StudentORM是您的模型类，name是要搜索的字段
    query = StudentORM.query
    if name:
        # 使用like实现模糊查询，%name%表示任何包含name的字符串
        query = query.filter(StudentORM.name.like('%' + name + '%'))

    # 使用paginate进行分页查询
    paginate = query.paginate(page=page, per_page=per_page, error_out=False)
    items = paginate.items

    return {
        'code': 0,
        'msg': '信息查询成功',
        'count': paginate.total,
        'data': [
            {
                'id': item.id,
                'name': item.name,
                'gender': item.gender,
                'mobile': item.mobile,
                'class_name': item.class_name,
                'address': item.address,
                'disable': item.disable,
                'is_del': item.is_del,
                'create_at': item.create_at.strftime('%Y-%m-%d %H:%M:%S'),
                'update_at': item.update_at.strftime('%Y-%m-%d %H:%M:%S'),
            } for item in items
        ]
    }
###新增
@app.get('/student_add')
def student_add():
    return render_template('student_add.html')



@app.post('/api/student')
def api_student_post():
    data = request.get_json()
    data['create_at'] = datetime.strptime(data['create_at'], '%Y-%m-%d %H:%M:%S')
    student = StudentORM()
    student.update(data)
    try:
        student.save()
    except Exception as e:
        return {
            'code': -1,
            'msg': '新增数据失败'
        }
    return {
        'code': 0,
        'msg': '新增数据成功'
    }

@app.put('/api/student/<int:sid>')
def api_student_put(sid):
    data = request.get_json()
    data['create_at'] = datetime.strptime(data['create_at'], '%Y-%m-%d %H:%M:%S')
    # student = StudentORM.query.get(sid)
    student = db.get_or_404(StudentORM, sid)
    student.update(data)
    try:
        student.save()
    except Exception as e:
        return {
            'code': -1,
            'msg': '修改数据失败'
        }
    return {
        'code': 0,
        'msg': '修改数据成功'
    }

@app.delete('/api/student/<int:sid>')
def api_student_del(sid):
    student: StudentORM = db.get_or_404(StudentORM, sid)
    try:
        db.session.delete(student)
        #student.is_del = True
        db.session.commit()
    except Exception as e:
        return {
            'code': -1,
            'msg': '删除数据失败'
        }
    return {
        'code': 0,
        'msg': '删除数据成功'
    }
@app.put('/api/student/<int:sid>/class_name')
def api_student_class_name(sid):
    student: StudentORM = db.get_or_404(StudentORM, sid)
    data = request.get_json()
    try:
        student.class_name = data['class_name']
        student.save()
    except Exception as e:
        return {
            'code': -1,
            'msg': '修改班级失败'
        }
    return {
        'code': 0,
        'msg': '修改班级成功'
    }


@app.put('/api/student/<int:sid>/address')
def api_student_address(sid):
    student: StudentORM = db.get_or_404(StudentORM, sid)
    data = request.get_json()
    try:
        student.address = data['address']
        student.save()
    except Exception as e:
        return {
            'code': -1,
            'msg': '修改地址失败'
        }
    return {
        'code': 0,
        'msg': '修改地址成功'
    }

@app.put('/api/student/<int:sid>/disable')
def api_student_disable(sid):
    student: StudentORM = db.get_or_404(StudentORM, sid)
    data = request.get_json()
    try:
        student.disable = data['disable']
        student.save()
    except Exception as e:
        return {
            'code': -1,
            'msg': '修改禁用失败'
        }
    return {
        'code': 0,
        'msg': '修改禁用成功'
    }


if __name__ == '__main__':
    app.run(debug=True)