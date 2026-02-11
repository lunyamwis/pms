from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView,
    TemplateView, View
)
from django.db.models import Q, Count, Avg
from django.http import JsonResponse
from django.urls import reverse_lazy
from .models import Property, PropertyImage, PropertyReview
from messaging.models import PropertyInquiry
from agents.models import Agent
from .forms import (
    PropertyForm, PropertyImageForm, PropertyReviewForm,
    PropertySearchForm, PropertyInquiryForm
)

class HomeView(TemplateView):
    template_name = 'pages/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get featured properties
        featured_properties = Property.objects.filter(
            is_featured=True, 
            status='available'
        ).select_related('owner', 'agent').prefetch_related('images')[:6]
        
        # If we don't have enough featured properties, add recent ones
        if featured_properties.count() < 6:
            recent_properties = Property.objects.filter(
                status='available'
            ).exclude(
                id__in=[p.id for p in featured_properties]
            ).select_related('owner', 'agent').prefetch_related('images').order_by('-created_at')[:6-featured_properties.count()]
            
            # Combine featured and recent properties
            context['featured_properties'] = list(featured_properties) + list(recent_properties)
        else:
            context['featured_properties'] = featured_properties
        
        # Get featured agents with their property count and ratings
        agents = Agent.objects.annotate(
            owned_count=Count('user__owned_properties', filter=Q(user__owned_properties__status='available')),
            managed_count=Count('user__managed_properties', filter=Q(user__managed_properties__status='available')),
            properties_count=Count('user__owned_properties', filter=Q(user__owned_properties__status='available')) + 
                           Count('user__managed_properties', filter=Q(user__managed_properties__status='available')),
            average_rating=Avg('user__property_reviews__rating')
        ).order_by('-properties_count')[:4]
        
        context['featured_agents'] = agents
        
        return context

class PropertyListView(ListView):
    model = Property
    template_name = 'properties/property_list.html'
    context_object_name = 'properties'
    paginate_by = 12

    def get_queryset(self):
        queryset = Property.objects.filter(status='available').select_related('agent', 'owner').prefetch_related('images')
        
        # Handle sorting
        sort = self.request.GET.get('sort', 'latest')
        if sort == 'price_low':
            queryset = queryset.order_by('price')
        elif sort == 'price_high':
            queryset = queryset.order_by('-price')
        elif sort == 'beds':
            queryset = queryset.order_by('-bedrooms')
        elif sort == 'baths':
            queryset = queryset.order_by('-bathrooms')
        elif sort == 'area':
            queryset = queryset.order_by('-area')
        else:  # default to latest
            queryset = queryset.order_by('-created_at')
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = PropertySearchForm()
        return context

class PropertySearchView(ListView):
    model = Property
    template_name = 'properties/property_search.html'
    context_object_name = 'properties'
    paginate_by = 12

    def get_queryset(self):
        form = PropertySearchForm(self.request.GET)
        queryset = Property.objects.filter(status='available').select_related('agent')

        if form.is_valid():
            keyword = form.cleaned_data.get('keyword')
            property_type = form.cleaned_data.get('property_type')
            listing_type = form.cleaned_data.get('listing_type')
            price_range = form.cleaned_data.get('price_range')
            bedrooms = form.cleaned_data.get('bedrooms')
            bathrooms = form.cleaned_data.get('bathrooms')
            min_area = form.cleaned_data.get('min_area')
            max_area = form.cleaned_data.get('max_area')
            location = form.cleaned_data.get('location')

            if keyword:
                queryset = queryset.filter(
                    Q(title__icontains=keyword) |
                    Q(description__icontains=keyword) |
                    Q(address__icontains=keyword)
                )

            if property_type:
                queryset = queryset.filter(property_type=property_type)

            if listing_type:
                queryset = queryset.filter(listing_type=listing_type)

            if price_range:
                min_price, max_price = self._parse_price_range(price_range)
                if min_price is not None:
                    queryset = queryset.filter(price__gte=min_price)
                if max_price is not None:
                    queryset = queryset.filter(price__lte=max_price)

            if bedrooms:
                queryset = queryset.filter(bedrooms__gte=int(bedrooms))

            if bathrooms:
                queryset = queryset.filter(bathrooms__gte=float(bathrooms))

            if min_area:
                queryset = queryset.filter(area__gte=min_area)

            if max_area:
                queryset = queryset.filter(area__lte=max_area)

            if location:
                queryset = queryset.filter(
                    Q(city__icontains=location) |
                    Q(state__icontains=location) |
                    Q(zip_code__icontains=location)
                )

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = PropertySearchForm(self.request.GET)
        return context

    def _parse_price_range(self, price_range):
        if not price_range:
            return None, None
        if price_range == '1000000-plus':
            return 1000000, None
        try:
            min_price, max_price = price_range.split('-')
            return int(min_price), int(max_price)
        except ValueError:
            return None, None

class PropertyDetailView(DetailView):
    model = Property
    template_name = 'properties/property_detail.html'
    context_object_name = 'property'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        property_obj = self.get_object()
        
        # Increment views count
        property_obj.views_count += 1
        property_obj.save()

        context['similar_properties'] = Property.objects.filter(
            property_type=property_obj.property_type,
            status='available'
        ).exclude(id=property_obj.id)[:3]
        
        context['property_images'] = property_obj.images.all()
        context['reviews'] = property_obj.reviews.select_related('user').order_by('-created_at')
        context['review_form'] = PropertyReviewForm()
        context['inquiry_form'] = PropertyInquiryForm()
        
        if self.request.user.is_authenticated:
            context['is_favorited'] = property_obj.favorited_by.filter(id=self.request.user.id).exists()
        
        return context

class PropertyCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Property
    form_class = PropertyForm
    template_name = 'properties/property_form.html'
    success_url = reverse_lazy('properties:list')

    def test_func(self):
        return self.request.user.role in ['agent', 'seller']

    def form_valid(self, form):
        try:
            form.instance.owner = self.request.user
            # If the user is an agent, they are also the managing agent
            if self.request.user.role == 'agent':
                form.instance.agent = self.request.user
            
            # Save the form to create the property
            response = super().form_valid(form)
            
            # Handle gallery images
            gallery_images = self.request.FILES.getlist('gallery_images')
            if gallery_images:
                for idx, image in enumerate(gallery_images):
                    PropertyImage.objects.create(
                        property=self.object,
                        image=image,
                        is_primary=(idx == 0 and not self.object.main_image),  # First image is primary if no main image
                        caption=f"Property Image {idx + 1}"
                    )
            
            messages.success(self.request, 'Property created successfully!')
            return response
        except Exception as e:
            messages.error(self.request, f'Error creating property: {str(e)}')
            return self.form_invalid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)

class PropertyUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Property
    form_class = PropertyForm
    template_name = 'properties/property_form.html'

    def test_func(self):
        property_obj = self.get_object()
        # Allow both the owner and the managing agent to update
        return (self.request.user == property_obj.owner or 
                (property_obj.agent and self.request.user == property_obj.agent))

    def get_success_url(self):
        return reverse_lazy('properties:detail', kwargs={'slug': self.object.slug})

    def form_valid(self, form):
        try:
            # Save the form first
            response = super().form_valid(form)
            
            # Handle new gallery images
            gallery_images = self.request.FILES.getlist('gallery_images')
            if gallery_images:
                # Get the current count of existing images
                existing_count = self.object.images.count()
                for idx, image in enumerate(gallery_images):
                    PropertyImage.objects.create(
                        property=self.object,
                        image=image,
                        is_primary=False,  # Don't override existing primary
                        caption=f"Property Image {existing_count + idx + 1}"
                    )
            
            messages.success(self.request, 'Property updated successfully!')
            return response
        except Exception as e:
            messages.error(self.request, f'Error updating property: {str(e)}')
            return self.form_invalid(form)

class PropertyDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Property
    template_name = 'properties/property_confirm_delete.html'
    success_url = reverse_lazy('properties:list')

    def test_func(self):
        property_obj = self.get_object()
        # Only the owner can delete the property
        return self.request.user == property_obj.owner

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Property deleted successfully!')
        return super().delete(request, *args, **kwargs)

class PropertyImageUploadView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        property_obj = get_object_or_404(Property, slug=self.kwargs['slug'])
        return self.request.user == property_obj.agent

    def post(self, request, slug):
        property_obj = get_object_or_404(Property, slug=slug)
        form = PropertyImageForm(request.POST, request.FILES)
        
        if form.is_valid():
            image = form.save(commit=False)
            image.property = property_obj
            image.save()
            
            return JsonResponse({
                'success': True,
                'image_url': image.image.url,
                'image_id': image.id
            })
        
        return JsonResponse({'success': False, 'errors': form.errors})

class PropertyImageDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        image = get_object_or_404(PropertyImage, id=self.kwargs['image_id'])
        property_obj = image.property
        return (self.request.user == property_obj.owner or 
                (property_obj.agent and self.request.user == property_obj.agent))

    def delete(self, request, image_id):
        image = get_object_or_404(PropertyImage, id=image_id)
        image.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Image deleted successfully'
        })

class PropertyReviewCreateView(LoginRequiredMixin, View):
    def post(self, request, slug):
        property_obj = get_object_or_404(Property, slug=slug)
        form = PropertyReviewForm(request.POST)
        
        if form.is_valid():
            review = form.save(commit=False)
            review.property = property_obj
            review.user = request.user
            review.save()
            
            messages.success(request, 'Review submitted successfully!')
            return redirect('properties:detail', slug=slug)
        
        messages.error(request, 'Error submitting review. Please try again.')
        return redirect('properties:detail', slug=slug)

class PropertyFavoriteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        property_obj = get_object_or_404(Property, pk=pk)
        user = request.user
        
        if property_obj.favorited_by.filter(id=user.id).exists():
            property_obj.favorited_by.remove(user)
            is_favorited = False
        else:
            property_obj.favorited_by.add(user)
            is_favorited = True
        
        return JsonResponse({
            'success': True,
            'is_favorited': is_favorited
        })

class PropertyInquiryView(LoginRequiredMixin, View):
    def post(self, request, pk):
        property_obj = get_object_or_404(Property, pk=pk)
        form = PropertyInquiryForm(request.POST)
        
        if form.is_valid():
            inquiry = PropertyInquiry.objects.create(
                property=property_obj,
                user=request.user,
                message=form.cleaned_data['message'],
                phone=form.cleaned_data['phone'],
                email=form.cleaned_data['email'],
                preferred_contact_method=form.cleaned_data['preferred_contact']
            )
            
            messages.success(request, 'Your inquiry has been sent successfully!')
            return redirect('properties:detail', slug=property_obj.slug)
        
        messages.error(request, 'Error sending inquiry. Please try again.')
        return redirect('properties:detail', slug=property_obj.slug)

class PropertyMapView(TemplateView):
    template_name = 'properties/property_map.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        properties = Property.objects.filter(
            status='available',
            latitude__isnull=False,
            longitude__isnull=False
        ).values('id', 'title', 'price', 'latitude', 'longitude', 'slug')
        context['properties_json'] = list(properties)
        return context

class NewsletterSubscriptionView(View):
    def post(self, request):
        email = request.POST.get('email')
        if email:
            # Here you would typically:
            # 1. Validate the email
            # 2. Save to your newsletter subscription model
            # 3. Send a confirmation email
            # For now, we'll just show a success message
            messages.success(request, 'Thank you for subscribing to our newsletter!')
        else:
            messages.error(request, 'Please provide a valid email address.')
        return redirect('properties:home')

class PropertyMarkSoldView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        property_obj = get_object_or_404(Property, slug=self.kwargs['slug'])
        return (self.request.user == property_obj.owner or 
                (property_obj.agent and self.request.user == property_obj.agent))

    def post(self, request, slug):
        property_obj = get_object_or_404(Property, slug=slug)
        property_obj.status = 'sold'
        property_obj.save()
        messages.success(request, 'Property has been marked as sold.')
        return redirect('properties:detail', slug=slug)

class ContactView(View):
    def get(self, request):
        return render(request, 'pages/contact.html')

    def post(self, request):
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # Here you would typically send an email or save to database
        # For now, just show a success message
        messages.success(request, 'Thank you for your message. We will get back to you soon!')
        return redirect('contact')
