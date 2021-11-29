import logging
import math
from collections import namedtuple
from typing import Dict, List, Optional

from django.db.models import F
from django.forms import model_to_dict
from django.http import HttpRequest
from django.utils import timezone

from wiki_app.models import User, Party, PartyMember, AdminRole, Round, MemberRound
from wiki_race.settings import USER_COOKIE_NAME, POINTS_FOR_SOLVING, MIN_TIME_LIMIT_SECONDS, MAX_TIME_LIMIT_SECONDS
from wiki_race.wiki_api.parse import generate_round, compare_titles


def get_user(request: HttpRequest) -> User:
    """
    Gets user by user cookie (or creates new user if none found)
    :return: `User` object
    """
    # get user_id
    user_id = request.COOKIES.get(USER_COOKIE_NAME)
    # if no cookie
    if user_id is None:
        # create new user
        new_user = User()
        new_user.save()
        return new_user
    # try to get saved user
    # TODO: if invalid, create new user
    return User.objects.get(uid=user_id)


def create_party(admin_user: User, form: Dict) -> Party:
    """
    Creates new party
    :param admin_user: host user
    :param form: form submitted via api
    :return: new party
    :raises: KeyError or ValueError if incorrect form data submitted
    """
    # get time limit
    time_limit = int(form["time_limit_seconds"])
    # validate time limit
    if not (MIN_TIME_LIMIT_SECONDS <= time_limit <= MAX_TIME_LIMIT_SECONDS):
        raise ValueError(f"incorrect time limit: {time_limit}")
    # get admin's name
    admin_name = form["name"]
    # create party
    party = Party(time_limit=time_limit)
    party.save()
    # create party member
    member = PartyMember(name=admin_name, user=admin_user, party=party)
    member.save()
    # create admin
    admin_role = AdminRole(party=party, admin_member=member)
    admin_role.save()
    # return party
    return party


def join_party(user: User, form: Dict) -> Party:
    """
    Joins party
    :param user: user to join
    :param form: form submitted via api
    :return: game_id
    :raises: Party.DoesNotExist if no such party exists,
     KeyError if incorrect form data submitted
    """
    # get party id
    game_id = form["game_id"]
    # get user's name
    name = form["name"]
    # get party
    party = Party.objects.get(uid=game_id)
    # create member
    PartyMember(user=user, name=name, party=party).save()
    # return party
    return party


def is_admin(party: Party, user: User) -> bool:
    """
    Checks whether user is an admin (host) in a party.
    :return: True if admin, false otherwise
    """
    try:
        return party.adminrole.admin_member.user == user
    except:
        return False


def get_member(party: Party, user: User) -> Optional[PartyMember]:
    """
    Gets party member by user.
    :return: `PartyMember` if found, None if no such member in party
    """
    try:
        return party.members.get(user=user)
    except:
        return


def new_round(party: Party) -> Round:
    """
    Creates new round for party. Doesn't check if previous round has finished.
    """
    # generate round package
    start, end, solution = generate_round()
    # create round
    party_round = Round(party=party, start_page=start, end_page=end, solution=solution)
    party_round.save()
    # create member round for each member
    for member in party.members.all():
        member_round = MemberRound(member=member, round=party_round, current_page=start)
        member_round.save()
    # return round
    return party_round


def get_initial_round_info(party_round: Round) -> dict:
    """
    Gets information about party round for frontend.
    """
    res = model_to_dict(party_round, fields=["start_page", "end_page"])
    res['time_limit'] = party_round.party.time_limit
    return res


def get_time_specific_round_info(party_round: Round) -> dict:
    """
    Gets information abut party round for frontend.
    Different to `get_initial_round_info` only in using relative `time_limit`.
    """
    res = get_initial_round_info(party_round)
    res['time_limit'] = get_left_seconds(party_round)
    return res


def generate_leaderboards(party: Party) -> List[dict]:
    """
    Generates leaderboards for party for frontend to display.
    """
    # get admin
    admin = party.adminrole.admin_member
    # generate
    res = [{
        'name': member.name,
        'is_admin': admin == member,
        'points': member.points
    } for member in party.members.all()]
    # TODO: try speeding up with query
    # sort by number of points
    res.sort(key=(lambda x: x['points']), reverse=True)

    return res


def finish_round(party_round: Round) -> dict:
    """
    Finishes party round. Doesn't check whether party round is already finished.
    :return: finished round info for frontend
    """
    # set running to false
    party_round.running = False
    party_round.save(update_fields=["running"])
    # generate leaderboards
    leaderboards = generate_leaderboards(party_round.party)
    return {
        "solution": party_round.solution,
        "leaderboards": leaderboards
    }


def get_latest_party_round(party: Party) -> Optional[Round]:
    """
    Gets latest (or currently running) party round for party.
    :return: Latest round, or None if no rounds have been started yet.
    """
    try:
        return party.rounds.latest("start_time")
    except Round.DoesNotExist:
        pass


def get_latest_member_round(member: PartyMember) -> Optional[MemberRound]:
    """
    Gets latest member round for member
    :return: Latest round, or None if no rounds have been started with this member yet.
    """
    # get latest party round
    party_round = get_latest_party_round(member.party)
    if not party_round:
        return
    # get latest member round
    try:
        return party_round.member_rounds.get(member=member)
    except MemberRound.DoesNotExist:
        pass


def get_left_seconds(party_round: Round) -> int:
    """
    Gets seconds left to round end.
    """
    seconds_since_start = math.floor((timezone.now() - party_round.start_time).total_seconds())
    return party_round.party.time_limit - seconds_since_start


def member_click(member_round: MemberRound, clicked_page: str) -> bool:
    """
    Logic for member click FIXME
    :param member_round: member round
    :param clicked_page: wiki page title, member has clicked on
    :return: true if now solved, false if not yet solved
    """
    # check if member solved
    member_solved = compare_titles(clicked_page, member_round.round.end_page)
    if member_solved:
        # save time
        member_round.solved_at = get_left_seconds(member_round.round)
        # calculate points
        member_round.member.points = F("points") + POINTS_FOR_SOLVING + member_round.solved_at
        member_round.member.save(update_fields=["points"])

    # update current page
    member_round.current_page = clicked_page
    member_round.save(update_fields=["solved_at", "current_page"])

    return member_solved


def have_all_solved(party_round: Round) -> bool:
    """
    Checks whether every member in party has solved the wikirace
    """
    return party_round.member_rounds.filter(solved_at=-1).count() == 0


def get_or_create_member_round(party_round: Round, member: PartyMember) -> MemberRound:
    """
    Get or create member round for member.
    """
    return MemberRound.objects.get_or_create(round=party_round, member=member, defaults={'current_page': party_round.start_page})[0]


def check_if_time_ran_out(party_round: Round) -> bool:
    # get seconds until round end
    left_seconds = get_left_seconds(party_round)
    # if there is still time, ok
    if left_seconds > 0:
        return False
    # if round has been already declared finished, ok
    if not party_round.running:
        return False
    # time has run out, but not declared finished
    logging.warning(f"{party_round.party.uid} round finished after deadline!")
    return True
