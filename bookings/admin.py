from django.contrib import admin
from .models import Booking, BookingPayment, BookingMessage, BookingNote


class BookingPaymentInline(admin.TabularInline):
    model = BookingPayment
    extra = 0


class BookingMessageInline(admin.TabularInline):
    model = BookingMessage
    extra = 0


class BookingNoteInline(admin.TabularInline):
    model = BookingNote
    extra = 0


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['booking_reference', 'guest', 'asset_property' , 'check_in_date', 'check_out_date', 'status', 'source', 'total_amount']
    list_filter = ['status', 'source', 'check_in_date']
    search_fields = ['booking_reference', 'guest__first_name', 'guest__last_name', 'guest__phone']
    inlines = [BookingPaymentInline, BookingMessageInline, BookingNoteInline]
    readonly_fields = ['booking_reference', 'total_nights', 'subtotal', 'total_amount', 'created_at', 'updated_at']
    date_hierarchy = 'check_in_date'


@admin.register(BookingPayment)
class BookingPaymentAdmin(admin.ModelAdmin):
    list_display = ['booking', 'amount', 'payment_method', 'status', 'paid_at']
    list_filter = ['status', 'payment_method']
