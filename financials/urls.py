from django.urls import path
from . import views

app_name = 'financials'

urlpatterns = [
    path('', views.FinancialDashboardView.as_view(), name='dashboard'),
    path('cashbook/', views.CashbookView.as_view(), name='cashbook'),
    path('cashbook/add/', views.CashbookEntryCreateView.as_view(), name='add_entry'),
    path('cashbook/<int:pk>/edit/', views.CashbookEntryUpdateView.as_view(), name='edit_entry'),
    path('cashbook/<int:pk>/delete/', views.CashbookEntryDeleteView.as_view(), name='delete_entry'),
    path('cashbook/export/', views.ExportCashbookView.as_view(), name='export_cashbook'),
    path('receipts/', views.ReceiptListView.as_view(), name='receipt_list'),
    path('receipts/<int:pk>/', views.ReceiptDetailView.as_view(), name='receipt_detail'),
    path('report/', views.FinancialReportView.as_view(), name='report'),
    path('opening-balance/', views.SetOpeningBalanceView.as_view(), name='opening_balance'),
    path('api/chart-data/', views.FinancialChartDataView.as_view(), name='chart_data'),
]
