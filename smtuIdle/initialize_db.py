from peewee import SqliteDatabase
from models import * # Замените models на имя вашего модуля или файла с определением моделей
import os

db = SqliteDatabase('test.db')  # Замените на имя вашей базы данных

def initialize_database():
    # Проверяем, существует ли файл маркера
    if not os.path.exists('database_initialized.marker'):
        db.connect()
        db_folder = "файлы бд"
        os.makedirs(db_folder, exist_ok=True)
        db.create_tables([Purchase, User, Role, UserRole, Contract,FinalDetermination,CurrencyRate,UserLog ])
        admin_user = User.create(username='Якупов', password='Якупов')
        readactor =User.create(username='Померанец', password='Померанец')
        regular_user = User.create(username='Маковий', password='Маковий')
        gost = User.create(username='Ваучский', password='Ваучский')
        admin_role = Role.create(name='Администратор')
        readactor_role = Role.create(name='Редактор')
        user_role = Role.create(name='Пользователь')
        gost_role = Role.create(name='Гость')
        UserRole.create(user=regular_user, role=user_role)
        UserRole.create(user=admin_user, role=admin_role)
        UserRole.create(user=readactor, role=readactor_role)
        UserRole.create(user=gost, role=gost_role)
        db.close()

        # Создаем файл маркера, чтобы показать, что инициализация была завершена
        with open('database_initialized.marker', 'w'):
            pass
