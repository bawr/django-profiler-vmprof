from django.contrib.auth.models import User
from django.db.models import BigIntegerField
from django.db.models import BinaryField
from django.db.models import BooleanField
from django.db.models import DateTimeField
from django.db.models import FloatField
from django.db.models import ForeignKey
from django.db.models import IntegerField
from django.db.models import TextField
from django.db.models import Model
from django.db.models import SET_NULL

class RequestProfile(Model):
    started_at = DateTimeField()
    created_at = DateTimeField()
    request_user = ForeignKey(User, on_delete=SET_NULL, null=True)
    request_path = TextField(blank=True)
    response_code = IntegerField()
    time_real = FloatField()
    time_user = FloatField()
    time_sys = FloatField()
    allocated_vm = BigIntegerField()
    peak_rss_use = BigIntegerField()
    data = BinaryField(null=True)
    data_json = BooleanField()
    data_path = TextField(blank=True)
    size_base = BigIntegerField(null=True)
    size_gzip = BigIntegerField(null=True)
    size_json = BigIntegerField(null=True)
