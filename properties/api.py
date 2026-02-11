from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Avg, Count
from .models import Property, PropertyImage, PropertyReview
from .serializers import (
    PropertyListSerializer, PropertyDetailSerializer,
    PropertyCreateUpdateSerializer, PropertyImageSerializer,
    PropertyReviewSerializer
)
from .filters import PropertyFilter
from .permissions import IsAgentOrSellerOrReadOnly, IsOwnerOrReadOnly

class PropertyViewSet(viewsets.ModelViewSet):
    queryset = Property.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PropertyFilter
    search_fields = ['title', 'description', 'address', 'city', 'state', 'zip_code']
    ordering_fields = ['price', 'created_at', 'views_count']
    ordering = ['-created_at']
    permission_classes = [IsAuthenticatedOrReadOnly, IsAgentOrSellerOrReadOnly]

    def get_serializer_class(self):
        if self.action == 'list':
            return PropertyListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return PropertyCreateUpdateSerializer
        return PropertyDetailSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == 'list':
            return queryset.select_related('owner', 'agent')
        elif self.action == 'retrieve':
            return queryset.select_related('owner', 'agent').prefetch_related(
                'images', 'features', 'amenities', 'reviews__user'
            ).annotate(
                average_rating=Avg('reviews__rating'),
                review_count=Count('reviews')
            )
        return queryset

    def perform_create(self, serializer):
        # Set the owner to the current user
        instance = serializer.save(owner=self.request.user)
        # If the user is an agent, also set them as the managing agent
        if self.request.user.role == 'agent':
            instance.agent = self.request.user
            instance.save()

    @action(detail=True, methods=['post'])
    def favorite(self, request, pk=None):
        property_obj = self.get_object()
        user = request.user
        
        if property_obj.favorited_by.filter(id=user.id).exists():
            property_obj.favorited_by.remove(user)
            is_favorited = False
        else:
            property_obj.favorited_by.add(user)
            is_favorited = True
        
        return Response({
            'status': 'success',
            'is_favorited': is_favorited
        })

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def add_review(self, request, pk=None):
        property_obj = self.get_object()
        serializer = PropertyReviewSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(property=property_obj, user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsOwnerOrReadOnly])
    def upload_images(self, request, pk=None):
        property_obj = self.get_object()
        images = request.FILES.getlist('images')
        response_data = []
        
        for image in images:
            serializer = PropertyImageSerializer(data={
                'image': image,
                'property': property_obj.id
            })
            if serializer.is_valid():
                serializer.save(property=property_obj)
                response_data.append(serializer.data)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(response_data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def featured(self, request):
        featured = self.get_queryset().filter(is_featured=True)[:6]
        serializer = PropertyListSerializer(featured, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def similar(self, request):
        property_type = request.query_params.get('property_type')
        property_id = request.query_params.get('property_id')
        
        if not property_type or not property_id:
            return Response({
                'error': 'property_type and property_id parameters are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        similar = self.get_queryset().filter(
            property_type=property_type,
            status='available'
        ).exclude(id=property_id)[:3]
        
        serializer = PropertyListSerializer(similar, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def search(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        property_obj = self.get_object()
        return Response({
            'views_count': property_obj.views_count,
            'favorite_count': property_obj.favorited_by.count(),
            'review_count': property_obj.reviews.count(),
            'average_rating': property_obj.reviews.aggregate(Avg('rating'))['rating__avg'] or 0
        }) 