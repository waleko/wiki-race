import asyncio
import base64
import json
import logging

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from wiki_app.data.db import is_admin, new_round, get_initial_round_info, finish_round, member_click, \
    generate_leaderboards, get_latest_member_round, get_latest_party_round, get_time_specific_round_info, have_all_solved, \
    get_member, get_or_create_member_round, check_if_time_ran_out
from wiki_app.models import User, Party, Round, MemberRound
from wiki_app.websockets.protocol_handlers import protocol_handler, protocol_handlers
from wiki_race.wiki_api.parse import check_valid_transition


class GameConsumer(AsyncWebsocketConsumer):
    """
    Asynchronous websocket consumer for interacting with web wikirace game page.
    """
    async def connect(self) -> None:
        """
        Connect to websocket
        """
        # initialize fields with data from request
        successful_init = await self.init_fields()
        # if data incorrect, refuse connection
        if not successful_init:
            await self.close()
        # join party channel group
        await self.channel_layer.group_add(
            self.room_name,
            self.channel_name
        )
        # accept websocket
        await self.accept()

        # send leaderboards
        await self.update_leaderboards()
        # send round if in progress
        await self.send_connected_member()

    @sync_to_async
    def init_fields(self) -> bool:
        """
        Initializes fields on new websocket request
        :return: true if correct data, false otherwise
        """
        # get user id in args
        user_id = self.scope['url_route']['kwargs']['user_id']
        # get party id in args
        game_id = self.scope['url_route']['kwargs']['game_id']
        # get user
        self.user = User.objects.get(uid=user_id)
        # get party
        self.party = Party.objects.get(uid=game_id)
        # get member
        self.member = get_member(self.party, self.user)
        # if not member, refuse connection
        if not self.member:
            return False
        # check if admin
        self.is_admin = is_admin(self.party, self.user)

        # generate channel room name (required to be ascii)
        self.room_name = base64.b64encode(bytes(game_id.encode('ascii'))).decode('ascii')

        # clear to accept connection
        return True

    async def disconnect(self, close_code) -> None:
        """
        Disconnect from group
        """
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data) -> None:
        """
        Receive message from websocket
        """
        # load json data
        data = json.loads(text_data)
        # get action name
        action = data['type']
        # if action has no registered handlers, respond with not found
        if action not in protocol_handlers:
            await self.send_error('notfound')
            return
        # call corresponding handler
        await protocol_handlers[action](self, data)

    async def group_send(self, action_name: str, data: dict) -> None:
        """
        Send action to every room group (party) member
        """
        await self.channel_layer.group_send(
            self.room_name,
            {
                'type': 'receive_group_message',
                'message': {
                    'type': action_name,
                    'data': data
                }
            }
        )

    async def send_error(self, error_text: str) -> None:
        """
        Send error via websocket
        """
        await self.send(text_data=json.dumps({'error': error_text}))

    async def send_action(self, action_name: str, data: dict) -> None:
        """
        Send action via websocket
        """
        await self.send(text_data=json.dumps({'type': action_name, 'data': data}))

    async def receive_group_message(self, event) -> None:
        """
        Receive internal message from room group
        """
        # get data
        raw_data = event['message']
        # send message to websocket
        await self.send(text_data=json.dumps(raw_data))

    async def start_round_timer(self, party_round: Round) -> None:
        """
        Start internal round timer
        """
        # asynchronously sleep until round has ended
        await asyncio.sleep(self.party.time_limit)
        # announce finish
        await self.announce_finish_round(party_round)

    async def announce_finish_round(self, party_round) -> None:
        """
        Finish round
        """
        # refresh party round object instance
        await sync_to_async(party_round.refresh_from_db)()
        # if already finished, skip
        if not party_round.running:
            return
        # finish round and get data for frontend to be sent
        finished_data = await sync_to_async(finish_round)(party_round)
        # send data to every member
        await self.group_send('round_finished', finished_data)

    async def update_leaderboards(self) -> None:
        """
        Update leaderboards and send to every member
        """
        # get leaderboards
        leaderboards = await sync_to_async(generate_leaderboards)(self.party)
        # send to every member
        await self.group_send('leaderboard_update', {'leaderboards': leaderboards})

    async def send_connected_member(self) -> None:
        """
        Send data to newly connected member
        """
        # get latest party round
        party_round: Round = await sync_to_async(get_latest_party_round)(self.party)
        # if no party round is active, skip
        if not party_round or not party_round.running:
            return
        # if round has ended, but hasn't been declared as finished,
        #  this may happen if round has started right before server restart, so timer has been killed
        if check_if_time_ran_out(party_round):
            # finish forcefully
            return await self.announce_finish_round(party_round)
        # get member round
        member_round: MemberRound = await sync_to_async(get_or_create_member_round)(party_round, self.member)
        # generate data for frontend
        round_info = await sync_to_async(get_time_specific_round_info)(party_round)
        # send connected member 'new_round' (actually it can be already started, but they will never know)
        await self.send_action("new_round", round_info)
        # force redirect to current page
        await self.send_action("force_redirect", {'page': member_round.current_page})
        # if member has solved, send solved
        if member_round.solved_at != -1:
            await self.send_action('solved', {})

    async def finish_if_all_solved(self, party_round: Round) -> None:
        """
        Checks if all members have solved the wikirace. If yes, finishes round.
        """
        round_should_be_finished = await sync_to_async(have_all_solved)(party_round)
        if round_should_be_finished:
            await self.announce_finish_round(party_round)


# ===== Protocol handlers =====

@protocol_handler("new_round")
async def new_round_handler(self: GameConsumer, _: dict):
    """
    New round websocket command handler
    """
    # only host can call new round
    if not self.is_admin:
        return await self.send_error('not admin')

    # check no other round is running
    prev_round: MemberRound = await sync_to_async(get_latest_member_round)(self.member)
    if prev_round is not None and prev_round.round.running:
        return await self.send_error('another round is running')

    # create party round
    party_round = await sync_to_async(new_round)(self.party)
    # get info for frontend
    round_info = await sync_to_async(get_initial_round_info)(party_round)
    # send info
    await self.group_send('new_round', round_info)
    # start timer
    asyncio.ensure_future(self.start_round_timer(party_round))


@protocol_handler("click")
async def click_handler(self: GameConsumer, data: dict):
    """
    Click websocket command handler
    """
    # get clicked page
    if 'destination' not in data:
        return await self.send_error("no destination")
    clicked_page = data['destination']
    # get member round
    member_round: MemberRound = await sync_to_async(get_latest_member_round)(self.member)
    # if no active round
    if not member_round or not member_round.round.running:
        return await self.send_error('no active round')

    try:
        # if solved
        if member_round.solved_at != -1:
            return await self.send_error('already solved')
        # check if correct transition
        correct_transition = check_valid_transition(member_round.current_page, clicked_page)
        if not correct_transition:
            # if incorrect, force redirect to last confirmed
            return await self.send_action('force_redirect', {'page': member_round.current_page})
        # save to db and check if solved
        solved: bool = await sync_to_async(member_click)(member_round, clicked_page)
        if solved:
            # update leaderboards
            await self.update_leaderboards()
            # send solved
            await self.send_action('solved', {})
        # check if everyone has solved
        await self.finish_if_all_solved(member_round.round)
    except Exception as e:
        logging.error(e)


@protocol_handler("finish_early")
async def finish_early_handler(self: GameConsumer, _: dict):
    """
    Finish early websocket command handler
    """
    # only host can finish round early
    if not self.is_admin:
        return await self.send_error('not admin')
    # get party round
    party_round: Round = await sync_to_async(get_latest_party_round)(self.party)
    # if no round
    if party_round is None:
        return await self.send_error('no active round')
    # announce finish
    await self.announce_finish_round(party_round)
