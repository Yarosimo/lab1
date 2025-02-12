# Импортируем необходимые модули
from flask import Flask, render_template, request  # Flask — основной фреймворк, request — для обработки данных формы
import os  # Для работы с файловой системой
import cv2  # OpenCV для обработки изображений
import numpy as np  # NumPy для работы с массивами
import matplotlib.pyplot as plt  # Matplotlib для построения гистограмм
import requests  # Для работы с HTTP-запросами (не используется в коде, можно удалить)
from flask_wtf import FlaskForm  # Flask-WTF для работы с формами
from wtforms import FileField, SubmitField  # Поля формы: выбор файла и кнопка отправки
from flask_wtf.recaptcha import RecaptchaField  # Google reCAPTCHA для защиты от ботов

# Создаем Flask-приложение
app = Flask(__name__)

# Конфигурация приложения: секретный ключ и настройки reCAPTCHA
app.config['SECRET_KEY'] = '123'
app.config['RECAPTCHA_PUBLIC_KEY'] = '6Lfd29QqAAAAANUgxws1ukd-GzyR5Zol-7OxsCCs'
app.config['RECAPTCHA_PRIVATE_KEY'] = '6Lfd29QqAAAAAGWeXl_t_FhF36EBYH2ZogdGAORE'

# Папка для загрузки файлов
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Создаём папку, если её нет
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# Определяем форму загрузки файла с reCAPTCHA
class UploadForm(FlaskForm):
    file = FileField('Выберите изображение')  # Поле выбора файла
    recaptcha = RecaptchaField()  # Защита от ботов
    submit = SubmitField('Загрузить')  # Кнопка отправки формы


# Функция разбиения изображения на 4 части
def split_image(image_path):
    img = cv2.imread(image_path)  # Читаем изображение
    h, w, _ = img.shape  # Получаем его высоту и ширину
    mid_x, mid_y = w // 2, h // 2  # Вычисляем середину изображения

    # Разбиваем изображение на 4 части
    parts = {
        "top_left": img[:mid_y, :mid_x],  # Верхний левый угол
        "top_right": img[:mid_y, mid_x:],  # Верхний правый угол
        "bottom_left": img[mid_y:, :mid_x],  # Нижний левый угол
        "bottom_right": img[mid_y:, mid_x:]  # Нижний правый угол
    }

    filenames = {}
    for name, part in parts.items():
        filename = f"{name}.jpg"  # Генерируем имя файла
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        cv2.imwrite(filepath, part)  # Сохраняем изображение
        filenames[name] = filepath  # Запоминаем путь к файлу

    return filenames  # Возвращаем словарь с путями к изображениям


# Функция построения гистограммы цветов изображения
def plot_histogram(image_path, output_path):
    img = cv2.imread(image_path)  # Загружаем изображение
    colors = ('b', 'g', 'r')  # Цветовые каналы (синий, зелёный, красный)

    plt.figure(figsize=(6, 4))  # Создаем график

    for i, color in enumerate(colors):
        hist = cv2.calcHist([img], [i], None, [256], [0, 256])  # Строим гистограмму по каждому каналу
        plt.plot(hist, color=color)  # Рисуем график

    # Настраиваем внешний вид графика
    plt.xlim([0, 256])
    plt.title('Гистограмма цветов')
    plt.xlabel('Интенсивность')
    plt.ylabel('Количество пикселей')

    plt.savefig(output_path)  # Сохраняем график
    plt.close()  # Закрываем график, чтобы освободить память


# Маршрут главной страницы
@app.route('/', methods=['GET', 'POST'])
def upload_file():
    form = UploadForm()  # Создаём экземпляр формы

    if form.validate_on_submit():  # Проверяем, что форма отправлена и прошла валидацию
        file = request.files['file']  # Получаем загруженный файл

        # Проверяем, что файл имеет допустимое расширение
        if file and file.filename.endswith(('.png', '.jpg', '.jpeg')):
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)  # Сохраняем файл

            split_images = split_image(filepath)  # Разбиваем изображение на 4 части

            histograms = {}  # Создаём словарь для хранения гистограмм

            # Строим гистограмму для исходного изображения
            original_histogram = filepath.replace('.', '_hist.')
            plot_histogram(filepath, original_histogram)
            histograms['original'] = original_histogram

            # Строим гистограммы для каждой части изображения
            for name, img_path in split_images.items():
                hist_path = img_path.replace('.', '_hist.')
                plot_histogram(img_path, hist_path)
                histograms[name] = hist_path

            # Отображаем страницу с результатами
            return render_template('result.html', original=filepath, parts=split_images, histograms=histograms)

    return render_template('upload.html', form=form)  # Показываем форму загрузки


# Запуск приложения в режиме отладки
if __name__ == '__main__':
    app.run(debug=True)
