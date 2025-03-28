from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import RegistrationForm

def chatPage(request, *args, **kwargs):
    if not request.user.is_authenticated:
        return redirect("login-user")
    context = {}
    return render(request, "chat/chatPage.html", context)


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('chat-page')  # Replace with your chat view name
    else:
        form = RegistrationForm()
    return render(request, 'chat/register.html', {'form': form})    

  
