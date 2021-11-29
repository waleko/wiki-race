import uuid

from django.contrib.postgres.fields import ArrayField
from django.db import models


class User(models.Model):
    """
    Website user. Generated for everyone who will access join, new, or game pages
    """
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)


class Party(models.Model):
    """
    Party (Lobby, Group). Group of players.
    """
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    time_limit = models.IntegerField()
    """
    Time limit for each round played in party
    """


class PartyMember(models.Model):
    """
    Member of party (Player). They are connected with the corresponding user and party via a foreign key.
     Also has a name.
    """
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    party = models.ForeignKey(Party, on_delete=models.CASCADE, related_name='members')
    points = models.IntegerField(default=0)
    """
    Points received in a round
    """


class AdminRole(models.Model):
    """
    Administrator (Host) -- member who created party. Visible from party via one-to-one relationship.
    """
    party = models.OneToOneField(Party, primary_key=True, on_delete=models.CASCADE)
    admin_member = models.OneToOneField(PartyMember, on_delete=models.CASCADE)


class Round(models.Model):
    """
    Round (party round). Single round of wikiracing for party.
    """
    party = models.ForeignKey(Party, on_delete=models.CASCADE, related_name='rounds')
    start_page = models.CharField(max_length=100)
    """
    Start wiki page title
    """
    end_page = models.CharField(max_length=100)
    """
    End wiki page title
    """
    solution = ArrayField(models.CharField(max_length=100))
    """
    Solution: array of page titles leading from start to end via internal links (ends inclusive).
    
    NOTICE: requires postgres
    """
    start_time = models.DateTimeField(auto_now_add=True)
    """
    Time the round was started
    """
    running = models.BooleanField(default=True)
    """
    Whether round is currently active. Has to be updated in regards to `start_time`.
    """


class MemberRound(models.Model):
    """
    Member round. Each member's progress in the party round.
    """
    member = models.ForeignKey(PartyMember, on_delete=models.CASCADE, related_name='rounds')
    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name='member_rounds')
    current_page = models.CharField(max_length=100)
    """
    Current page the member is on
    """
    solved_at = models.IntegerField(default=-1)
    """
    Seconds left until time would run out, as member solved the wikirace. If -1, then member hasn't solved it (yet).
    """
