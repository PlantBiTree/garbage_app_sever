from flask import Flask, request, Response
import cv2, os
import requests
from flask_cors import CORS
from motor import set_servo_open, set_servo_close
import time


class VideoCamera(object):
    def __init__(self):
        # 通过opencv获取实时视频流
        self.video = cv2.VideoCapture(0)

    def __del__(self):
        self.video.release()

    def get_frame(self):
        success, image = self.video.read()
        # 因为opencv读取的图片并非jpeg格式，因此要用motion JPEG模式需要先将图片转码成jpg格式图片
        ret, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes()

    def get_imge(self):
        success, image = self.video.read()
        return image


app = Flask(__name__)
CORS(app, supports_credentials=True)
videoPreview = VideoCamera()


def gen(camera):
    while True:
        frame = camera.get_frame()
        # 使用generator函数输出视频流， 每次请求输出的content类型是image/jpeg
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')


@app.route('/video_img_url')  # 返回视频流响
def video_feed():
    return Response(gen(videoPreview),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/shut_photho')  # 拍照识别内容返回结果
def shut_photho():
    frame = videoPreview.get_imge()
    if (os.path.exists("./test.png")):
        os.remove("./test.png")
    cv2.imwrite("./test.png", frame)
    res = upload_image_to_sever_get_result("./test.png")
    print(res)
    return res


@app.route('/open_motor')  # 打开舵机
def open_motor():
    channel = int(request.args.get("channel"))
    set_servo_open(channel)
    time.sleep(5)
    set_servo_close(channel)
    return "successful"


# 上传图片到后台服务器
def upload_image_to_sever_get_result(img_url):
    files = {"file": ("img_url" + ".png", open(img_url, 'rb'), "image/png")}
    r = requests.post('http://192.168.50.54:5000/predict', files=files)
    return r.json()['result']


# host='0.0.0.0',port = 5000

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
