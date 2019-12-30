import Quartz
import AppKit
import asyncio
from aiohttp import web



def windowList(wl):
    for v in wl:
        yield {
            'pid': v.valueForKey_('kCGWindowOwnerPID'),
            'bounds': [int(v.valueForKey_('kCGWindowBounds').valueForKey_(x)) for x in ['X', 'Y', 'Width', 'Height']],
            'wid': v.valueForKey_('kCGWindowNumber'),
            'owner': v.valueForKey_('kCGWindowOwnerName'),
            'name': v.valueForKey_('kCGWindowName')
        }


async def screenshot_transmitter(ws, win):
    while True:
        WID = win['wid']
        theRect = Quartz.NSMakeRect(*win['bounds'])
        theImage = Quartz.CGWindowListCreateImage(
            theRect, 
            Quartz.kCGWindowListOptionIncludingWindow, 
            WID, 
            Quartz.kCGWindowImageDefault);
        bitmapRep = Quartz.NSBitmapImageRep.alloc().initWithCGImage_(theImage)
        pngData = bitmapRep.representationUsingType_properties_(Quartz.NSPNGFileType, None)
        await ws.send_bytes(pngData.bytes())
        pngData.autorelease()
        bitmapRep.autorelease()
        await asyncio.sleep(2)


async def main_handler(ws, win):
    await ws.send_str(repr(win))


    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            if msg.data == 'close':
                await ws.close()
            else:
                await ws.send_str(msg.data + '/answer')
        elif msg.type == aiohttp.WSMsgType.ERROR:
            print('ws connection closed with exception %s' %
                  ws.exception())

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    wl1 = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID)

    win = None
    for x in list(windowList(wl1)):
        if not (x['owner'] and 'Sublime' in x['owner']):
            continue
        win = x

    t1 = asyncio.create_task(screenshot_transmitter(ws, win))
    t2 = asyncio.create_task(main_handler(ws, win))

    await asyncio.wait([t1, t2])

    
        

        


    # while True:
    #     # await ws.send_str(msg.data + '/answer')
    #     await ws.send_str(datetime.datetime.utcnow().isoformat())
    #     await asyncio.sleep(2)


    print('websocket connection closed')
    return ws



async def hello(request):
    return web.Response(content_type='text/html', text="""
        <body>
        <style>
            #portal {
                width: 800px;
            }
        </style>
        <img id="portal">
        <script>
            var ws = new WebSocket('ws://' + location.host + '/ws'),
                messages = document.createElement('ul');
            ws.onmessage = function (event) {
                console.log(event)
                if(event.data instanceof Blob){
                    document.getElementById('portal').src = URL.createObjectURL(event.data)
                }else{
                var messages = document.getElementsByTagName('ul')[0],
                    message = document.createElement('li');
                    let content = document.createTextNode(event.data)
                    message.appendChild(content);
                    messages.appendChild(message);
                }
                
            };
            document.body.appendChild(messages);
        </script></body>
    """)


app = web.Application()
app.add_routes([web.get('/', hello)])    
app.add_routes([web.get('/ws', websocket_handler)])

web.run_app(app)
