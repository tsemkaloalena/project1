import datetime
import sqlite3
import sys
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QColorDialog, QFileDialog, QInputDialog, QTableWidgetItem
from PyQt5.QtGui import QPixmap
from PIL import Image, ImageFilter
import os


class OpenForm(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('data/UI/open.ui', self)
        self.setWindowTitle('Открытие')
        self.name_btn.clicked.connect(self.open_second_form)

    def open_second_form(self):
        name = QFileDialog.getOpenFileName(self, 'Выбрать картинку', '')[0]
        new_name = self.make_new_name(name)
        self.redactor_form = RedactorForm(self, name, new_name)
        self.redactor_form.show()

    def make_new_name(self, name):
        im = Image.open(name)
        while os.access(name, os.R_OK):
            name = '/'.join(name.split('/')[:-1] + ['1' + name.split('/')[-1]])
        im.save(name)

        return name


class HistoryForm(QWidget):
    def __init__(self, *f):
        super().__init__()
        uic.loadUi('data/UI/changedfiles.ui', self)
        self.setWindowTitle('История соханений')
        sp = "SELECT name, date FROM pictures ORDER BY id DESC"
        self.show_files(sp)

    def show_files(self, sp):
        con = sqlite3.connect('data/history.db')
        cur = con.cursor()
        result = cur.execute(sp).fetchall()
        title = ['Имя файла', 'Дата']
        self.tableWidget.setColumnCount(len(title))
        self.tableWidget.setHorizontalHeaderLabels(title)
        self.tableWidget.setRowCount(0)
        for i, row in enumerate(result):
            self.tableWidget.setRowCount(self.tableWidget.rowCount() + 1)
            for j, elem in enumerate(row):
                self.tableWidget.setItem(i, j, QTableWidgetItem(elem))
        self.tableWidget.resizeColumnsToContents()
        con.commit()


class RedactorForm(QWidget):
    def __init__(self, *names):
        super().__init__()
        uic.loadUi('data/UI/redactor.ui', self)
        self.setWindowTitle('Редактор')

        self.filename = names[-2]
        self.new_filename = names[-1]

        self.bw_btn.clicked.connect(self.make_bw)
        self.negative_check.stateChanged.connect(self.make_negative)
        self.quantize_btn.clicked.connect(self.change_quantize)
        self.contrast_btn.clicked.connect(self.change_contrast)
        self.blur_btn.clicked.connect(self.change_blur)
        self.sharp_btn.clicked.connect(self.change_sharp)
        self.color_btn.clicked.connect(self.change_color)
        self.brightness_btn.clicked.connect(self.change_brightness)
        self.save_btn.clicked.connect(self.save_img)
        self.save_as_btn.clicked.connect(self.save_img_as)
        self.cancel_btn.clicked.connect(self.delete_img)
        self.files_btn.clicked.connect(self.show_files)

    def show_files(self):
        self.history_form = HistoryForm(self)
        self.history_form.show()

    def save_img_as(self):
        i, okBtnPressed = QInputDialog.getText(self, "Введите имя новой фотографии",
                                               "Сохранить как")
        if okBtnPressed:
            new_name = '/'.join(self.new_filename.split('/')[:-1] + [i])
            im = Image.open(self.new_filename)
            im.save(new_name)

            date = datetime.datetime.now().strftime("%d.%m.%Y  %H:%M")
            con = sqlite3.connect('data/history.db')
            cur = con.cursor()
            cur.execute(f"INSERT INTO pictures(name, date) VALUES('{new_name}', '{date}')").fetchall()
            con.commit()

            self.close()

    def save_img(self):
        im = Image.open(self.new_filename)
        im.save(self.filename)

        date = datetime.datetime.now().strftime("%d.%m.%Y  %H:%M")
        con = sqlite3.connect('data/history.db')
        cur = con.cursor()
        cur.execute(f"INSERT INTO pictures(name, date) VALUES('{self.filename}', '{date}')").fetchall()
        con.commit()

        self.close()

    def delete_img(self):
        self.close()

    def show_img(self):
        self.pixmap = QPixmap(self.new_filename).scaled(self.image.size(), Qt.KeepAspectRatio)
        self.image.setPixmap(self.pixmap)
        self.show()

    def enterEvent(self, QEvent):
        self.show_img()

    def closeEvent(self, QCloseEvent):
        os.remove(self.new_filename)

    def change_blur(self):
        self.blur_form = BlurForm(self, self.new_filename)
        self.blur_form.show()

    def change_quantize(self):
        self.quantize_form = QuantizeForm(self, self.new_filename)
        self.quantize_form.show()

    def change_sharp(self):
        self.sharp_form = SharpForm(self, self.new_filename)
        self.sharp_form.show()

    def change_brightness(self):
        self.brightness_form = BrightnessForm(self, self.new_filename)
        self.brightness_form.show()

    def change_contrast(self):
        self.contrast_form = ContrastForm(self, self.new_filename)
        self.contrast_form.show()

    def make_negative(self):
        im = Image.open(self.new_filename)
        pixels = im.load()
        x, y = im.size
        for i in range(x):
            for j in range(y):
                r, g, b = pixels[i, j]
                pixels[i, j] = 255 - r, 255 - g, 255 - b
        im.save(self.new_filename)
        self.pixmap = QPixmap(self.new_filename).scaled(self.image.size(), Qt.KeepAspectRatio)
        self.image.setPixmap(self.pixmap)

    def make_bw(self):
        self.bw_form = BlackAndWhiteForm(self, self.new_filename)
        self.bw_form.show()

    def change_color(self):
        color = self.choose_color()
        im = Image.open(self.new_filename)
        pixels = im.load()
        x, y = im.size
        for i in range(x):
            for j in range(y):
                r, g, b = pixels[i, j]
                bw = (r + g + b) // 3
                pixels[i, j] = int(bw * (color[0] / 255)), int(bw * (color[1] / 255)), int(bw * (color[2] / 255))
        im.save(self.new_filename)
        self.pixmap = QPixmap(self.new_filename).scaled(self.image.size(), Qt.KeepAspectRatio)
        self.image.setPixmap(self.pixmap)

    def choose_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            return color.getRgb()


class ContrastForm(QWidget):
    def __init__(self, *names):
        super().__init__()
        uic.loadUi('data/UI/contrast.ui', self)
        self.setWindowTitle('Контрастность')

        self.contrast_filename = names[-1]
        self.new_contrast_filename = self.new_contrast_name()
        self.pixmap = QPixmap(self.contrast_filename).scaled(self.contrast_image.size(), Qt.KeepAspectRatio)
        self.contrast_image.setPixmap(self.pixmap)
        self.show()

        self.change_btn.clicked.connect(self.run_contrast)
        self.ok_btn.clicked.connect(self.save_img)
        self.cancel_btn.clicked.connect(self.delete_img)

    def new_contrast_name(self):
        name = self.contrast_filename
        im = Image.open(self.contrast_filename)
        while os.access(name, os.R_OK):
            name = '/'.join(name.split('/')[:-1] + ['1' + name.split('/')[-1]])
        im.save(name)
        return name

    def run_contrast(self):
        value = self.contrast_value.value() / 100
        im = Image.open(self.contrast_filename)

        pixels = im.load()
        x, y = im.size

        n = 0
        for i in range(x):
            for j in range(y):
                r, g, b = pixels[i, j]
                n += r * 0.3 + g * 0.6 + b * 0.1
        n /= x * y

        palette = []
        for i in range(256):
            temp = int(n + value * (i - n))
            if temp < 0:
                temp = 0
            elif temp > 255:
                temp = 255
            palette.append(temp)

        for i in range(x):
            for j in range(y):
                r, g, b = pixels[i, j]
                pixels[i, j] = palette[r], palette[g], palette[b]

        im.save(self.new_contrast_filename)
        self.pixmap = QPixmap(self.new_contrast_filename).scaled(self.contrast_image.size(), Qt.KeepAspectRatio)
        self.contrast_image.setPixmap(self.pixmap)

    def save_img(self):
        im = Image.open(self.new_contrast_filename)
        im.save(self.contrast_filename)
        os.remove(self.new_contrast_filename)
        self.close()

    def delete_img(self):
        os.remove(self.new_contrast_filename)
        self.close()


class SharpForm(QWidget):
    def __init__(self, *names):
        super().__init__()
        uic.loadUi('data/UI/sharp.ui', self)
        self.setWindowTitle('Резкость')

        self.sharp_filename = names[-1]
        self.new_sharp_filename = self.new_sharp_name()
        self.pixmap = QPixmap(self.sharp_filename).scaled(self.sharp_image.size(), Qt.KeepAspectRatio)
        self.sharp_image.setPixmap(self.pixmap)
        self.show()

        self.sharp_slider.sliderMoved.connect(self.run_sharp)
        self.ok_btn.clicked.connect(self.save_img)
        self.cancel_btn.clicked.connect(self.delete_img)

    def new_sharp_name(self):
        name = self.sharp_filename
        im = Image.open(self.sharp_filename)
        while os.access(name, os.R_OK):
            name = '/'.join(name.split('/')[:-1] + ['1' + name.split('/')[-1]])
        im.save(name)
        return name

    def run_sharp(self):
        value = self.sharp_slider.value()
        im = Image.open(self.sharp_filename)
        im = im.filter(ImageFilter.UnsharpMask(2, value, 3))
        im.save(self.new_sharp_filename)
        self.pixmap = QPixmap(self.new_sharp_filename).scaled(self.sharp_image.size(), Qt.KeepAspectRatio)
        self.sharp_image.setPixmap(self.pixmap)

    def save_img(self):
        im = Image.open(self.new_sharp_filename)
        im.save(self.sharp_filename)
        os.remove(self.new_sharp_filename)
        self.close()

    def delete_img(self):
        os.remove(self.new_sharp_filename)
        self.close()


class BlurForm(QWidget):
    def __init__(self, *names):
        super().__init__()
        uic.loadUi('data/UI/blur.ui', self)
        self.setWindowTitle('Размытие')

        self.blur_filename = names[-1]
        self.new_blur_filename = self.new_blur_name()
        self.pixmap = QPixmap(self.blur_filename).scaled(self.blur_image.size(), Qt.KeepAspectRatio)
        self.blur_image.setPixmap(self.pixmap)
        self.show()

        self.blur_slider.sliderMoved.connect(self.run_blur)
        self.ok_btn.clicked.connect(self.save_img)
        self.cancel_btn.clicked.connect(self.delete_img)

    def new_blur_name(self):
        name = self.blur_filename
        im = Image.open(self.blur_filename)
        while os.access(name, os.R_OK):
            name = '/'.join(name.split('/')[:-1] + ['1' + name.split('/')[-1]])
        im.save(name)
        return name

    def run_blur(self):
        value = self.blur_slider.value()
        im = Image.open(self.blur_filename)
        im = im.filter(ImageFilter.GaussianBlur(value))
        im.save(self.new_blur_filename)
        self.pixmap = QPixmap(self.new_blur_filename).scaled(self.blur_image.size(), Qt.KeepAspectRatio)
        self.blur_image.setPixmap(self.pixmap)

    def save_img(self):
        im = Image.open(self.new_blur_filename)
        im.save(self.blur_filename)
        os.remove(self.new_blur_filename)
        self.close()

    def delete_img(self):
        os.remove(self.new_blur_filename)
        self.close()


class BrightnessForm(QWidget):
    def __init__(self, *names):
        super().__init__()
        uic.loadUi('data/UI/brightness.ui', self)
        self.setWindowTitle('Яркость')

        self.bright_filename = names[-1]
        self.new_bright_filename = self.new_bright_name()
        self.pixmap = QPixmap(self.bright_filename).scaled(self.bright_image.size(), Qt.KeepAspectRatio)
        self.bright_image.setPixmap(self.pixmap)
        self.show()

        self.change_btn.clicked.connect(self.run_bright)
        self.ok_btn.clicked.connect(self.save_img)
        self.cancel_btn.clicked.connect(self.delete_img)

    def new_bright_name(self):
        name = self.bright_filename
        im = Image.open(self.bright_filename)
        while os.access(name, os.R_OK):
            name = '/'.join(name.split('/')[:-1] + ['1' + name.split('/')[-1]])
        im.save(name)
        return name

    def run_bright(self):
        value = self.bright_value.value()
        im = Image.open(self.bright_filename)
        pixels = im.load()
        x, y = im.size
        for i in range(x):
            for j in range(y):
                r, g, b = pixels[i, j]
                r, g, b = r + value, g + value, b + value
                if r > 255:
                    r = 255
                elif r < 0:
                    r = 0
                if g > 255:
                    g = 255
                elif g < 0:
                    g = 0
                if b > 255:
                    b = 255
                elif b < 0:
                    b = 0
                pixels[i, j] = r, g, b
        im.save(self.new_bright_filename)
        self.pixmap = QPixmap(self.new_bright_filename).scaled(self.bright_image.size(), Qt.KeepAspectRatio)
        self.bright_image.setPixmap(self.pixmap)

    def save_img(self):
        im = Image.open(self.new_bright_filename)
        im.save(self.bright_filename)
        os.remove(self.new_bright_filename)
        self.close()

    def delete_img(self):
        os.remove(self.new_bright_filename)
        self.close()


class QuantizeForm(QWidget):
    def __init__(self, *names):
        super().__init__()
        uic.loadUi('data/UI/quantize.ui', self)
        self.setWindowTitle('Уменьшение количества цветов')

        self.quantize_filename = names[-1]
        self.new_quantize_filename = self.new_quantize_name()
        self.pixmap = QPixmap(self.quantize_filename).scaled(self.quantize_image.size(), Qt.KeepAspectRatio)
        self.quantize_image.setPixmap(self.pixmap)
        self.show()

        self.quantize_slider.sliderMoved.connect(self.run_quantize)
        self.ok_btn.clicked.connect(self.save_img)
        self.cancel_btn.clicked.connect(self.delete_img)

    def new_quantize_name(self):
        name = self.quantize_filename
        im = Image.open(self.quantize_filename)
        while os.access(name, os.R_OK):
            name = '/'.join(name.split('/')[:-1] + ['1' + name.split('/')[-1]])
        im.save(name)
        return name

    def run_quantize(self):
        value = self.quantize_slider.value()
        im = Image.open(self.quantize_filename)
        im = im.quantize(colors=value, method=None, kmeans=0, palette=None)
        im = im.convert(mode="RGB")
        im.save(self.new_quantize_filename)
        self.pixmap = QPixmap(self.new_quantize_filename).scaled(self.quantize_image.size(), Qt.KeepAspectRatio)
        self.quantize_image.setPixmap(self.pixmap)

    def save_img(self):
        im = Image.open(self.new_quantize_filename)
        im.save(self.quantize_filename)
        os.remove(self.new_quantize_filename)
        self.close()

    def delete_img(self):
        os.remove(self.new_quantize_filename)
        self.close()


class BlackAndWhiteForm(QWidget):
    def __init__(self, *names):
        super().__init__()
        uic.loadUi('data/UI/bw.ui', self)
        self.setWindowTitle('Чёрно-белое изображение')

        self.bw_filename = names[-1]
        self.new_bw_filename = self.new_bw_name()
        self.pixmap = QPixmap(self.bw_filename).scaled(self.bw_image.size(), Qt.KeepAspectRatio)
        self.bw_image.setPixmap(self.pixmap)
        self.show()

        self.bw_check.stateChanged.connect(self.run_bw)
        self.ok_btn.clicked.connect(self.save_img)
        self.cancel_btn.clicked.connect(self.delete_img)

    def new_bw_name(self):
        name = self.bw_filename
        im = Image.open(self.bw_filename)
        while os.access(name, os.R_OK):
            name = '/'.join(name.split('/')[:-1] + ['1' + name.split('/')[-1]])
        im.save(name)
        return name

    def run_bw(self):
        im = Image.open(self.bw_filename)
        if self.bw_check.isChecked():
            pixels = im.load()
            x, y = im.size
            for i in range(x):
                for j in range(y):
                    r, g, b = pixels[i, j]
                    bw = int(r * 0.3 + g * 0.6 + b * 0.1)
                    pixels[i, j] = bw, bw, bw
        im.save(self.new_bw_filename)
        self.pixmap = QPixmap(self.new_bw_filename).scaled(self.bw_image.size(), Qt.KeepAspectRatio)
        self.bw_image.setPixmap(self.pixmap)

    def save_img(self):
        im = Image.open(self.new_bw_filename)
        im.save(self.bw_filename)
        os.remove(self.new_bw_filename)
        self.close()

    def delete_img(self):
        os.remove(self.new_bw_filename)
        self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = OpenForm()
    ex.show()
    sys.exit(app.exec())
