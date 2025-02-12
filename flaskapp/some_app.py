from flask import Flask, render_template, request
import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
import requests
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField
from flask_wtf.recaptcha import RecaptchaField

app = Flask(__name__)
app.config['SECRET_KEY'] = '123'
app.config['RECAPTCHA_PUBLIC_KEY'] = '6Lfd29QqAAAAANUgxws1ukd-GzyR5Zol-7OxsCCs'
app.config['RECAPTCHA_PRIVATE_KEY'] = '6Lfd29QqAAAAAGWeXl_t_FhF36EBYH2ZogdGAORE'

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

class UploadForm(FlaskForm):
    file = FileField('Выберите изображение')
    recaptcha = RecaptchaField()
    submit = SubmitField('Загрузить')

def split_image(image_path):
    img = cv2.imread(image_path)
    h, w, _ = img.shape
    mid_x, mid_y = w // 2, h // 2
    parts = {
        "top_left": img[:mid_y, :mid_x],
        "top_right": img[:mid_y, mid_x:],
        "bottom_left": img[mid_y:, :mid_x],
        "bottom_right": img[mid_y:, mid_x:]
    }
    filenames = {}
    for name, part in parts.items():
        filename = f"{name}.jpg"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        cv2.imwrite(filepath, part)
        filenames[name] = filepath
    return filenames

def plot_histogram(image_path, output_path):
    img = cv2.imread(image_path)
    colors = ('b', 'g', 'r')
    plt.figure(figsize=(6, 4))
    for i, color in enumerate(colors):
        hist = cv2.calcHist([img], [i], None, [256], [0, 256])
        plt.plot(hist, color=color)
    plt.xlim([0, 256])
    plt.title('Гистограмма цветов')
    plt.xlabel('Интенсивность')
    plt.ylabel('Количество пикселей')
    plt.savefig(output_path)
    plt.close()

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    form = UploadForm()
    if form.validate_on_submit():
        file = request.files['file']
        if file and file.filename.endswith(('.png', '.jpg', '.jpeg')):
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            split_images = split_image(filepath)
            histograms = {}
            original_histogram = filepath.replace('.', '_hist.')
            plot_histogram(filepath, original_histogram)
            histograms['original'] = original_histogram
            for name, img_path in split_images.items():
                hist_path = img_path.replace('.', '_hist.')
                plot_histogram(img_path, hist_path)
                histograms[name] = hist_path
            return render_template('result.html', original=filepath, parts=split_images, histograms=histograms)
    return render_template('upload.html', form=form)

if __name__ == '__main__':
    app.run(debug=True)
