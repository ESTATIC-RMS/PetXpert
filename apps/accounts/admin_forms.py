from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from .models import User


class PetXpertUserAddForm(UserCreationForm):
  class Meta:
    model = User
    fields = ('email', 'full_name', 'role', 'is_staff', 'is_superuser', 'is_active')


class PetXpertUserChangeForm(UserChangeForm):
  class Meta:
    model = User
    fields = '__all__'


class PetXpertAdminPasswordChangeForm(AdminPasswordChangeForm):
  pass
