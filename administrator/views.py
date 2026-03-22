from django.contrib.auth import get_user_model
from django.shortcuts import render
from django.urls import reverse



from django.views.generic import TemplateView
from accounts.mixins import RoleRequiredMixin
from django.contrib.auth.mixins import LoginRequiredMixin


class AdminDashboardView(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
    template_name = "administrator/dashboard.html"
    allowed_roles = ["admin"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        orders = (
            Order.objects.select_related("user", "table")
            .prefetch_related("items__menu_item")
            .order_by("-created_at")
        )

        table_filter = self.request.GET.get("table", "").strip()
        customer_filter = self.request.GET.get("customer", "").strip()

        if table_filter:
            orders = orders.filter(table__number=table_filter)

        if customer_filter:
            orders = orders.filter(user__username__icontains=customer_filter)

        context["orders"] = orders
        context["table_filter"] = table_filter
        context["customer_filter"] = customer_filter
        context["tables"] = Table.objects.order_by("number")
        context["customers"] = (
            get_user_model().objects.filter(role="customer").order_by("username")
        )
        return context

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Sum
from django.utils.timezone import now
from datetime import timedelta

from accounts.mixins import RoleRequiredMixin
from orders.models import Order
from payments.models import Payment
from feedback.models import Feedback


class AdminAnalyticsView(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
    template_name = "administrator/analytics.html"
    allowed_roles = ["admin"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        last_7_days = now() - timedelta(days=7)
        owned_orders = Order.objects.filter(table__owner=self.request.user)
        owned_payments = Payment.objects.filter(order__table__owner=self.request.user)
        owned_feedback = Feedback.objects.filter(order__table__owner=self.request.user)

        context["total_orders"] = owned_orders.count()
        context["pending_orders"] = owned_orders.filter(status="pending").count()
        context["preparing_orders"] = owned_orders.filter(status="preparing").count()
        context["completed_orders"] = owned_orders.filter(status="served").count()

        context["total_revenue"] = (
            owned_payments.filter(is_success=True)
            .aggregate(total=Sum("amount"))["total"] or 0
        )

        context["weekly_revenue"] = (
            owned_payments.filter(is_success=True, paid_at__gte=last_7_days)
            .aggregate(total=Sum("amount"))["total"] or 0
        )

        context["total_feedbacks"] = owned_feedback.count()
        context["orders_by_day"] = (
            owned_orders.filter(created_at__gte=last_7_days)
            .values("created_at__date")
            .annotate(count=Count("id"))
            .order_by("created_at__date")
        )

        return context
    
#menulist
from django.views.generic import ListView
from menu.models import MenuItem

class MenuManageView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    model = MenuItem
    template_name = "administrator/menu_list.html"
    allowed_roles = ["admin"]

    def get_queryset(self):
        return MenuItem.objects.filter(owner=self.request.user).select_related("category")

#Add Item

from django.views import View
from django.shortcuts import redirect
from menu.models import Category

class MenuCreateView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = ["admin"]

    def get(self, request):
        return render(request,"administrator/menu_add.html",
            {"categories": Category.objects.filter(owner=request.user).order_by("name")}
        )

    def post(self, request):
        MenuItem.objects.create(
            owner=request.user,
            name=request.POST["name"],
            price=request.POST["price"],
            category_id=request.POST["category"],
            is_available="available" in request.POST
        )
        return redirect("administrator:admin-menu")
#Edit Menu
class MenuUpdateView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = ["admin"]

    def get(self, request, pk):
        item = get_object_or_404(MenuItem, id=pk, owner=request.user)
        return render(request,"administrator/menu_edit.html",
            {"item": item, "categories": Category.objects.filter(owner=request.user).order_by("name")}
        )

    def post(self, request, pk):
        item = get_object_or_404(MenuItem, id=pk, owner=request.user)
        item.name = request.POST["name"]
        item.price = request.POST["price"]
        item.category_id = request.POST["category"]
        item.is_available = "available" in request.POST
        item.save()
        return redirect("administrator:admin-menu")
#Delete Menu

class MenuDeleteView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = ["admin"]

    def get(self, request, pk):
        get_object_or_404(MenuItem, id=pk, owner=request.user).delete()
        return redirect("administrator:admin-menu")
#Qr generator view
import qrcode
from django.conf import settings
from django.core.files import File
from io import BytesIO
from menu.models import Table

class GenerateQRView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = ["admin"]

    def get(self, request, table_id):
        table = Table.objects.get(id=table_id)

        url = f"{request.build_absolute_uri('/')}menu/table/{table.uuid}/"

        img = qrcode.make(url)
        buffer = BytesIO()
        img.save(buffer)

        table.qr_code.save(
            f"table_{table.number}.png",
            File(buffer),
            save=True
        )

        return redirect("admin-tables")
#orders dasboard

from orders.models import Order

class OrdersDashboardView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    model = Order
    template_name = "administrator/orders.html"
    allowed_roles = ["admin"]
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = (
            Order.objects.select_related("user", "table")
            .prefetch_related("items__menu_item")
            .filter(table__owner=self.request.user)
            .order_by("-created_at")
        )

        table_filter = self.request.GET.get("table", "").strip()
        customer_filter = self.request.GET.get("customer", "").strip()

        if table_filter:
            queryset = queryset.filter(table__number=table_filter)
        if customer_filter:
            queryset = queryset.filter(user__username__icontains=customer_filter)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["table_filter"] = self.request.GET.get("table", "").strip()
        context["customer_filter"] = self.request.GET.get("customer", "").strip()
        context["tables"] = Table.objects.filter(owner=self.request.user).order_by("number")
        return context
#Payments dashboard

from payments.models import Payment

class PaymentsDashboardView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    model = Payment
    template_name = "administrator/payments.html"
    allowed_roles = ["admin"]

    def get_queryset(self):
        queryset = Payment.objects.select_related("order__user", "order__table").filter(order__table__owner=self.request.user).order_by("-paid_at")

        table_filter = self.request.GET.get("table", "").strip()
        customer_filter = self.request.GET.get("customer", "").strip()

        if table_filter:
            queryset = queryset.filter(order__table__number=table_filter)
        if customer_filter:
            queryset = queryset.filter(order__user__username__icontains=customer_filter)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["table_filter"] = self.request.GET.get("table", "").strip()
        context["customer_filter"] = self.request.GET.get("customer", "").strip()
        context["tables"] = Table.objects.filter(owner=self.request.user).order_by("number")
        return context
from accounts.models import User
#Staff Management
class StaffListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    model = User
    template_name = "administrator/staff.html"
    allowed_roles = ["admin"]

    def get_queryset(self):
        return User.objects.exclude(role="customer")
    
from django.views.generic import ListView, View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import make_password
from django.contrib.auth.mixins import LoginRequiredMixin

from accounts.models import User
from orders.models import Order
from payments.models import Payment
from accounts.mixins import RoleRequiredMixin
class StaffListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    template_name = "administrator/staffs.html"
    allowed_roles = ["admin"]
    model = User

    def get_queryset(self):
        return User.objects.filter(role="kitchen", managed_by=self.request.user)

class StaffCreateView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = ["admin"]

    def get(self, request):
        return render(request, "administrator/add_staff.html", {"form_data": {}})

    def post(self, request):
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")

        context = {
            "form_data": {
                "username": username,
                "email": email,
            }
        }

        if User.objects.filter(username__iexact=username).exists():
            context["error_message"] = "Username already exists. Please choose a different username."
            return render(request, "administrator/add_staff.html", context)

        if User.objects.filter(email__iexact=email).exists():
            context["error_message"] = "Email already exists. Please use a different email address."
            return render(request, "administrator/add_staff.html", context)

        User.objects.create(
            username=username,
            password=make_password(password),
            role="kitchen",
            email=email,
            managed_by=request.user,
        )
        return redirect("administrator:admin-staff")
class StaffUpdateView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = ["admin"]

    def get(self, request, pk):
        user = get_object_or_404(User, pk=pk, role="kitchen", managed_by=request.user)
        return render(
            request,
            "administrator/edit_staff.html",
            {"staff": user, "form_data": {"email": user.email}},
        )

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk, role="kitchen", managed_by=request.user)
        new_email = request.POST.get("email", "").strip()
        new_password = request.POST.get("password", "").strip()

        if new_email and User.objects.filter(email__iexact=new_email).exclude(pk=user.pk).exists():
            return render(
                request,
                "administrator/edit_staff.html",
                {
                    "staff": user,
                    "form_data": {"email": new_email},
                    "error_message": "Email already exists. Please use a different email address.",
                },
            )

        if new_email:
            user.email = new_email
        if new_password:
            user.password = make_password(new_password)
        user.save()
        return redirect("administrator:admin-staff")
class StaffDeleteView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = ["admin"]

    def get(self, request, pk):
        user = get_object_or_404(User, pk=pk, role="kitchen", managed_by=request.user)
        user.delete()
        return redirect("administrator:admin-staff")


from django.views.generic import TemplateView, View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from accounts.mixins import RoleRequiredMixin
from menu.models import Table, TableQR


# LIST TABLES
class AdminTableListView(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
    template_name = "administrator/tables.html"
    allowed_roles = ["admin"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tables"] = Table.objects.filter(owner=self.request.user)
        context["qr_map"] = {
            qr.table_id: qr for qr in TableQR.objects.select_related("table")
        }
        
        return context


# ADD TABLE
class AddTableView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = ["admin"]

    def post(self, request):
        number = request.POST.get("number")
        capacity = request.POST.get("capacity")

        Table.objects.create(owner=request.user, number=number, capacity=capacity)
        return redirect("administrator:admin-tables")


# DELETE TABLE
class DeleteTableView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = ["admin"]

    def post(self, request, pk):
        get_object_or_404(Table, id=pk, owner=request.user).delete()
        return redirect("administrator:admin-tables")
from django.conf import settings
from django.core.files.base import ContentFile
from urllib.parse import urlencode

def generate_qr_image(code):
    
    img = qrcode.make(url)
    path = f"{settings.MEDIA_ROOT}/qr/{code}.png"
    img.save(path)

# GENERATE QR
class GenerateQRView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = ["admin"]

    def post(self, request, pk):
        table = get_object_or_404(Table, id=pk, owner=request.user)
        
        qr_obj, created = TableQR.objects.get_or_create(table=table)

        if not qr_obj.qr_image:
            login_url = request.build_absolute_uri(reverse("accounts:login"))
            next_url = reverse('menu:table-menu', args=[table.id])
            url = f"{login_url}?{urlencode({'next': next_url})}"

            
            qr = qrcode.make(url)
            # Create buffer (THIS WAS MISSING OR WRONG)
            qr_buffer = BytesIO()
            qr.save(qr_buffer, format="PNG")

            # Create or get QR model
            qr_obj, created = TableQR.objects.get_or_create(table=table)

            # Save image
            qr_obj.qr_image     .save(
                f"table_{table.number}.png",
                ContentFile(qr_buffer.getvalue()),
                save=True
            )
        return redirect("administrator:admin-tables")

from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from accounts.mixins import RoleRequiredMixin
from menu.models import Category


# LIST
class CategoryListView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = ["admin"]

    def get(self, request):
        categories = Category.objects.filter(owner=request.user).order_by("name")
        return render(request, "administrator/categories/list.html", {
            "categories": categories
        })


# CREATE
class CategoryCreateView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = ["admin"]

    def get(self, request):
        return render(request, "administrator/categories/add.html")

    def post(self, request):
        name = request.POST.get("name")

        if name:
            Category.objects.create(owner=request.user, name=name)

        return redirect("administrator:category-list")


# UPDATE
class CategoryUpdateView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = ["admin"]

    def get(self, request, pk):
        category = get_object_or_404(Category, pk=pk, owner=request.user)
        return render(request, "administrator/categories/edit.html", {
            "category": category
        })

    def post(self, request, pk):
        category = get_object_or_404(Category, pk=pk, owner=request.user)

        category.name = request.POST.get("name")
        category.save()

        return redirect("administrator:category-list")


# DELETE
class CategoryDeleteView(LoginRequiredMixin, RoleRequiredMixin, View):
    allowed_roles = ["admin"]

    def post(self, request, pk):
        category = get_object_or_404(Category, pk=pk, owner=request.user)
        category.delete()
        return redirect("administrator:category-list")
