import uuid

from django.contrib.postgres.fields import ArrayField
from django.db import models


class User(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)


class Party(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    time_limit = models.IntegerField()


class PartyMember(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    party = models.ForeignKey(Party, on_delete=models.CASCADE, related_name='members')

    points = models.IntegerField(default=0)


class AdminRole(models.Model):
    party = models.OneToOneField(Party, primary_key=True, on_delete=models.CASCADE)
    admin_member = models.OneToOneField(PartyMember, on_delete=models.CASCADE)


class Round(models.Model):
    party = models.ForeignKey(Party, on_delete=models.CASCADE, related_name='rounds')
    start_page = models.CharField(max_length=100)
    end_page = models.CharField(max_length=100)
    solution = ArrayField(models.CharField(max_length=100))

    start_time = models.DateTimeField(auto_now_add=True)
    running = models.BooleanField(default=True)


class MemberRound(models.Model):
    member = models.ForeignKey(PartyMember, on_delete=models.CASCADE, related_name='rounds')
    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name='member_rounds')

    current_page = models.CharField(max_length=100)
    solved_at = models.IntegerField(default=-1)
