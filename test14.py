import asyncio
from aiohttp import web

import datetime
import random

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    while True:
        # await ws.send_str(msg.data + '/answer')
        await ws.send_str(datetime.datetime.utcnow().isoformat())
        await asyncio.sleep(2)

    # async for msg in ws:
    #     if msg.type == aiohttp.WSMsgType.TEXT:
    #         if msg.data == 'close':
    #             await ws.close()
    #         else:
    #             await ws.send_str(msg.data + '/answer')
    #     elif msg.type == aiohttp.WSMsgType.ERROR:
    #         print('ws connection closed with exception %s' %
    #               ws.exception())

    print('websocket connection closed')
    return ws



async def hello(request):
    return web.Response(content_type='text/html', text="""
        <body>
        <script>
            var ws = new WebSocket('ws://' + location.host + '/ws'),
                messages = document.createElement('ul');
            ws.onmessage = function (event) {
                var messages = document.getElementsByTagName('ul')[0],
                    message = document.createElement('li'),
                    content = document.createTextNode(event.data);
                message.appendChild(content);
                messages.appendChild(message);
            };
            document.body.appendChild(messages);
        </script></body>
    """)


app = web.Application()
app.add_routes([web.get('/', hello)])    
app.add_routes([web.get('/ws', websocket_handler)])

web.run_app(app)
