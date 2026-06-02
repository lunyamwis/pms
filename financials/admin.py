from django.contrib import admin
from .models import CashbookEntry, Receipt, Budget


@admin.register(CashbookEntry)
class CashbookEntryAdmin(admin.ModelAdmin):
    list_display = ['date','name','description','entry_type','category','amount','balance']
    list_filter = ['entry_type','category','date']
    search_fields = ['name','description','reference']
    date_hierarchy = 'date'
    readonly_fields = ['balance','created_at','updated_at']


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ['receipt_number','guest_name','property_name','total_amount','issued_at']
    search_fields = ['receipt_number','guest_name']
