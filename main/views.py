from django.shortcuts import render, redirect
import requests
from django.conf import settings
from django.contrib.auth import logout as django_logout
from django.http import HttpResponseRedirect
from urllib.parse import urlencode
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from functools import wraps

def login_view(request):
    auth0_url = f"https://{settings.AUTH0_DOMAIN}/authorize"
    params = {
        "client_id": settings.AUTH0_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": settings.AUTH0_CALLBACK_URL,
        "scope": "openid profile email",
        "state": request.GET.get('next', '/'),
    }
    return HttpResponseRedirect(f"{auth0_url}?{urlencode(params)}")

def callback_view(request):
    code = request.GET.get("code")
    token_url = f"https://{settings.AUTH0_DOMAIN}/oauth/token"
    token_data = {
        "grant_type": "authorization_code",
        "client_id": settings.AUTH0_CLIENT_ID,
        "client_secret": settings.AUTH0_CLIENT_SECRET,
        "redirect_uri": settings.AUTH0_CALLBACK_URL,
        "code": code,
    }
    
    token_response = requests.post(token_url, json=token_data)
    
    if token_response.status_code != 200:
        return redirect('login')

    tokens = token_response.json()
    print("Token response:", tokens)

    user_info_url = f"https://{settings.AUTH0_DOMAIN}/userinfo"
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    user_info_response = requests.get(user_info_url, headers=headers)
    
    if user_info_response.status_code != 200:
        return redirect('login')  

    user_info = user_info_response.json()
    print("User info from Auth0:", user_info)

    request.session['user'] = {
        "user_id": user_info["sub"],
        "name": user_info["name"],
        "picture": user_info["picture"],
        "email": user_info.get("email")
    }
    
    next_url = request.GET.get("state", "/") 
    return redirect(next_url)

def logout_view(request):
    django_logout(request)
    params = {
        "returnTo": "http://localhost:8000",
        "client_id": settings.AUTH0_CLIENT_ID,
    }
    return redirect(f"https://{settings.AUTH0_DOMAIN}/v2/logout?{urlencode(params)}")

def auth0_login_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user_info = request.session.get("user")
        if user_info is None:
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def home_view(request):
    user_data = request.session.get('user')
    

    if user_data:
        user_id = user_data.get("user_id")
        roles = get_user_roles(user_id)


        if "Admin" in roles:
            role_message = "Tienes permisos de Administrador."
        elif "User" in roles:
            role_message = "Tienes permisos de Usuario."
        else:
            role_message = "No tienes permisos asignados."

    else:
        role_message = "Usuario no autenticado."

    context = {
        'user': user_data,
        'role_message': role_message,
    }
    return render(request, 'home.html', context)

@auth0_login_required
def prueba_view(request):
    user_data = request.session.get('user')
    return render(request, 'prueba.html', {'user': user_data})

def get_user_roles(user_id):
    token_response = requests.post(
        f"https://{settings.AUTH0_DOMAIN}/oauth/token",
        json={
            "client_id": settings.AUTH0_CLIENT_ID,
            "client_secret": settings.AUTH0_CLIENT_SECRET,
            "audience": f"https://{settings.AUTH0_DOMAIN}/api/v2/",
            "grant_type": "client_credentials",
        },
    )
    token_data = token_response.json()

    token = token_data.get("access_token")
    if not token:
        print("Error: No se pudo obtener el token de acceso")
        return []

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    response = requests.get(
        f"https://{settings.AUTH0_DOMAIN}/api/v2/users/{user_id}/roles",
        headers=headers,
    )

    try:
        roles_data = response.json()
        if isinstance(roles_data, list):
            roles = [role["name"] for role in roles_data]
            return roles
        else:
            print(f"Error: Respuesta inesperada para roles del usuario: {roles_data}")
            return []
    except ValueError:
        print("Error: La respuesta no es un JSON válido")
        return []


