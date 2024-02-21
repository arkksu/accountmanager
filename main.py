from sys import argv, exit
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from string import ascii_lowercase, ascii_uppercase, digits
import random
import sqlite3
from hwid import get_hwid
from os import rename, remove, path, mkdir, getcwd
import base64
from cryptography.fernet import Fernet


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Менеджер аккаунтов')
        self.setFixedSize(800, 600)
        self.accountlabel = QLabel('Аккаунты', self)
        self.accountlabel.setGeometry(10, 0, 525, 50)
        self.accountlabel.setFont(QFont('Arial', 24, 50))
        self.accountlabel.setAlignment(Qt.AlignCenter)
        self.accountlist = QListWidget(self)
        self.accountlist.setGeometry(10, 50, 525, 540)
        self.accountlist.setFont(QFont('Arial', 12))
        self.actionslabel = QLabel('Действия', self)
        self.actionslabel.setGeometry(550, 0, 240, 50)
        self.actionslabel.setFont(QFont('Arial', 18, 50))
        self.actionslabel.setAlignment(Qt.AlignCenter)
        self.addbutton = QPushButton('Добавить аккаунт', self)
        self.addbutton.setGeometry(550, 50, 240, 50)
        self.addbutton.clicked.connect(self.addEvent)
        self.delbutton = QPushButton('Удалить аккаунт', self)
        self.delbutton.setGeometry(550, 110, 240, 50)
        self.delbutton.clicked.connect(self.removeEvent)
        self.openbutton = QPushButton('Открыть аккаунт', self)
        self.openbutton.setGeometry(550, 170, 240, 50)
        self.openbutton.clicked.connect(self.openEvent)
        self.genbutton = QPushButton('Генерация пароля', self)
        self.genbutton.setGeometry(550, 230, 240, 50)
        self.genbutton.clicked.connect(self.generateEvent)
        self.accountlist.itemClicked.connect(self.openEvent)
        self.fer = Fernet(base64.b64encode(get_hwid()[4:].encode()))
        self.existed_names = []
        if path.isfile('accounts.db'):
            self.con = sqlite3.connect('accounts.db')
            self.check_db()
        else:
            self.createdatabase()

    def check_db(self):
        f = False
        cur = self.con.cursor()
        try:
            if not all(
                    cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{i}'").fetchall() for i in
                    ('accounts', 'mails', 'logins')):
                f = True
            else:
                self.existed_names = [i[0] for i in cur.execute('SELECT name FROM accounts').fetchall()]
                for i in self.existed_names:
                    item = QListWidgetItem()
                    item.setText(i)
                    self.accountlist.addItem(item)
        except sqlite3.OperationalError:
            f = True
        if f:
            self.con.close()
            if path.isfile('accounts.db.bak'):
                remove('accounts.db.bak')
            rename('accounts.db', 'accounts.db.bak')
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle('Ошибка')
            msg.setText('База данных повреждена')
            msg.setInformativeText('База аккаунтов будет создана заново')
            msg.exec()
            self.createdatabase()

    def createdatabase(self):
        self.con = sqlite3.connect('accounts.db')
        cur = self.con.cursor()
        cur.execute('''CREATE TABLE logins (id INTEGER PRIMARY KEY
                            AUTOINCREMENT NOT NULL UNIQUE, name TEXT NOT NULL UNIQUE)''')
        cur.execute('''CREATE TABLE mails (id INTEGER PRIMARY KEY AUTOINCREMENT
                            NOT NULL UNIQUE, name TEXT NOT NULL UNIQUE)''')
        cur.execute('''CREATE TABLE accounts (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE, login
                            INTEGER REFERENCES logins (id) NOT NULL, mail INTEGER REFERENCES mails (id), password
                            BLOB NOT NULL, name TEXT NOT NULL UNIQUE, maillogin INTEGER NOT NULL)''')

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            self.removeEvent()
        elif event.key() == Qt.Key_Return:
            self.openEvent(status=1)

    def addEvent(self):
        x = self.x() + (self.width() // 2) - 162
        y = self.y() + (self.height() // 2) - 100
        self.addw = AddWindow(self, x, y)
        self.addw.exec()

    def removeEvent(self):
        curr = self.accountlist.selectedItems()
        curr_index = self.accountlist.currentRow()
        if curr:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Question)
            msg.setWindowTitle('Удаление аккаунта')
            msg.setText(f'Вы уверены, что хотите удалить аккаунт {curr[0].text()}?')
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            answer = msg.exec()
            if answer == QMessageBox.Yes:
                delete = self.accountlist.takeItem(curr_index)
                self.existed_names.pop(curr_index)
                cur = self.con.cursor()
                cur.execute(f'''DELETE FROM accounts WHERE name = "{delete.text()}"''')
                self.con.commit()
        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle('Ошибка')
            msg.setText('Ни один из элементов не выделен')
            msg.exec()

    def openEvent(self, status=0):
        selected = self.accountlist.selectedItems()
        if not selected:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle('Ошибка')
            msg.setText('Ни один из элементов не выделен')
            msg.exec()
        elif self.sender() == self.openbutton or status == 1:
            x = self.x() + (self.width() // 2) - 202
            y = self.y() + (self.height() // 2) - 92
            self.openw = AccountWindow(self, x, y, selected[0])
            self.openw.exec()

    def generateEvent(self):
        x = self.x() + (self.width() // 2) - 172
        y = self.y() + (self.height() // 2) - 100
        self.genw = GenerateWindow(self, x, y)
        self.genw.exec()

    def closeEvent(self, t):
        self.con.close()
        QApplication.clipboard().setText('')
        QApplication.closeAllWindows()


class AddWindow(QDialog):
    def __init__(self, parent, x, y, password=''):
        super().__init__()
        self.parent = parent
        self.setWindowTitle('Добавление аккаунта')
        self.setGeometry(x, y, 370, 170)
        self.namelabel = QLabel('Название:', self)
        self.namelabel.setGeometry(200, 10, 150, 20)
        self.nameline = QLineEdit(self)
        self.nameline.setGeometry(200, 30, 150, 20)
        self.maillabel = QLabel('Почта: (необязательно)', self)
        self.maillabel.setGeometry(200, 60, 150, 20)
        self.mailline = QLineEdit(self)
        self.mailline.setGeometry(200, 80, 150, 20)
        self.loginlabel = QLabel('Логин:', self)
        self.loginlabel.setGeometry(10, 10, 100, 20)
        self.loginline = QLineEdit(self)
        self.loginline.setGeometry(10, 30, 150, 20)
        self.loginline.textChanged.connect(self.lgchanged)
        self.passlabel = QLabel('Пароль:', self)
        self.passlabel.setGeometry(10, 60, 100, 20)
        self.passline = QLineEdit(self)
        self.passline.setGeometry(10, 80, 150, 20)
        self.passline.setEchoMode(2)
        self.maillogin = QCheckBox('Почта совпадает с логином', self)
        self.maillogin.setGeometry(200, 110, 170, 20)
        self.maillogin.stateChanged.connect(self.mlchecked)
        self.showpass = QCheckBox('Показать пароль', self)
        self.showpass.setGeometry(10, 110, 170, 20)
        self.showpass.stateChanged.connect(self.showpassword)
        self.genpass = QPushButton('Генерация пароля', self)
        self.genpass.setGeometry(10, 137, 120, 25)
        self.genpass.clicked.connect(self.gen)
        self.createacc = QPushButton('Создать', self)
        self.createacc.setGeometry(280, 137, 80, 25)
        self.createacc.clicked.connect(self.checkValues)

        if password:
            self.passline.setEnabled(False)
            self.passline.setText(password)
            self.genpass.hide()

    def mlchecked(self, status):
        if status:
            self.maillabel.setEnabled(False)
            self.mailline.setEnabled(False)
            self.mailline.setText(self.loginline.text())
        else:
            self.maillabel.setEnabled(True)
            self.mailline.setEnabled(True)
            self.mailline.setText('')

    def showpassword(self, status):
        if status:
            self.passline.setEchoMode(0)
        else:
            self.passline.setEchoMode(2)

    def lgchanged(self):
        if not self.mailline.isEnabled():
            self.mailline.setText(self.loginline.text())

    def checkValues(self):
        if not self.loginline.text():
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle('Ошибка')
            msg.setText('Введите логин')
            msg.exec()
        elif not self.passline.text():
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle('Ошибка')
            msg.setText('Введите пароль или сгенерируйте его')
            msg.exec()
        elif not self.nameline.text():
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle('Ошибка')
            msg.setText('Введите название')
            msg.exec()
        elif self.nameline.text() in self.parent.existed_names:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle('Ошибка')
            msg.setText('Данное название уже используется')
            msg.exec()
        else:
            if self.maillogin.isChecked():
                ml = 1
            else:
                ml = 0
            cur = self.parent.con.cursor()
            cur.execute(f'INSERT OR IGNORE INTO logins (name) VALUES ("{self.loginline.text()}")')
            login_id = cur.execute(f'SELECT id FROM logins WHERE name = "{self.loginline.text()}"').fetchone()[0]
            password = self.parent.fer.encrypt(self.passline.text().encode('utf-8'))
            mail_id = 'NULL'
            if self.mailline.text():
                cur.execute(f'INSERT OR IGNORE INTO mails (name) VALUES ("{self.mailline.text()}")')
                mail_id = cur.execute(f'SELECT id FROM mails WHERE name = "{self.mailline.text()}"').fetchone()[0]
            cur.execute(f'''INSERT INTO accounts VALUES (NULL, {login_id},
                {mail_id}, "{password}", "{self.nameline.text()}", {ml})''')
            item = QListWidgetItem()
            item.setText(self.nameline.text())
            self.parent.accountlist.addItem(item)
            self.parent.con.commit()
            self.close()

    def gen(self):
        self.close()
        self.genw = GenerateWindow(self.parent, self.x(), self.y())
        self.genw.exec()


class GenerateWindow(QDialog):
    def __init__(self, parent, x, y):
        super().__init__()
        self.parent = parent
        self.setWindowTitle('Генерация пароля')
        self.setGeometry(x, y, 325, 200)
        self.password = QLineEdit(self)
        self.password.setGeometry(10, 10, 305, 30)
        self.password.setEnabled(False)
        self.small = QCheckBox('Использовать маленькие англ. символы', self)
        self.small.move(10, 50)
        self.small.setChecked(True)
        self.big = QCheckBox('Использовать большие англ. символы', self)
        self.big.move(10, 70)
        self.big.setChecked(True)
        self.digit = QCheckBox('Использовать цифры', self)
        self.digit.move(10, 90)
        self.digit.setChecked(True)
        self.special = QCheckBox('Использовать специальные символы', self)
        self.special.move(10, 110)
        self.lenghtlabel = QLabel('Длина:', self)
        self.lenghtlabel.move(10, 136)
        self.lenght = QSpinBox(self)
        self.lenght.move(50, 133)
        self.lenght.setValue(12)
        self.lenght.setRange(8, 50)
        self.copy = QPushButton('Скопировать', self)
        self.copy.setGeometry(10, 165, 100, 25)
        self.copy.clicked.connect(self.copyEvent)
        self.add = QPushButton('Использовать в новом аккаунте', self)
        self.add.setGeometry(115, 165, 200, 25)
        self.add.clicked.connect(self.addEvent)
        self.gen = QPushButton('Сгенерировать', self)
        self.gen.setGeometry(215, 130, 100, 30)
        self.gen.clicked.connect(self.genEvent)

    def copyEvent(self):
        if self.password.text():
            QApplication.clipboard().setText(self.password.text())

    def genEvent(self):
        f = False
        st = ''
        if self.small.isChecked():
            st += ascii_lowercase
            f = True
        if self.big.isChecked():
            st += ascii_uppercase
            f = True
        if self.digit.isChecked():
            st += digits
            f = True
        if self.special.isChecked():
            st += '!@#$%^&*-_+=;:,./?|`~()[]{}'
            f = True
        if f:
            self.password.setText(''.join(random.choices(st, k=self.lenght.value())))
        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle('Ошибка')
            msg.setText('Выберите хотя бы один пункт для генерации')
            msg.exec()

    def addEvent(self):
        if self.password.text():
            x = self.x()
            y = self.y()
            self.close()
            self.addw = AddWindow(self.parent, x, y, password=self.password.text())
            self.addw.exec()
        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle('Ошибка')
            msg.setText('Аккаунт нельзя создать без сгенерированного пароля')
            msg.exec()


class AccountWindow(QDialog):
    def __init__(self, parent, x, y, account):
        super().__init__()
        self.setWindowTitle('Аккаунт')
        self.setGeometry(x, y, 405, 185)
        self.parent = parent
        self.account = account
        self.loginlabel = QLabel('Логин:', self)
        self.loginlabel.setGeometry(10, 10, 100, 20)
        self.loginline = QLineEdit(self)
        self.loginline.setGeometry(10, 30, 150, 20)
        self.loginline.setEnabled(False)
        self.loginline.textChanged.connect(self.lgchanged)
        self.logincopy = QPushButton('c', self)
        self.logincopy.setGeometry(165, 30, 20, 20)
        self.logincopy.clicked.connect(self.copyEvent)
        self.maillabel = QLabel('Почта:', self)
        self.maillabel.setGeometry(220, 10, 150, 20)
        self.mailline = QLineEdit(self)
        self.mailline.setGeometry(220, 30, 150, 20)
        self.mailline.setEnabled(False)
        self.mailcopy = QPushButton('c', self)
        self.mailcopy.setGeometry(375, 30, 20, 20)
        self.mailcopy.clicked.connect(self.copyEvent)
        self.passlabel = QLabel('Пароль:', self)
        self.passlabel.setGeometry(10, 60, 100, 20)
        self.passline = QLineEdit(self)
        self.passline.setGeometry(10, 80, 150, 20)
        self.passline.setEnabled(False)
        self.passline.setEchoMode(2)
        self.passcopy = QPushButton('c', self)
        self.passcopy.setGeometry(165, 80, 20, 20)
        self.passcopy.clicked.connect(self.copyEvent)
        self.showpass = QCheckBox('Показать пароль', self)
        self.showpass.setGeometry(10, 110, 170, 20)
        self.showpass.clicked.connect(self.showpassword)
        self.copy = QPushButton('Скопировать всё', self)
        self.copy.setGeometry(10, 150, 110, 25)
        self.copy.clicked.connect(self.copyEvent)
        self.savetofile = QPushButton('Сохранить в файл', self)
        self.savetofile.setGeometry(125, 150, 115, 25)
        self.savetofile.clicked.connect(self.fileEvent)
        self.edit = QPushButton('Изменить', self)
        self.edit.setGeometry(315, 150, 80, 25)
        self.edit.clicked.connect(self.editEvent)
        self.save = QPushButton('Сохранить', self)
        self.save.setGeometry(220, 150, 80, 25)
        self.save.clicked.connect(self.saveEvent)
        self.save.hide()
        self.cancel = QPushButton('Отменить', self)
        self.cancel.setGeometry(315, 150, 80, 25)
        self.cancel.clicked.connect(self.cancelEvent)
        self.cancel.hide()
        self.maillogin = QCheckBox('Почта совпадает с логином', self)
        self.maillogin.setGeometry(220, 60, 170, 20)
        self.maillogin.stateChanged.connect(self.mlchecked)
        self.maillogin.hide()
        self.loadEvent()

    def loadEvent(self):
        cur = self.parent.con
        values = cur.execute(f'''SELECT * FROM accounts WHERE name = "{self.account.text()}"''').fetchone()
        self.id = values[0]
        self.loginline.setText(cur.execute(f'SELECT name FROM logins WHERE id = "{values[1]}"').fetchone()[0])
        self.passline.setText(self.parent.fer.decrypt(values[3][2:-1]).decode('utf-8'))
        if values[2]:
            self.mailline.setText(cur.execute(f'SELECT name FROM mails WHERE id = "{values[2]}"').fetchone()[0])
        self.maillogin.setChecked(bool(values[5]))

    def copyEvent(self):
        if self.sender() == self.logincopy:
            QApplication.clipboard().setText(self.loginline.text())
        elif self.sender() == self.mailcopy:
            QApplication.clipboard().setText(self.mailline.text())
            if self.mailline.text() == '':
                QApplication.clipboard().setText('Почты нет')
        elif self.sender() == self.passcopy:
            QApplication.clipboard().setText(self.passline.text())
        elif self.sender() == self.copy:
            if self.maillogin.isChecked() is False and self.mailline.text():
                QApplication.clipboard().setText(
                    f'{self.loginline.text()}:{self.mailline.text()}:{self.passline.text()}')
            else:
                QApplication.clipboard().setText(f'{self.loginline.text()}:{self.passline.text()}')

    def fileEvent(self):
        file = open(QFileDialog.getSaveFileName(self, 'Сохранить', '',
                                                'Текстовый файл (*.txt);;Все файлы (*)')[0], 'w')
        if self.maillogin.isChecked() is False and self.mailline.text():
            file.write(f'Логин: {self.loginline.text()}\nПочта: {self.mailline.text()}\nПароль: {self.passline.text()}')
        else:
            file.write(f'Логин: {self.loginline.text()}\nПароль: {self.passline.text()}')
        file.close()

    def showpassword(self, status):
        if status:
            self.passline.setEchoMode(0)
        else:
            self.passline.setEchoMode(2)

    def editEvent(self):
        self.savetofile.hide()
        self.copy.hide()
        self.edit.hide()
        self.maillogin.show()
        self.cancel.show()
        self.save.show()
        self.logincopy.hide()
        self.mailcopy.hide()
        self.passcopy.hide()
        self.loginline.setEnabled(True)
        if self.maillogin.isChecked() is False:
            self.mailline.setEnabled(True)
        self.passline.setEnabled(True)
        self.login = self.loginline.text()
        self.mail = self.mailline.text()
        self.password = self.passline.text()
        self.mlstatus = self.maillogin.isChecked()

    def mlchecked(self, status):
        if status:
            self.maillabel.setEnabled(False)
            self.mailline.setEnabled(False)
            self.mailline.setText(self.loginline.text())
        else:
            self.maillabel.setEnabled(True)
            self.mailline.setEnabled(True)
            self.mailline.setText('')

    def lgchanged(self):
        if self.maillogin.isChecked():
            self.mailline.setText(self.loginline.text())

    def cancelEvent(self, status=0):
        self.savetofile.show()
        self.copy.show()
        self.edit.show()
        self.maillogin.hide()
        self.cancel.hide()
        self.save.hide()
        self.logincopy.show()
        self.mailcopy.show()
        self.passcopy.show()
        self.loginline.setEnabled(False)
        self.mailline.setEnabled(False)
        self.passline.setEnabled(False)
        if status == 0:
            self.loginline.setText(self.login)
            self.mailline.setText(self.mail)
            self.passline.setText(self.password)
            self.maillogin.setChecked(self.mlstatus)
            self.mailline.setEnabled(False)

    def saveEvent(self):
        if not self.loginline.text():
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle('Ошибка')
            msg.setText('Логин не может быть пустым')
            msg.exec()
        elif not self.passline.text():
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle('Ошибка')
            msg.setText('Пароль не может быть пустым')
            msg.exec()
        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Question)
            msg.setWindowTitle('Изменение данных')
            msg.setText(f'Вы уверены, что хотите изменить данные для {self.account.text()}?')
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            answer = msg.exec()
            if answer == QMessageBox.Yes:
                cur = self.parent.con.cursor()
                if self.maillogin.isChecked():
                    ml = 1
                else:
                    ml = 0
                cur.execute(f'INSERT OR IGNORE INTO logins (name) VALUES ("{self.loginline.text()}")')
                login_id = cur.execute(f'SELECT id FROM logins WHERE name = "{self.loginline.text()}"').fetchone()[0]
                password = self.parent.fer.encrypt(self.passline.text().encode('utf-8'))
                mail_id = 'NULL'
                if self.mailline.text():
                    cur.execute(f'INSERT OR IGNORE INTO mails (name) VALUES ("{self.mailline.text()}")')
                    mail_id = cur.execute(f'SELECT id FROM mails WHERE name = "{self.mailline.text()}"').fetchone()[0]
                cur.execute(f'''UPDATE accounts SET login = {login_id}, mail = {mail_id},
                    password = "{password}", maillogin = {ml} WHERE id = {self.id}''')
                self.parent.con.commit()
                self.cancelEvent(status=1)


class WrongParameter(Exception):
    pass


if __name__ == '__main__':
    app = QApplication(argv)
    ex = MainWindow()
    ex.show()
    exit(app.exec())
