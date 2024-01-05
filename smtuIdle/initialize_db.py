from peewee import SqliteDatabase
from models import * # Замените models на имя вашего модуля или файла с определением моделей
import os

db = SqliteDatabase('test.db')  # Замените на имя вашей базы данных

def initialize_database():
    # Проверяем, существует ли файл маркера
    if not os.path.exists('database_initialized.marker'):
        db.connect()
        db.create_tables([Purchase, User, Role, UserRole, Contract])
        admin_user = User.create(username='admin', password='sa')
        regular_user = User.create(username='user', password='sa')
        admin_role = Role.create(name='Администратор')
        user_role = Role.create(name='Пользователь')
        UserRole.create(user=regular_user, role=user_role)
        UserRole.create(user=admin_user, role=admin_role)
        db.close()

        # Создаем файл маркера, чтобы показать, что инициализация была завершена
        with open('database_initialized.marker', 'w'):
            pass
