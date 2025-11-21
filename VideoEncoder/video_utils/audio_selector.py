import asyncio
from asyncio import Event, wait_for, wrap_future, gather, create_task
from functools import partial
from time import time

from pyrogram import filters
from pyrogram.types import CallbackQuery, Message
from pyrogram.handlers import CallbackQueryHandler

from ..utils.button_maker import ButtonMaker
from ..utils.display_progress import TimeFormatter

class AudioSelect():
    def __init__(self, client, message):
        self._is_cancelled = False
        self._reply = None
        self._time = time()
        self.client = client
        self.message = message
        self.aud_streams = {}
        self.event = Event()
        self.streams = -1
        self.stream_view_msg = None

    async def _event_handler(self):
        # We need to register a dynamic handler for this specific session
        # Ideally we filter by user ID and maybe a unique ID for this session
        pfunc = partial(cb_audiosel, obj=self)
        # Using a unique filter. Note: 'group' might need to be managed if used extensively.
        # We use group=-1 to allow other handlers too, but here we want exclusive handling for this menu.
        handler = self.client.add_handler(CallbackQueryHandler(pfunc, filters=filters.regex('^audiosel') & filters.user(self.message.from_user.id)), group=-1)
        try:
            await wait_for(self.event.wait(), timeout=180)
        except asyncio.TimeoutError:
            self._is_cancelled = True
            self.event.set()
        finally:
            self.client.remove_handler(*handler)

    async def get_buttons(self, streams):
        self.streams = streams
        for stream in self.streams:
            if stream.get('codec_type') == 'audio':
                index = stream.get('index')
                tags = stream.get('tags', {})
                self.aud_streams[index] = {
                    'map': index,
                    'title': tags.get('title'),
                    'lang': tags.get('language')
                }

        if not self.aud_streams or len(self.aud_streams) < 2:
            return -1, -1

        future = asyncio.create_task(self._event_handler())
        await self._send_message()
        await future

        if self._is_cancelled:
            if self._reply:
                await self._reply.edit('Task has been cancelled!')
            return -1, -1

        if self._reply:
            await self._reply.delete()
        if self.stream_view_msg:
            await self.stream_view_msg.delete()

        maps = [i['map'] for i in self.aud_streams.values()]
        return maps, self.aud_streams

    async def _send_message(self):
        buttons = ButtonMaker()
        text = f"<b>CHOOSE AUDIO STREAM TO SWAP</b>\n\n<b>Audio Streams: {len(self.aud_streams)}</b>"
        for index, stream in self.aud_streams.items():
            buttons.button_data(f"{stream['lang'] or 'und'} | {stream['title'] or 'No Title'}", f"audiosel none {index}")
            buttons.button_data("▲", f"audiosel up {index}")
            buttons.button_data("⇅", f"audiosel swap {index}")
            buttons.button_data("▼", f"audiosel down {index}")
        buttons.button_data('Done', 'audiosel done', 'footer')
        buttons.button_data('Cancel', 'audiosel cancel', 'footer')

        if not self._reply:
            self._reply = await self.message.reply(text, reply_markup=buttons.build_menu(4))
        else:
            await self._reply.edit(text, reply_markup=buttons.build_menu(4))
        await self._create_streams_view(self._reply)

    async def _create_streams_view(self, reply):
        text = f"<b>STREAMS ORDER</b>"
        for index, stream in self.aud_streams.items():
            text += f"\n{stream['lang'] or 'und'} | {stream['title'] or 'No Title'}"
        text += f'\n\nTime Out: {TimeFormatter(180 - (time()-self._time))}'

        if self.stream_view_msg and self.stream_view_msg.text != text:
            await self.stream_view_msg.edit(text)
        elif not self.stream_view_msg:
             # Send a new message for stream view to keep it separate or just update it.
             # The original code kept a separate view.
             self.stream_view_msg = await self.message.reply(text)

async def cb_audiosel(client, query: CallbackQuery, obj: AudioSelect):
    data = query.data.split()
    if data[1] == 'cancel':
        obj._is_cancelled = True
        obj.event.set()
        await query.answer()
        return
    elif data[1] == 'done':
        obj.event.set()
        await query.answer()
        return
    elif data[1] == 'none':
        await query.answer()
        return

    await query.answer()

    aud_list = list(obj.aud_streams.keys())
    if data[1] == 'swap':
        pos = aud_list.index(int(data[2]))
        if pos != 0:
            # Swap keys in the dict? No, dict is insertion ordered in recent python.
            # But we need to reorder the list of keys and reconstruct the dict.
            # Swap with previous
            temp = aud_list[pos]
            aud_list[pos] = aud_list[pos-1]
            aud_list[pos-1] = temp
    elif data[1] == 'up':
        pos = aud_list.index(int(data[2]))
        if pos != 0:
            aud_list.insert(pos-1, aud_list.pop(pos))
    elif data[1] == 'down':
        pos = aud_list.index(int(data[2]))
        if pos != len(aud_list)-1:
            aud_list.insert(pos+1, aud_list.pop(pos))

    new_aud_streams = {}
    for aud in aud_list:
        new_aud_streams[aud] = obj.aud_streams[aud]
    obj.aud_streams = new_aud_streams

    if not obj._is_cancelled:
        await obj._send_message()
    else:
        obj.event.set()
