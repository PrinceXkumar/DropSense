from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import UserSignupForm

def signup(request):
    """
    Handles student mentor/parent registration.
    """
    if request.method == "POST":
        form = UserSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Log the user in immediately
            login(request, user)
            return redirect("students:student_list")
    else:
        form = UserSignupForm()

    return render(request, "registration/signup.html", {"form": form})
