# filename: /get_captcha.py
from io import BytesIO
from random import choices

from captcha.image import ImageCaptcha
from flask import make_response
from PIL import Image


def gen_captcha(content="0123456789"):
    """生成验证码"""
    image = ImageCaptcha()
    # 获取字符串
    captcha_text = "".join(choices(content, k=4))
    # 生成图像
    captcha_image = Image.open(image.generate(captcha_text))
    return captcha_text, captcha_image


# 生成验证码
def get_captcha_code_and_content():
    code, image = gen_captcha()
    out = BytesIO()
    image.save(out, "png")
    out.seek(0)
    content = out.read()  # 读取图片的二进制数据做成响应体
    return code, content


if __name__ == '__main__':
    code, content = get_captcha_code_and_content()
    print(code, content)