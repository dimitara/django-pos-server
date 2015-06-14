from django.contrib.auth.models import User, Group
from pos.models import Table, Product, Category, Employee, Order, OrderItem

from rest_framework import serializers


class EmployeeSerializer(serializers.HyperlinkedModelSerializer):
    name = serializers.ReadOnlyField()
    username = serializers.ReadOnlyField()
    userId = serializers.ReadOnlyField()

    class Meta:
        model = Employee
        fields = ('id', 'username', 'pin', 'name', 'userId')


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'url', 'username', 'email', 'groups')


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('id', 'url', 'name')

class TableSerializer(serializers.HyperlinkedModelSerializer):
    parentId = serializers.ReadOnlyField()

    class Meta:
        model = Table
        fields = ('id', 'number', 'nickname', 'taken', 'parent', 'booked', 'parentId')

class ProductSerializer(serializers.HyperlinkedModelSerializer):
    categoryId = serializers.ReadOnlyField()
    categoryNeatName = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = ('id', 'name', 'description', 'categoryId', 'price', 'availability', 'availabilityUpdated', 'order', 'categoryNeatName', 'available')

class OrderSerializer(serializers.HyperlinkedModelSerializer):
    table = serializers.PrimaryKeyRelatedField(queryset=Table.objects.all())
    operatedBy = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    openedBy = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    operatedById = serializers.ReadOnlyField()
    items = serializers.ReadOnlyField()

    class Meta:
        model = Order
        fields = ('id', 'table', 'total', 'discount', 'discountReason', 'notes', 'status', 'openedBy', 'operatedBy', 'operatedById', 'fis', 'items', 'reportedDate')

class OrderItemSerializer(serializers.HyperlinkedModelSerializer):
    productId = serializers.ReadOnlyField()
    productName = serializers.ReadOnlyField()
    productDesc = serializers.ReadOnlyField()
    productPrice = serializers.ReadOnlyField()
    tableName = serializers.ReadOnlyField()
    categoryType = serializers.ReadOnlyField()
    categoryNeatName = serializers.ReadOnlyField()
    waiter = serializers.ReadOnlyField()
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    order = serializers.PrimaryKeyRelatedField(queryset=Order.objects.all())
    addedBy = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = OrderItem
        fields = ('id', 'order', 'productId', 'productName', 'productPrice', 'product', 'quantity', 'changed', 'wasted', 'wastedReason', 'addedBy', 'sent', 'tableName', 'categoryType', 'categoryNeatName', 'waiter', 'cooked', 'comment', 'entered', 'productDesc', 'reduced', 'price')




class CategorySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'neatName', 'order')