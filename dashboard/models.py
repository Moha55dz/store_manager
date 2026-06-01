from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Customer(models.Model):
    name = models.CharField(max_length=150, verbose_name="اسم الزبون")
    phone = models.CharField(max_length=20, null=True, blank=True, verbose_name="رقم الهاتف")
    debt = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="ديون الزبون")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Expense(models.Model):
    title = models.CharField(max_length=200, verbose_name="عنوان المصروف")
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=5000.00, null=True, blank=True, verbose_name="المبلغ")
    date = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ المصروف")

    def __str__(self):
        return f"{self.title} - {self.amount} DA"

class Employee(models.Model):
    name = models.CharField(max_length=150, verbose_name="اسم العامل")
    phone = models.CharField(max_length=20, null=True, blank=True, verbose_name="رقم الهاتف")
    job_title = models.CharField(max_length=100, verbose_name="المسمى الوظيفي")
    salary = models.DecimalField(max_digits=10, decimal_places=2, default=25000.00, null=True, blank=True, verbose_name="الراتب الأساسي")
    
    def __str__(self):
        return self.name

class Attendance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name="العامل")
    date = models.DateField(auto_now_add=True, verbose_name="التاريخ")
    is_present = models.BooleanField(default=True, verbose_name="حاضر؟")
    note = models.CharField(max_length=255, null=True, blank=True, verbose_name="ملاحظات")

    def __str__(self):
        return f"{self.employee.name} - {self.date}"

class Supplier(models.Model):
    name = models.CharField(max_length=150, verbose_name="اسم المورد")
    phone = models.CharField(max_length=20, null=True, blank=True, verbose_name="رقم الهاتف")
    debt = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="ديون المورد")

    def __str__(self):
        return self.name

class PurchasedPhone(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, verbose_name="المورد")
    model_name = models.CharField(max_length=200, verbose_name="نوع الهاتف")
    imei = models.CharField(max_length=50, unique=True, verbose_name="رقم التسلسل (IMEI)")
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, default=15000.00, null=True, blank=True, verbose_name="سعر الشراء")
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, default=20000.00, null=True, blank=True, verbose_name="سعر البيع")
    date_purchased = models.DateField(auto_now_add=True, verbose_name="تاريخ الشراء")
    is_sold = models.BooleanField(default=False, verbose_name="تم البيع؟")

    def __str__(self):
        return self.model_name

class MaintenanceTask(models.Model):
    STATUS_CHOICES = (
        ('pending', 'قيد الانتظار'),
        ('in_progress', 'قيد الصيانة'),
        ('completed', 'مكتملة'),
        ('external', 'صيانة خارجية'),
    )
    customer_name = models.CharField(max_length=150, verbose_name="اسم الزبون")
    device_info = models.CharField(max_length=200, verbose_name="نوع الجهاز والمشكلة")
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=1000.00, null=True, blank=True, verbose_name="تكلفة الصيانة")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="حالة الصيانة")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الاستلام")

    def __str__(self):
        return f"{self.device_info} - {self.customer_name}"

class ElectronicService(models.Model):
    service_name = models.CharField(max_length=150, verbose_name="اسم الخدمة")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=1500.00, null=True, blank=True, verbose_name="السعر")
    date = models.DateTimeField(auto_now_add=True, verbose_name="التاريخ")

    def __str__(self):
        return self.service_name

class Installment(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name="الزبون")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=50000.00, null=True, blank=True, verbose_name="المبلغ الإجمالي")
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=10000.00, null=True, blank=True, verbose_name="المبلغ المدفوع")
    remaining_amount = models.DecimalField(max_digits=10, decimal_places=2, default=40000.00, null=True, blank=True, verbose_name="المبلغ المتبقي")
    due_date = models.DateField(verbose_name="تاريخ القسط القادم")

    def __str__(self):
        return f"قسط {self.customer.name}"

class DeliveryTracker(models.Model):
    order_details = models.CharField(max_length=250, verbose_name="تفاصيل الطلبية")
    delivery_person = models.CharField(max_length=100, verbose_name="عامل التوصيل")
    status = models.BooleanField(default=False, verbose_name="تم التوصيل؟")
    delivery_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="سعر التوصيل")

    def __str__(self):
        return self.order_details

class Treasury(models.Model):
    initial_capital = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="رأس المال الافتتاحي")

    class Meta:
        verbose_name = "الخزينة"
        verbose_name_plural = "الخزينة"

    def __str__(self):
        return f"الخزينة - رأس المال الافتتاحي: {self.initial_capital} DA"