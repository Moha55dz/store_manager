from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.db.models import Sum, Count

# استيراد النماذج (Models)
from .models import (
    Customer, Expense, Supplier, Employee, MaintenanceTask,
    Attendance, ElectronicService, Installment, DeliveryTracker,
    PurchasedPhone, Treasury
)

# Create your views here.

def login(request):
    """صفحة تسجيل الدخول"""
    
    if request.user.is_authenticated:
        return redirect('dashboard_home')
    
    error_message = None

    if request.method == 'POST':
        user_name = request.POST.get('username')
        user_pass = request.POST.get('password')

        user = authenticate(request, username=user_name, password=user_pass)

        if user is not None:
            auth_login(request, user)
            return redirect('dashboard_home')
        else:
            error_message = "اسم المستخدم أو كلمة المرور غير صحيحة!"

    return render(request, 'login.html', {'error_message': error_message})


@login_required(login_url='/login/')
def dashboard_home(request):
    """الصفحة الرئيسية للوحة التحكم - مع حساب الإحصائيات"""
    
    # 1. حساب مجموع سعر الخدمات الإلكترونية
    total_electronic_services_price = ElectronicService.objects.aggregate(total=Sum('price'))['total'] or 0
    
    # 2. حساب تتبع الطلبيات
    delivery_orders_count = DeliveryTracker.objects.count()
    
    # 3. حساب إجمالي المبالغ المتبقية للأقساط
    total_remaining_installments = Installment.objects.aggregate(total=Sum('remaining_amount'))['total'] or 0
    
    # 4. حساب مجموع الرواتب
    total_salaries = Employee.objects.aggregate(total=Sum('salary'))['total'] or 0
    
    # 5. حساب الخزينة (يتم حسابه لاحقاً بالأسفل بعد حساب كل المتغيرات المطلوبة)
    
    # 6. حساب التوصيلات المكتملة والأرباح منها
    completed_deliveries = DeliveryTracker.objects.filter(status=True).count()
    total_deliveries = DeliveryTracker.objects.count()
    total_delivery_earnings = DeliveryTracker.objects.aggregate(total=Sum('delivery_price'))['total'] or 0
    
    # 7. حساب الحضور اليومي
    today_attendance = Attendance.objects.filter(is_present=True).count()
    
    # 8. حساب عدد المستخدمين
    users_count = User.objects.count()
    
    # 9. حساب عدد العمال
    employees_count = Employee.objects.count()
    
    # 10. حساب عدد الموردين
    suppliers_count = Supplier.objects.count()
    
    # 11. حساب مجموع ديون الزبائن
    total_customer_debts = Customer.objects.aggregate(total=Sum('debt'))['total'] or 0
    
    # 12. حساب مجموع ديون الموردين
    total_supplier_debts = Supplier.objects.aggregate(total=Sum('debt'))['total'] or 0
    
    # 13. حساب مجموع المصاريف
    total_expenses = Expense.objects.aggregate(total=Sum('amount'))['total'] or 0
    
    # 14. حساب عدد الهواتف المشتراة
    phones_purchased_count = PurchasedPhone.objects.count()
    
    # 15. حساب مجموع المبالغ المستعملة (سعر الشراء الكلي)
    total_spent_on_phones = PurchasedPhone.objects.aggregate(total=Sum('purchase_price'))['total'] or 0
    
    # 16. حساب الصيانة الجارية والمعلقة
    pending_maintenance = MaintenanceTask.objects.filter(status__in=['pending', 'in_progress']).count()
    total_maintenance = MaintenanceTask.objects.count()
    completed_maintenance = MaintenanceTask.objects.filter(status='completed').count()
    maintenance_status = f"{total_maintenance}/{completed_maintenance}"
    
    # 17. حساب الصيانة الخارجية
    external_maintenance = MaintenanceTask.objects.filter(status='external').count()
    
    # حساب الخزينة بالصيغة المالية الشاملة
    # الخزينة = رأس المال الافتتاحي + التدفقات النقدية الداخلة - التدفقات النقدية الخارجة
    treasury_obj = Treasury.objects.first()
    initial_capital = treasury_obj.initial_capital if treasury_obj else 0

    # التدفقات النقدية الداخلة
    completed_maintenance_revenue = MaintenanceTask.objects.filter(status='completed').aggregate(total=Sum('cost'))['total'] or 0
    total_paid_installments = Installment.objects.aggregate(total=Sum('paid_amount'))['total'] or 0
    total_phone_sales_revenue = PurchasedPhone.objects.filter(is_sold=True).aggregate(total=Sum('selling_price'))['total'] or 0
    actual_phone_sales_cash = total_phone_sales_revenue - total_customer_debts

    # التدفقات النقدية الخارجة
    actual_phone_purchase_cash = total_spent_on_phones - total_supplier_debts

    total_treasury = (
        initial_capital
        + total_electronic_services_price
        + completed_maintenance_revenue
        + total_paid_installments
        + total_delivery_earnings
        + actual_phone_sales_cash
        - total_expenses
        - total_salaries
        - actual_phone_purchase_cash
    )

    # وضع جميع البيانات في قاموس Context لتمريرها إلى الـ HTML
    context = {
        'total_electronic_services_price': total_electronic_services_price,
        'delivery_orders_count': delivery_orders_count,
        'total_remaining_installments': total_remaining_installments,
        'total_salaries': total_salaries,
        'total_treasury': total_treasury,
        'completed_deliveries': completed_deliveries,
        'total_deliveries': total_deliveries,
        'total_delivery_earnings': total_delivery_earnings,
        'today_attendance': today_attendance,
        'users_count': users_count,
        'employees_count': employees_count,
        'suppliers_count': suppliers_count,
        'total_customer_debts': total_customer_debts,
        'total_supplier_debts': total_supplier_debts,
        'total_expenses': total_expenses,
        'phones_purchased_count': phones_purchased_count,
        'total_spent_on_phones': total_spent_on_phones,
        'maintenance_status': maintenance_status,
        'external_maintenance': external_maintenance,
    }
    
    return render(request, 'dashboard/home.html', context)


def logout(request):
    """تسجيل الخروج"""
    auth_logout(request)
    return redirect('login')


@login_required
def manage_users_view(request):
    """صفحة إدارة المستخدمين - متاحة فقط للمسؤولين والسوبريوزر"""
    # حماية الصفحة: إذا لم يكن المستخدم سوبر أو ليس في مجموعة Admin يتم طرده
    is_admin = request.user.is_superuser or request.user.groups.filter(name='Admin').exists()
    if not is_admin:
        return redirect('dashboard_home')

    all_users = User.objects.all().prefetch_related('groups').order_by('id')

    if request.method == 'POST':
        user_name = request.POST.get('username', '').strip()
        user_pass = request.POST.get('password', '').strip()
        role = request.POST.get('role')

        if not user_name or not user_pass:
            messages.error(request, 'يجب تعبئة جميع الحقول المطلوبة!')
        elif User.objects.filter(username=user_name).exists():
            messages.error(request, f'اسم المستخدم «{user_name}» موجود بالفعل!')
        elif role not in ['Admin', 'Normal_User']:
            messages.error(request, 'الرتبة المختارة غير صحيحة!')
        else:
            try:
                group = Group.objects.get(name=role)
                new_user = User.objects.create_user(username=user_name, password=user_pass)
                new_user.groups.add(group)
                messages.success(request, f'تم إنشاء حساب «{user_name}» بنجاح كـ {role}!')
                return redirect('manage_users')
            except Group.DoesNotExist:
                messages.error(request, f'مجموعة «{role}» غير موجودة. تأكد من إنشائها أولاً من لوحة تحكم Django.')

    context = {
        'users': all_users,
    }
    return render(request, 'dashboard/manage_users.html', context)


@login_required
def delete_user_view(request, user_id):
    """حذف مستخدم - متاح فقط للمسؤولين والسوبريوزر"""
    is_admin = request.user.is_superuser or request.user.groups.filter(name='Admin').exists()
    if not is_admin:
        return redirect('dashboard_home')

    if request.method == 'POST':
        try:
            user_to_delete = User.objects.get(id=user_id)
            # منع المسؤول من حذف نفسه
            if user_to_delete == request.user:
                messages.error(request, 'لا يمكنك حذف حسابك الخاص!')
            # منع حذف السوبريوزر
            elif user_to_delete.is_superuser:
                messages.error(request, 'لا يمكن حذف حساب مدير النظام!')
            else:
                username = user_to_delete.username
                user_to_delete.delete()
                messages.success(request, f'تم حذف حساب «{username}» بنجاح!')
        except User.DoesNotExist:
            messages.error(request, 'المستخدم غير موجود!')

    return redirect('manage_users')