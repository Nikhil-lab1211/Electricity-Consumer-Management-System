from django.db import models

# Create your models here.
# user_app/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid

class User(AbstractUser):
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    role = models.CharField(max_length=20, choices=[
        ('admin', 'Admin'),
        ('consumer', 'Consumer'),
        ('staff', 'Staff')
    ], default='consumer')
    
    # Add related_name attributes to avoid clashes
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='user_app_user_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='user_app_user_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )
    
    def __str__(self):
        return self.username
    
class Consumer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='consumer_profile')
    consumer_id = models.CharField(max_length=20, unique=True)
    account_number = models.CharField(max_length=20, unique=True)
    meter_number = models.CharField(max_length=20, unique=True)
    address = models.TextField()
    connection_type = models.CharField(max_length=20, choices=[
        ('residential', 'Residential'),
        ('commercial', 'Commercial'),
        ('industrial', 'Industrial')
    ])
    sanctioned_load = models.FloatField(help_text="In kW")
    
    def __str__(self):
        return f"{self.consumer_id} - {self.user.full_name}"

class Bill(models.Model):
    consumer = models.ForeignKey(Consumer, on_delete=models.CASCADE, related_name='bills')
    bill_number = models.CharField(max_length=20, unique=True)
    bill_date = models.DateTimeField(default=timezone.now)
    due_date = models.DateTimeField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    units_consumed = models.IntegerField()
    status = models.CharField(max_length=20, choices=[
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue')
    ], default='unpaid')
    payment_date = models.DateTimeField(null=True, blank=True)
    payment_method = models.CharField(max_length=20, null=True, blank=True)
    payment_reference = models.CharField(max_length=20, null=True, blank=True)
    
    def __str__(self):
        return f"Bill #{self.bill_number} - {self.consumer.user.full_name}"
    
    def save(self, *args, **kwargs):
        if not self.bill_number:
            self.bill_number = f"BILL-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

class ConsumptionRecord(models.Model):
    consumer = models.ForeignKey(Consumer, on_delete=models.CASCADE, related_name='consumption_records')
    reading_date = models.DateTimeField(default=timezone.now)
    meter_reading = models.IntegerField()
    units_consumed = models.IntegerField()
    reading_type = models.CharField(max_length=20, choices=[
        ('actual', 'Actual'),
        ('estimated', 'Estimated')
    ], default='actual')
    
    def __str__(self):
        return f"{self.consumer.consumer_id} - {self.reading_date.strftime('%Y-%m-%d')}"

class PowerOutage(models.Model):
    area_code = models.CharField(max_length=20)
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('reported', 'Reported'),
        ('investigating', 'Investigating'),
        ('fixing', 'Fixing'),
        ('resolved', 'Resolved')
    ], default='reported')
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='reported_outages')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_outages')
    description = models.TextField()
    estimated_resolution_time = models.DateTimeField()
    
    def __str__(self):
        return f"Outage #{self.id} - {self.area_code}"

class Complaint(models.Model):
    consumer = models.ForeignKey(Consumer, on_delete=models.CASCADE, related_name='complaints')
    complaint_number = models.CharField(max_length=20, unique=True)
    subject = models.CharField(max_length=100)
    description = models.TextField()
    complaint_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=[
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed')
    ], default='open')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_complaints')
    resolution_date = models.DateTimeField(null=True, blank=True)
    resolution_description = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return f"Complaint #{self.complaint_number} - {self.consumer.user.full_name}"
    
    def save(self, *args, **kwargs):
        if not self.complaint_number:
            self.complaint_number = f"COMP-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)