from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

def admin_login_view(request):
    """Vista de login para panel de administración"""
    # Si ya está autenticado y es admin, redirigir directamente
    if request.method == 'GET' and request.user.is_authenticated:
        next_url = request.GET.get('next', '/panel-admin/dashboard/')
        if getattr(request.user, 'role', None) == 'admin':
            return redirect(next_url)
        else:
            messages.error(request, 'No tienes permisos de administrador.')
            return redirect('/')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.role == 'admin':
                login(request, user)
                # Mantener sesión por 8 horas
                request.session.set_expiry(60 * 60 * 8)
                messages.success(request, 'Inicio de sesión exitoso')
                next_url = request.GET.get('next', '/panel-admin/dashboard/')
                return redirect(next_url)
            else:
                messages.error(request, 'No tienes permisos de administrador.')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    
    return render(request, 'admin/login.html')
