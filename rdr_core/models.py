from django.db import models
# Create your models here.


class Rule(models.Model):
    id = models.IntegerField(primary_key=True)
    conditions = models.JSONField(null=True)
    parent = models.IntegerField(default=None, blank=True, null=True)
    is_stopping = models.BooleanField(blank=True, null=True, default=False)
    conclusion = models.CharField(max_length=200, blank=True, null=True)
    if_true = models.IntegerField(default=None, blank=True, null=True)
    if_false = models.IntegerField(default=None, blank=True, null=True)
    cornerstone = models.IntegerField(default=None, blank=True, null=True)

    def __str__(self) -> str:
        if not self.conclusion:
            return f"{self.id}. Stop Rule: {self.parent}"
        return f"{self.id}. {self.conclusion}"

    def details(self) -> str:
        return_string = f'''Rule No:{self.id}
        \n conditions: {self.conditions}
        \n conclusion: {self.conclusion}
        \n is_stopping: {self.is_stopping}'''
        return return_string


class Case(models.Model):
    case_arr = models.JSONField(null=True)
