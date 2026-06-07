import os
import re

models = [
    ('Customer', 'customer', 'customer_list'),
    ('Expense', 'expense', 'expense_list'),
    ('Employee', 'employee', 'employee_list'),
    ('Attendance', 'attendance', 'attendance_list'),
    ('Supplier', 'supplier', 'supplier_list'),
    ('PurchasedPhone', 'purchased_phone', 'purchased_phone_list'),
    ('ElectronicService', 'electronic_service', 'electronic_service_list'),
    ('Installment', 'installment', 'installment_list'),
    ('DeliveryTracker', 'delivery_tracker', 'delivery_tracker_list'),
    ('Treasury', 'treasury', 'treasury_list'),
    ('MaintenanceTask', 'maintenance', 'maintenance_list'),
]

views_file = r'c:\Users\ThinkPad Yoga\Desktop\store_manager\store_manager\dashboard\views.py'
urls_file = r'c:\Users\ThinkPad Yoga\Desktop\store_manager\store_manager\dashboard\urls.py'
templates_dir = r'c:\Users\ThinkPad Yoga\Desktop\store_manager\store_manager\templates\dashboard'

# 1. Update views.py
with open(views_file, 'r', encoding='utf-8') as f:
    views_content = f.read()

new_views = ""
for model_name, name, redirect_url in models:
    if f"def delete_{name}(" not in views_content:
        new_views += f"""
@login_required
def delete_{name}(request, pk):
    item = get_object_or_404({model_name}, pk=pk)
    item.delete()
    return redirect(request.META.get('HTTP_REFERER', '{redirect_url}'))
"""
if new_views:
    with open(views_file, 'a', encoding='utf-8') as f:
        f.write("\n" + new_views)
    print("Updated views.py")

# 2. Update urls.py
with open(urls_file, 'r', encoding='utf-8') as f:
    urls_content = f.read()

urls_changed = False
for model_name, name, redirect_url in models:
    url_pattern = f"path('{name.replace('_', '-')}/delete/<int:pk>/', views.delete_{name}, name='delete_{name}'),"
    if url_pattern not in urls_content:
        # Find the edit url and insert after it
        edit_pattern = f"path('{name.replace('_', '-')}/edit/<int:pk>/', views.edit_{name}, name='edit_{name}'),"
        if edit_pattern in urls_content:
            urls_content = urls_content.replace(edit_pattern, edit_pattern + "\n    " + url_pattern)
            urls_changed = True
        else:
            # For maintenance
            edit_m_pattern = "path('maintenance/edit/<int:pk>/', views.edit_maintenance, name='edit_maintenance'),"
            if name == 'maintenance' and edit_m_pattern in urls_content:
                urls_content = urls_content.replace(edit_m_pattern, edit_m_pattern + "\n    " + url_pattern)
                urls_changed = True

if urls_changed:
    with open(urls_file, 'w', encoding='utf-8') as f:
        f.write(urls_content)
    print("Updated urls.py")

# 3. Update all list templates
import glob
for list_file in glob.glob(os.path.join(templates_dir, '*_list.html')):
    with open(list_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if "delete_" in content and "حذف" in content:
        continue # Already added
        
    pattern = r'(<a href="{% url \'edit_[a-z_]+\' (item|task)\.id %}"[^>]*>.*?</a>)'
    
    def replacer(match):
        edit_link = match.group(1)
        m = re.search(r"{% url 'edit_([a-z_]+)' (item|task)\.id %}", edit_link)
        if m:
            model_n = m.group(1)
            var_n = m.group(2)
            delete_link = f'\n                    <span style="color: #ccc;">|</span>\n                    <a href="{{% url \'delete_{model_n}\' {var_n}.id %}}" style="color: #e74c3c; text-decoration: none; font-weight: bold; margin-right: 5px;" onclick="return confirm(\'هل أنت متأكد من الحذف؟ لا يمكن التراجع عن هذه العملية.\')">حذف 🗑️</a>'
            return edit_link + delete_link
        return edit_link

    new_content = re.sub(pattern, replacer, content)
    
    if new_content != content:
        with open(list_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {os.path.basename(list_file)}")
