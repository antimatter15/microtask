import Quartz
import AppKit
import asyncio
import json
from aiohttp import web
import aiohttp


def windowList(wl):
    for v in wl:
        yield {
            'pid': v.valueForKey_('kCGWindowOwnerPID'),
            'bounds': [int(v.valueForKey_('kCGWindowBounds').valueForKey_(x)) for x in ['X', 'Y', 'Width', 'Height']],
            'wid': v.valueForKey_('kCGWindowNumber'),
            'owner': v.valueForKey_('kCGWindowOwnerName'),
            'name': v.valueForKey_('kCGWindowName')
        }


async def screenshot_transmitter(ws, state):
    while True:
        WID = state['wid']

        if WID is None:
            await asyncio.sleep(0.1)
            continue

        win = list(windowList(Quartz.CGWindowListCreateDescriptionFromArray([WID])))[0]

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
        await asyncio.sleep(0.5)


# async def main_handler(ws, win):
#     await ws.send_str(repr(win))


#     async for msg in ws:
#         if msg.type == aiohttp.WSMsgType.TEXT:
#             if msg.data == 'close':
#                 await ws.close()
#             else:
#                 await ws.send_str(msg.data + '/answer')
#         elif msg.type == aiohttp.WSMsgType.ERROR:
#             print('ws connection closed with exception %s' %
#                   ws.exception())

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    wl1 = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID)

    state = {
        'wid': None
    }

    for x in list(windowList(wl1)):
        await ws.send_json({
            'type': 'add_option',
            'text': x['owner'] + ' - ' + x['name'],
            'value': x['wid'],
        })


    task1 = asyncio.create_task(screenshot_transmitter(ws, state))

    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            data = json.loads(msg.data)

            print(data)
            if data['type'] == 'set_window':
                state['wid'] = int(data['wid'])

            elif data['type'] == 'mouse_move':
                WID = state['wid']
                win = list(windowList(Quartz.CGWindowListCreateDescriptionFromArray([WID])))[0]
                x, y, w, h = win['bounds']
                point = Quartz.CGPointMake(x + w * data['x'], y + h * data['y'])
                print(point)

                moveEvent = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventMouseMoved, point, Quartz.kCGMouseButtonLeft)
                Quartz.CGEventSetType(moveEvent, Quartz.kCGEventMouseMoved)
                Quartz.CGEventPostToPid(win['pid'], moveEvent)
                moveEvent.autorelease()

            elif data['type'] == 'mouse_down':
                WID = state['wid']
                win = list(windowList(Quartz.CGWindowListCreateDescriptionFromArray([WID])))[0]
                x, y, w, h = win['bounds']
                # https://github.com/ThePacielloGroup/CCA-OSX/blob/master/Colour%20Contrast%20Analyser/CCAPickerController.swift#L85
                # //Because AppKit and CoreGraphics use different coordinat systems

                screenHeight = Quartz.NSScreen.mainScreen().frame().size.height
                point = Quartz.CGPointMake(w * data['x'], screenHeight - h * (data['y']))
                print(win['bounds'], point)
                customEvent = Quartz.NSEvent.mouseEventWithType_location_modifierFlags_timestamp_windowNumber_context_eventNumber_clickCount_pressure_(
                    Quartz.NSEventTypeLeftMouseDown, 
                    point, 
                    0,
                    AppKit.NSDate.timeIntervalSinceReferenceDate(), 
                    WID, 
                    None, 
                    0, 
                    1, 
                    0
                )
                print(customEvent.description())
                Quartz.CGEventPostToPid(win['pid'], customEvent.CGEvent())
                customEvent.autorelease()

            elif data['type'] == 'mouse_up':
                WID = state['wid']
                win = list(windowList(Quartz.CGWindowListCreateDescriptionFromArray([WID])))[0]
                x, y, w, h = win['bounds']
                screenHeight = Quartz.NSScreen.mainScreen().frame().size.height
                point = Quartz.CGPointMake(w * data['x'], screenHeight - h * (data['y']))
                print(point)
                customEvent = Quartz.NSEvent.mouseEventWithType_location_modifierFlags_timestamp_windowNumber_context_eventNumber_clickCount_pressure_(
                    Quartz.NSEventTypeLeftMouseUp, 
                    point, 
                    0,
                    AppKit.NSDate.timeIntervalSinceReferenceDate(), 
                    WID, 
                    None, 
                    0, 
                    1, 
                    0
                )
                Quartz.CGEventPostToPid(win['pid'], customEvent.CGEvent())
                customEvent.autorelease()

        elif msg.type == aiohttp.WSMsgType.ERROR:
            print('ws connection closed with exception %s' %
                  ws.exception())

    # t1 = asyncio.create_task(screenshot_transmitter(ws, state))
    # t2 = asyncio.create_task(main_handler(ws, state))

    # await asyncio.wait([t1, t2])

    await task1

    

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
                display: block;
            }
        </style>
        <select id="options">
            <option disabled selected>Select a window</option>
        </select>
        <img id="portal">
        
        <script>
            var ws = new WebSocket('ws://' + location.host + '/ws');

            function send(x){
                console.log(x)
                ws.send(JSON.stringify(x))
            }

            document.getElementById('options').onchange = e => {
                location.hash = '#' + e.target.value
                send({ type: 'set_window', wid: e.target.value })
            }

            const portal = document.getElementById('portal');

            portal.onmousemove = e => {
                let bb = portal.getBoundingClientRect()
                send({
                    type: 'mouse_move', 
                    x: (e.clientX - bb.x) / bb.width, 
                    y: (e.clientY - bb.y) / bb.height
                })
            }

            portal.onmousedown = e => {
                e.preventDefault()
                let bb = portal.getBoundingClientRect()
                send({
                    type: 'mouse_down', 
                    x: (e.clientX - bb.x) / bb.width, 
                    y: (e.clientY - bb.y) / bb.height
                })
            }

            portal.onmouseup = e => {
                e.preventDefault()
                let bb = portal.getBoundingClientRect()
                send({
                    type: 'mouse_up', 
                    x: (e.clientX - bb.x) / bb.width, 
                    y: (e.clientY - bb.y) / bb.height
                })
            }
            
            ws.onclose = () => {
                document.body.innerHTML = "Please refresh the page (Socket closed)"
            }

            ws.onmessage = function (event) {
                if(event.data instanceof Blob){
                    portal.src = URL.createObjectURL(event.data)
                    return;
                }

                let data = JSON.parse(event.data);
                console.log(data)
                
                if(data.type === 'add_option'){
                    document.getElementById('options').appendChild(new Option(data.text, data.value))
                    
                    if('#' + data.value === location.hash){
                        document.getElementById('options').value = data.value;
                        send({ type: 'set_window', wid: data.value })
                    }
                }

                
            };
        </script></body>
    """)


app = web.Application()
app.add_routes([web.get('/', hello)])    
app.add_routes([web.get('/ws', websocket_handler)])

web.run_app(app)
