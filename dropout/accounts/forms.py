from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class UserSignupForm(UserCreationForm):
    # Filter the role choices so only 'mentor' and 'parent' are available
    # We do NOT allow signing up as an 'admin' publicly.
    role = forms.ChoiceField(
        choices=[
            (User.ROLE_MENTOR, "Mentor (Teacher/Staff)"),
            (User.ROLE_PARENT, "Parent (Student Guardian)"),
        ],
        required=True,
        help_text="Choose your role in the system."
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "first_name", "last_name", "role")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = self.cleaned_data["role"]
        if commit:
            user.save()
        return user
