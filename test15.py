import Quartz
import AppKit
import Foundation
import asyncio
import json
from aiohttp import web
import aiohttp
import Cocoa
import objc

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
    jpegSettings = Foundation.NSDictionary({
        "NSImageCompressionFactor": 0.5
    })
    while True:
        with objc.autorelease_pool():
            WID = state['wid']

            if WID is None:
                await asyncio.sleep(0.1)
                continue

            win = get_win(state)
            theRect = Quartz.NSMakeRect(*win['bounds'])
            theImage = Quartz.CGWindowListCreateImage(
                theRect, 
                Quartz.kCGWindowListOptionIncludingWindow, 
                WID, 
                Quartz.kCGWindowImageShouldBeOpaque | Quartz.kCGWindowImageNominalResolution);
            bitmapRep = Quartz.NSBitmapImageRep.alloc().initWithCGImage_(theImage)
            
            jpegData = bitmapRep.representationUsingType_properties_(Quartz.NSJPEGFileType, jpegSettings)
            await ws.send_bytes(jpegData.bytes())

        # del jpegData
        # del bitmapRep
        # del theImage
        # del theRect
        # Quartz.CFRelease(jpegData)
        # Quartz.CFRelease(bitmapRep)
        # Quartz.CFRelease(theImage)
        # Quartz.CFRelease(theRect)
        # jpegData.release()
        # jpegSettings.release()

        # pngData = bitmapRep.representationUsingType_properties_(Quartz.NSPNGFileType, None)
        # await ws.send_bytes(pngData.bytes())
        # pngData.release()
        # bitmapRep.release()
        # theImage.release()

        for i in range(10):
            if state['send_now']:
                print('fastpath')
                state['send_now'] = False
                continue
            await asyncio.sleep(0.05)

    Quartz.CFRelease(jpegSettings)
    print('DONE TRANSMITTING')



def get_win(state):
    WID = state['wid']
    arr = Quartz.CGWindowListCreateDescriptionFromArray([WID])
    win = list(windowList(arr))[0]
    # arr.release()
    return win

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    

    state = {
        'wid': None,
        'send_now': False
    }

    with objc.autorelease_pool():
        wl1 = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID)
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
                with objc.autorelease_pool():
                    win = get_win(state)
                    x, y, w, h = win['bounds']
                    point = Quartz.CGPointMake(x + w * data['x'], y + h * data['y'])
                    print(point)

                    moveEvent = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventMouseMoved, point, Quartz.kCGMouseButtonLeft)
                    Quartz.CGEventSetType(moveEvent, Quartz.kCGEventMouseMoved)
                    Quartz.CGEventPostToPid(win['pid'], moveEvent)

            elif data['type'] == 'mouse_wheel':
                with objc.autorelease_pool():
                    win = get_win(state)

                    event = Quartz.CGEventCreateScrollWheelEvent(None, Quartz.kCGScrollEventUnitPixel, 2, data['deltaY'], data['deltaX']);
                    Quartz.CGEventSetType(event, Quartz.kCGEventScrollWheel)
                    
                    # CGEventSetIntegerValueField(*event, kCGMouseEventDeltaX, deltaX);
                    # CGEventSetIntegerValueField(*event, kCGMouseEventDeltaY, deltaY);

                    Quartz.CGEventPostToPid(win['pid'], event)
                    # event.release()
                    # state['send_now'] = True

            elif data['type'] == 'mouse_down':
                with objc.autorelease_pool():
                    win = get_win(state)
                    x, y, w, h = win['bounds']
                    # https://github.com/ThePacielloGroup/CCA-OSX/blob/master/Colour%20Contrast%20Analyser/CCAPickerController.swift#L85
                    # Because AppKit and CoreGraphics use different coordinate systems

                    screenHeight = Quartz.NSScreen.mainScreen().frame().size.height
                    point = Quartz.CGPointMake(w * data['x'], screenHeight - h * (data['y']))
                    customEvent = Quartz.NSEvent.mouseEventWithType_location_modifierFlags_timestamp_windowNumber_context_eventNumber_clickCount_pressure_(
                        Quartz.NSEventTypeLeftMouseDown, 
                        point, 
                        0,
                        AppKit.NSDate.timeIntervalSinceReferenceDate(), 
                        win['wid'], 
                        None, 
                        0, 
                        1, 
                        0
                    )
                    print(customEvent.description())
                    Quartz.CGEventPostToPid(win['pid'], customEvent.CGEvent())
                    # customEvent.release()
                    state['send_now'] = True



            elif data['type'] == 'mouse_up':
                with objc.autorelease_pool():
                    win = get_win(state)
                    x, y, w, h = win['bounds']
                    screenHeight = Quartz.NSScreen.mainScreen().frame().size.height
                    point = Quartz.CGPointMake(w * data['x'], screenHeight - h * (data['y']))
                    print(point)
                    customEvent = Quartz.NSEvent.mouseEventWithType_location_modifierFlags_timestamp_windowNumber_context_eventNumber_clickCount_pressure_(
                        Quartz.NSEventTypeLeftMouseUp, 
                        point, 
                        0,
                        AppKit.NSDate.timeIntervalSinceReferenceDate(), 
                        win['wid'], 
                        None, 
                        0, 
                        1, 
                        0
                    )
                    Quartz.CGEventPostToPid(win['pid'], customEvent.CGEvent())
                
                    state['send_now'] = True
            elif data['type'] == 'key_down':
                with objc.autorelease_pool():
                    if data['key'] in US_keyboard:
                        win = get_win(state)
                        key_down = Quartz.CGEventCreateKeyboardEvent(None, US_keyboard[data['key']], True)
                        Quartz.CGEventPostToPid(win['pid'], key_down)
                        # key_down.release()
                        state['send_now'] = True

            elif data['type'] == 'key_up':
                with objc.autorelease_pool():
                    if data['key'] in US_keyboard:
                        win = get_win(state)

                        key_up = Quartz.CGEventCreateKeyboardEvent(None, US_keyboard[data['key']], False)
                        Quartz.CGEventPostToPid(win['pid'], key_up)
                        # Quartz.CFRelease(key_up)
                        # key_up.release()
                        state['send_now'] = True

        elif msg.type == aiohttp.WSMsgType.ERROR:
            print('ws connection closed with exception %s' % ws.exception())
            task1.cancel()
        else:
            print(msg)


    await task1

    
    print('websocket connection closed')
    return ws

US_keyboard = {
    # Letters
    'a': 0,
    'b': 11,
    'c': 8,
    'd': 2,
    'e': 14,
    'f': 3,
    'g': 5,
    'h': 4,
    'i': 34,
    'j': 38,
    'k': 40,
    'l': 37,
    'm': 46,
    'n': 45,
    'o': 31,
    'p': 35,
    'q': 12,
    'r': 15,
    's': 1,
    't': 17,
    'u': 32,
    'v': 9,
    'w': 13,
    'x': 7,
    'y': 16,
    'z': 6,

    # Numbers
    '0': 29,
    '1': 18,
    '2': 19,
    '3': 20,
    '4': 21,
    '5': 23,
    '6': 22,
    '7': 26,
    '8': 28,
    '9': 25,

    # Symbols
    '!': 18,
    '@': 19,
    '#': 20,
    '$': 21,
    '%': 23,
    '^': 22,
    '&': 26,
    '*': 28,
    '(': 25,
    ')': 29,
    '-': 27,  # Dash
    '_': 27,  # Underscore
    '=': 24,
    '+': 24,
    '`': 50,  # Backtick
    '~': 50,
    '[': 33,
    ']': 30,
    '{': 33,
    '}': 30,
    ';': 41,
    ':': 41,
    "'": 39,
    '"': 39,
    ',': 43,
    '<': 43,
    '.': 47,
    '>': 47,
    '/': 44,
    '?': 44,
    '\\': 42,
    '|': 42,  # Pipe
    # TAB: 48,  # Tab: Shift-Tab sent for Tab
    # SPACE: 49,
    ' ': 49,  # Space

    'Enter': 36,

    # RETURN: 36,
    # DELETE: 117,
    # TAB: 48,
    # SPACE: 49,
    # ESCAPE: 53,
    # CAPS_LOCK: 57,
    # NUM_LOCK: 71,
    # SCROLL_LOCK: 107,
    # PAUSE: 113,
    # BACKSPACE: 51,
    # INSERT: 114,
    'Backspace': 51,

    # # Cursor movement
    'ArrowUp': 126,
    'ArrowDown': 125,
    'ArrowLeft': 123,
    'ArrowRight': 124,
    # PAGE_UP: 116,
    # PAGE_DOWN: 121,
}

async def hello(request):
    return web.Response(content_type='text/html', text="""
        <body>
        <style>
            #portal {
                width: 1200px;
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

            window.onkeydown = e => {
                e.preventDefault()
                send({
                    type: 'key_down', 
                    key: e.key
                })
            }

            document.addEventListener('mousewheel', e => {
                e.preventDefault()
                send({
                    'type': 'mouse_wheel',
                    deltaY: e.deltaY,
                    deltaX: e.deltaX
                })
            }, {passive: false});


            window.onkeyup = e => {
                e.preventDefault()
                send({
                    type: 'key_up', 
                    key: e.key
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
