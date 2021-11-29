import asyncio
import base64
import json
import logging

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from wiki_app.data.db import is_admin, new_round, get_round_info, finish_round, member_click, \
    generate_leaderboards, get_latest_member_round, get_latest_party_round, get_member_round_info, have_all_solved, \
    get_member, get_or_create_member_round
from wiki_app.models import User, Party, Round, MemberRound
from wiki_app.websockets.protocol_handlers import protocol_handler, protocol_handlers
from wiki_race.wiki_api.parse import check_valid_transition


class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        successful_init = await self.init_fields()

        if not successful_init:
            await self.close()

        # Join room group
        await self.channel_layer.group_add(
            self.room_name,
            self.channel_name
        )

        await self.accept()

        await self.update_leaderboards()
        await self.send_round_on_return()

    @sync_to_async
    def init_fields(self) -> bool:
        user_id = self.scope['url_route']['kwargs']['user_id']
        game_id = self.scope['url_route']['kwargs']['game_id']

        self.user = User.objects.get(uid=user_id)
        self.party = Party.objects.get(uid=game_id)
        self.room_name = base64.b64encode(bytes(game_id.encode('ascii'))).decode('ascii')

        self.member = get_member(self.party, self.user)
        if not self.member:
            return False

        self.is_admin = is_admin(self.party, self.user)
        return True

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data['type']

        if action not in protocol_handlers:
            await self.send_error('notfound')
            return

        await protocol_handlers[action](self, data)

    async def group_send(self, action_name: str, data: dict):
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

    # Receive message from room group
    async def receive_group_message(self, event):
        raw_data = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps(raw_data))

    async def announce_finish_round(self, party_round):
        # time ended
        await sync_to_async(party_round.refresh_from_db)()
        if not party_round.running:
            return
        finished_data = await sync_to_async(finish_round)(party_round)
        await self.group_send('round_finished', finished_data)

    async def start_round_timer(self, party_round: Round):
        # wait for round to end
        await asyncio.sleep(self.party.time_limit)
        await self.announce_finish_round(party_round)

    async def send_error(self, error_text: str):
        await self.send(text_data=json.dumps({'error': error_text}))

    async def send_action(self, action_name: str, data: dict):
        await self.send(text_data=json.dumps({'type': action_name, 'data': data}))

    async def update_leaderboards(self):
        leaderboards = await sync_to_async(generate_leaderboards)(self.party)
        await self.group_send('leaderboard_update', {'leaderboards': leaderboards})

    async def send_round_on_return(self):
        party_round: Round = await sync_to_async(get_latest_party_round)(self.party)
        if not party_round or not party_round.running:
            return

        member_round: MemberRound = await sync_to_async(get_or_create_member_round)(party_round, self.member)
        round_info = await sync_to_async(get_member_round_info)(member_round)

        if round_info['time_limit'] <= 0:
            await self.announce_finish_round(party_round)
            logging.info(f"{party_round.party.uid} round finished after deadline!")
            return

        await self.send_action("new_round", round_info)
        await self.send_action("force_redirect", {'page': member_round.current_page})
        if member_round.solved_at != -1:
            await self.send_action('solved', {})

    async def finish_if_all_solved(self, party_round: Round):
        round_should_be_finished = await sync_to_async(have_all_solved)(party_round)
        if round_should_be_finished:
            await self.announce_finish_round(party_round)


# Handlers
@protocol_handler("click")
async def click_handler(self: GameConsumer, data: dict):
    member_round: MemberRound = await sync_to_async(get_latest_member_round)(self.party, self.user)
    if not member_round:
        return await self.send_error('no active round')

    try:
        clicked_page = data['destination']

        if member_round.solved_at != -1:
            return await self.send_error('already solved')

        correct_transition = check_valid_transition(member_round.current_page, clicked_page)
        if not correct_transition:
            return await self.send_action('force_redirect', {'page': member_round.current_page})

        solved: bool = await sync_to_async(member_click)(member_round, clicked_page)
        if solved:
            await self.update_leaderboards()
            await self.send_action('solved', {})
        await self.finish_if_all_solved(member_round.round)
    except Exception as e:
        logging.error(e)


@protocol_handler("new_round")
async def new_round_handler(self: GameConsumer, _: dict):
    if not self.is_admin:
        return await self.send_error('not admin')

    prev_round: MemberRound = await sync_to_async(get_latest_member_round)(self.party, self.user)
    if prev_round is not None and prev_round.round.running:
        return await self.send_error('another round is running')

    party_round = await sync_to_async(new_round)(self.party)
    round_info = await sync_to_async(get_round_info)(party_round)

    await self.group_send('new_round', round_info)
    # start round
    asyncio.ensure_future(self.start_round_timer(party_round))


@protocol_handler("finish_early")
async def new_round_handler(self: GameConsumer, _: dict):
    if not self.is_admin:
        await self.send_error('not admin')
        return

    party_round: Round = await sync_to_async(get_latest_party_round)(self.party)
    if party_round is None:
        return await self.send_error('no active round')

    await self.announce_finish_round(party_round)
