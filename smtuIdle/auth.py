from smtuIdle.BD.models import User


class AuthManager:
   
      

    def authenticate(self, username, password):
        try:
            user = User.get(User.username == username, User.password == password)
            return user
        except User.DoesNotExist:
            return None

