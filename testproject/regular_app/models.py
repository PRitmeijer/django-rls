from django.db import models

class RegularModel(models.Model):
    id = models.AutoField(primary_key=True)
    tenant_id = models.IntegerField()
    name = models.CharField(max_length=100)

class AnotherModel(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.IntegerField()
    description = models.TextField()

