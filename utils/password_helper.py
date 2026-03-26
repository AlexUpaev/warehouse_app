import bcrypt

class PasswordHelper:
    @staticmethod
    def hash_password(password: str) -> bytes:
        """
        Хеширование пароля с использованием bcrypt.
        
        :param password: Пароль для хеширования.
        :return: Закодированное представление хеша.
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """
        Проверка соответствия введенного пароля хранимому хешу.
        
        :param password: Введенный пароль.
        :param hashed_password: Хеш пароля из базы данных.
        :return: True, если пароль верный, иначе False.
        """
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))