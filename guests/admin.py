from django.contrib import admin
from .models import Guest, GuestDocument, GuestReview


class GuestDocumentInline(admin.TabularInline):
    model = GuestDocument
    extra = 0


@admin.register(Guest)
class GuestAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'phone', 'email', 'nationality', 'is_vip', 'is_blacklisted', 'total_bookings']
    list_filter = ['is_vip', 'is_blacklisted', 'nationality']
    search_fields = ['first_name', 'last_name', 'phone', 'email']
    inlines = [GuestDocumentInline]

    def full_name(self, obj):
        return obj.full_name
