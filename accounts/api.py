from rest_framework import viewsets, generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import update_session_auth_hash
from django.db.models import Count, Avg, Sum
from .models import User
from .serializers import (
    UserSerializer, UserDetailSerializer, UserUpdateSerializer,
    PasswordChangeSerializer, EmailPreferencesSerializer
)
from properties.models import Property
from properties.serializers import PropertyListSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return UserDetailSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == 'retrieve':
            return queryset.annotate(
                property_count=Count('properties'),
                average_rating=Avg('agent__reviews__rating'),
                review_count=Count('agent__reviews')
            )
        return queryset

    @action(detail=False, methods=['get'])
    def profile(self, request):
        user = request.user
        serializer = UserDetailSerializer(user)
        return Response(serializer.data)

    @action(detail=False, methods=['put'])
    def update_profile(self, request):
        user = request.user
        serializer = UserUpdateSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def change_password(self, request):
        user = request.user
        serializer = PasswordChangeSerializer(data=request.data)
        
        if serializer.is_valid():
            if not user.check_password(serializer.data.get('old_password')):
                return Response({'old_password': ['Wrong password.']},
                              status=status.HTTP_400_BAD_REQUEST)
            
            user.set_password(serializer.data.get('new_password1'))
            user.save()
            update_session_auth_hash(request, user)
            return Response({'status': 'password set'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get', 'put'])
    def email_preferences(self, request):
        user = request.user
        if request.method == 'GET':
            serializer = EmailPreferencesSerializer(user)
            return Response(serializer.data)
        
        serializer = EmailPreferencesSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def favorite_properties(self, request):
        user = request.user
        properties = user.favorite_properties.all()
        serializer = PropertyListSerializer(properties, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_properties(self, request):
        user = request.user
        if not user.is_agent:
            return Response(
                {'detail': 'Only agents can access this endpoint.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        properties = Property.objects.filter(agent=user)
        serializer = PropertyListSerializer(properties, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        user = request.user
        if not user.is_agent:
            return Response(
                {'detail': 'Only agents can access this endpoint.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        properties = Property.objects.filter(agent=user)
        return Response({
            'total_properties': properties.count(),
            'active_listings': properties.filter(status='available').count(),
            'sold_properties': properties.filter(status='sold').count(),
            'total_views': properties.aggregate(total_views=Sum('views_count'))['total_views'] or 0,
            'average_rating': user.agent.average_rating if hasattr(user, 'agent') else 0,
            'total_reviews': user.agent.reviews.count() if hasattr(user, 'agent') else 0,
        })

class AgentListView(generics.ListAPIView):
    serializer_class = UserDetailSerializer
    
    def get_queryset(self):
        return User.objects.filter(role='agent').annotate(
            property_count=Count('properties'),
            average_rating=Avg('agent__reviews__rating'),
            review_count=Count('agent__reviews')
        ).order_by('-property_count') 