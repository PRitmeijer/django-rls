import uuid
from django.db import models

class TenantModel(models.Model):
    id = models.AutoField(primary_key=True)
    tenant_id = models.IntegerField()
    name = models.CharField(max_length=100)

class UserModel(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.IntegerField()
    title = models.CharField(max_length=100)

class MixedModel(models.Model):
    id = models.AutoField(primary_key=True)
    tenant_id = models.IntegerField()
    user_id = models.IntegerField()
    content = models.TextField()

class NoRLSModel(models.Model):
    id = models.AutoField(primary_key=True)
    description = models.TextField()

class UUIDTenantModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField()
    name = models.CharField(max_length=100)

class UUIDMixedModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField()
    user_id = models.UUIDField()
    content = models.TextField()

