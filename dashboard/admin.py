from django.contrib import admin
from .models import (
    Employee, Attendance, Supplier, PurchasedPhone, MaintenanceTask,
    ElectronicService, Customer, Expense, Installment, DeliveryTracker,
    Treasury
)

# Register your models here.

class PurchasedPhoneAdmin(admin.ModelAdmin):
    list_display = ('model_name', 'imei', 'purchase_price', 'selling_price', 'is_sold', 'date_purchased')
    list_filter = ('is_sold', 'date_purchased')
    search_fields = ('model_name', 'imei')

class TreasuryAdmin(admin.ModelAdmin):
    list_display = ('initial_capital',)

admin.site.register(Employee)
admin.site.register(Attendance)
admin.site.register(Supplier)
admin.site.register(PurchasedPhone, PurchasedPhoneAdmin)
admin.site.register(MaintenanceTask)
admin.site.register(ElectronicService)
admin.site.register(Customer)
admin.site.register(Expense)
admin.site.register(Installment)
admin.site.register(DeliveryTracker)
admin.site.register(Treasury, TreasuryAdmin)