from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from backend.models import User, Shop, Category, Product, ProductInfo, Parameter, ProductParameter, Order, OrderItem, \
    Contact, ConfirmEmailToken


class ProductParameterInline(admin.TabularInline):
    model = ProductParameter
    extra = 1


class ProductInline(admin.TabularInline):
    model = Product
    extra = 1


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Панель управления пользователями
    """
    model = User
    fieldsets = (
        (None, {'fields': ('email', )}),
        ('Personal info', {'fields': ('first_name', 'surname','last_name', 'company', 'position')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'type', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide', ),
            'fields': ('email', 'first_name', 'surname', 'last_name', 'password1', 'password2', 'is_active', 'is_staff',)
        }
         ),
    )
    list_display = ('email', 'first_name', 'last_name', 'surname', 'is_staff')


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    model = Shop
    fieldsets = (
        (None, {'fields': ('name', 'state')}),
        ('Additional Info', {'fields': ('url', 'user'),
                             'classes': ('collapse',)}),
    )
    list_display = ('name', 'state', 'url')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    model = Category
    inlines = [ProductInline]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    pass


@admin.register(ProductInfo)
class ProductInfoAdmin(admin.ModelAdmin):
    model = ProductInfo
    fieldsets = (
        (None, {'fields': ('product', 'model', 'external_id', 'quantity')}),
        ('Prices', {'fields': ('price', 'price_rrc')}),
    )
    list_display = ('product', 'external_id', 'price', 'price_rrc', 'quantity')
    ordering = ('external_id',)
    inlines = [ProductParameterInline]


@admin.register(Parameter)
class ParameterAdmin(admin.ModelAdmin):
    pass


@admin.register(ProductParameter)
class ProductParameterAdmin(admin.ModelAdmin):
    pass


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    model = Order
    fields = ('user', 'state', 'contact')
    list_display = ('user', 'dt', 'state')
    ordering = ('dt',)
    inlines = [
        OrderItemInline,
    ]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    pass


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    pass


@admin.register(ConfirmEmailToken)
class ConfirmEmailTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'key', 'created_at',)
