from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()


# Create own class for register form
# And made it the ancestor of the build-in class UserCreationForm
class CreationForm(UserCreationForm):

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("first_name", "last_name", "username", "email")
