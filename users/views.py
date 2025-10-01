from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.http import HttpResponseNotAllowed
from django.shortcuts import redirect
from django.conf import settings
from .models import User
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer,
    UserListSerializer, ChangePasswordSerializer
)

class UserRegistrationView(generics.CreateAPIView):
    """
    API view for user registration.
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.role,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                },
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom JWT token view that returns user data along with tokens.
    """
    
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            username = request.data.get('username')
            password = request.data.get('password')
            try:
                user = User.objects.get(username=username)
                # Adjuntar datos del usuario en la respuesta
                response.data['user'] = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.role,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_admin': user.is_admin,
                    'is_customer': user.is_customer,
                    'is_staff': getattr(user, 'is_staff', False),
                    'is_superuser': getattr(user, 'is_superuser', False),
                }
                # Crear sesión de Django en el mismo login API para evitar doble login
                if username and password:
                    session_user = authenticate(request, username=username, password=password)
                    if session_user is not None:
                        login(request, session_user)
                        # Opcional: establecer expiración de sesión (ej. 8 horas)
                        request.session.set_expiry(60 * 60 * 8)
                        # Mensaje de confirmación para plantillas Django
                        messages.success(request, 'Inicio de sesión exitoso')
            except User.DoesNotExist:
                pass
        
        return response

class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    API view for user profile management.
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user

class ChangePasswordView(APIView):
    """
    API view for changing user password.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            return Response({
                'message': 'Password changed successfully'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserListView(generics.ListAPIView):
    """
    API view for listing users (admin only).
    """
    queryset = User.objects.all()
    serializer_class = UserListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Only allow admins to view user list
        if not self.request.user.is_admin:
            return User.objects.none()
        return User.objects.all().order_by('-date_joined')

class AdminPermission(permissions.BasePermission):
    """
    Custom permission to only allow admin users.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            (
                getattr(request.user, 'is_admin', False) or
                getattr(request.user, 'is_staff', False) or
                getattr(request.user, 'is_superuser', False) or
                getattr(request.user, 'role', '') == 'superadmin'
            )
        )

class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view for user detail management (admin only).
    """
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [AdminPermission]
    
    def get_queryset(self):
        return User.objects.all()

def logout_view(request):
    """
    Synchronous logout view that accepts GET or POST, logs out the user
    and redirects to LOGOUT_REDIRECT_URL or '/'.
    Fixes HTTP 405 issues from default LogoutView expectations.
    """
    if request.method in ['GET', 'POST']:
        try:
            logout(request)
            # Ensure session is flushed
            request.session.flush()
        except Exception:
            pass
        next_page = request.GET.get('next') or getattr(settings, 'LOGOUT_REDIRECT_URL', '/') or '/'
        return redirect(next_page)
    return HttpResponseNotAllowed(['GET', 'POST'])

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_stats(request):
    """
    API endpoint for user statistics (admin only).
    """
    if not request.user.is_admin:
        return Response(
            {'error': 'Admin access required'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    total_users = User.objects.count()
    total_customers = User.objects.filter(role='customer').count()
    total_admins = User.objects.filter(role='admin').count()
    active_users = User.objects.filter(is_active=True).count()
    
    # Recent registrations (last 30 days)
    from django.utils import timezone
    from datetime import timedelta
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_registrations = User.objects.filter(
        date_joined__gte=thirty_days_ago
    ).count()
    
    return Response({
        'total_users': total_users,
        'total_customers': total_customers,
        'total_admins': total_admins,
        'active_users': active_users,
        'recent_registrations': recent_registrations,
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def check_username_availability(request):
    """
    API endpoint to check if username is available.
    """
    username = request.data.get('username')
    if not username:
        return Response(
            {'error': 'Username is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    is_available = not User.objects.filter(username=username).exists()
    
    return Response({
        'username': username,
        'is_available': is_available
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def check_email_availability(request):
    """
    API endpoint to check if email is available.
    """
    email = request.data.get('email')
    if not email:
        return Response(
            {'error': 'Email is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    is_available = not User.objects.filter(email=email).exists()
    
    return Response({
        'email': email,
        'is_available': is_available
    }, status=status.HTTP_200_OK)
