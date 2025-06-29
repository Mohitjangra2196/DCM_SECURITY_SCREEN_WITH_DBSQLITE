# gatepass_app/models.py
from django.db import models



class GatePass(models.Model):

    GATEPASS_NO = models.CharField(max_length=60, primary_key=True) # Assuming GATEPASS_NO is unique and primary key
    GATEPASS_DATE = models.DateField()
    PAYCODE = models.CharField(max_length=60)
    NAME = models.CharField(max_length=300, null=True, blank=True)
    DEPARTMENT = models.CharField(max_length=300, null=True, blank=True)
    GATEPASS_TYPE = models.CharField(max_length=150, null=True, blank=True)
    REMARKS = models.CharField(max_length=765, null=True, blank=True)
    REQUEST_TIME = models.CharField(max_length=60, null=True, blank=True)
    AUTH = models.CharField(max_length=3, null=True, blank=True)
    AUTH1_BY = models.CharField(max_length=24, null=True, blank=True)
    AUTH1_STATUS = models.CharField(max_length=3, null=True, blank=True)
    AUTH1_DATE = models.DateField(null=True, blank=True)
    AUTH1_REMARKS = models.CharField(max_length=150, null=True, blank=True)
    FINAL_STATUS = models.CharField(max_length=3, null=True, blank=True) # A = Approved
    OUT_TIME = models.DateTimeField(null=True, blank=True)
    OUT_BY = models.CharField(max_length=60, null=True, blank=True) # Represents who marked out
    IN_TIME = models.DateTimeField(null=True, blank=True)
    IN_BY = models.CharField(max_length=60, null=True, blank=True) # Represents who marked in
    INOUT_STATUS = models.CharField(max_length=3, null=True, blank=True) # O = Out, I = In
    UNIT_NAME = models.CharField(max_length=300, null=True, blank=True) # Represents the unit name EXAMPLE: UNIT-1, UNIT-2, etc.
    EMP_TYPE = models.CharField(max_length=60, null=True, blank=True) # Represents the employee type S =STAFF /W =WORKER
    LUNCH = models.CharField(max_length=3, null=True, blank=True) # Represents the lunch status Y/N

    class Meta:
        db_table = 'GATEPASS' # The actual view name in Oracle
