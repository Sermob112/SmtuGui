from models import User, Role, UserRole

class AuthManager:
   
      

    def authenticate(self, username, password):
        try:
            user = User.get(User.username == username, User.password == password)
            return user
        except User.DoesNotExist:
            return None

    # def register(self, username, password):
    #     try:
    #         user = User.create(username=username, password=password)
    #         return user
    #     except Exception as e:
    #         print(f"Error creating user: {e}")
    #         return None

    # def assign_role(self, user, role_name):
    #     try:
    #         role = Role.get(Role.name == role_name)
    #         UserRole.create(user=user, role=role)
    #     except Role.DoesNotExist:
    #         print(f"Role {role_name} does not exist")