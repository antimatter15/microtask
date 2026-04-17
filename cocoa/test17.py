import asyncio
import json
import time
import AppKit
import ApplicationServices as AS
import Foundation
import Quartz
import aiohttp
import objc
from aiohttp import web


# ---------- AX helpers ----------

def ax_get(el, attr):
    if el is None:
        return None
    try:
        err, v = AS.AXUIElementCopyAttributeValue(el, attr, None)
        return v if err == 0 else None
    except Exception:
        return None


def ax_set(el, attr, val):
    if el is None:
        return False
    try:
        return AS.AXUIElementSetAttributeValue(el, attr, val) == 0
    except Exception:
        return False


def ax_actions(el):
    if el is None:
        return []
    try:
        err, names = AS.AXUIElementCopyActionNames(el, None)
        return list(names) if err == 0 and names else []
    except Exception:
        return []


def ax_press(el):
    if el is None:
        return False
    try:
        return AS.AXUIElementPerformAction(el, 'AXPress') == 0
    except Exception:
        return False


def ax_parent(el):
    return ax_get(el, 'AXParent')


def find_ancestor_with_role(el, roles, max_depth=15):
    cur = el
    for _ in range(max_depth):
        if cur is None:
            return None
        if ax_get(cur, 'AXRole') in roles:
            return cur
        cur = ax_parent(cur)
    return None


def hit_test(app_ax, gx, gy):
    """Hit-test WITHIN a specific app's tree. Doing this system-wide would
    return whichever element is topmost visually — for a backgrounded
    target obscured by another window, that's the wrong app. App-scoped
    hit-test ignores z-order and finds what's at that point in Messages."""
    if app_ax is None:
        return None
    try:
        err, el = AS.AXUIElementCopyElementAtPosition(app_ax, float(gx), float(gy), None)
        return el if err == 0 else None
    except Exception:
        return None


# Roles where a single AXPress is the right interaction for a click.
AX_PRESSABLE_ROLES = {
    'AXButton', 'AXMenuItem', 'AXMenuButton', 'AXCheckBox', 'AXRadioButton',
    'AXLink', 'AXPopUpButton', 'AXComboBox', 'AXSegmentedControl',
    'AXDisclosureTriangle', 'AXToolbarButton',
}
# Roles where AXPress toggles selection (Catalyst sidebars, tables). We clear
# sibling selection first so AXPress ends up single-selecting.
AX_SELECTABLE_ROLES = {
    'AXRow', 'AXCell', 'AXStaticText', 'AXOutlineRow', 'AXListItem',
}
AX_TEXT_ROLES = {'AXTextField', 'AXTextArea'}
AX_SCROLL_ROLES = {'AXScrollArea'}


def single_select_row(el):
    """Make `el` the sole-selected, most-recently-pressed row in its list.

    Catalyst Messages-style sidebars: AXPress is a toggle, multiple rows
    can be selected simultaneously, and the visible pane follows whichever
    row was pressed most recently. A naive AXPress on a new row when
    another is already selected yields multi-select, not a switch.

    Pattern:
      1. Deselect every selected sibling (AXPress toggles off).
      2. If target is currently selected, toggle it off first.
      3. AXPress target — it becomes the last-pressed and the sole-selected,
         so the right pane renders it.
    """
    parent = ax_parent(el)
    if parent is not None:
        for sib in (ax_get(parent, 'AXChildren') or []):
            if sib is el:
                continue
            if ax_get(sib, 'AXSelected'):
                ax_press(sib)
                time.sleep(0.03)
    if ax_get(el, 'AXSelected'):
        ax_press(el)
        time.sleep(0.05)
    return ax_press(el)


# ---------- Target attach / detach ----------

def attach_target(pid):
    app_ax = AS.AXUIElementCreateApplication(pid)
    try:
        AS.AXUIElementSetMessagingTimeout(app_ax, 2.0)
    except Exception:
        pass
    # SyntheticAppFocusEnforcer flags — best-effort; Catalyst rejects them,
    # AppKit accepts them and becomes event-responsive while non-frontmost.
    ax_set(app_ax, 'AXEnhancedUserInterface', True)
    ax_set(app_ax, 'AXManualAccessibility', True)
    return app_ax


def detach_target(app_ax):
    if app_ax is None:
        return
    ax_set(app_ax, 'AXEnhancedUserInterface', False)
    ax_set(app_ax, 'AXManualAccessibility', False)


# ---------- Focus-steal guard (carried over from test16) ----------

RAISE_SUPPRESS_SETTLE = 0.12


def _frontmost_pid():
    app = AppKit.NSWorkspace.sharedWorkspace().frontmostApplication()
    return int(app.processIdentifier()) if app is not None else None


async def _restore_if_target_raised(prev_pid, target_pid, settle=RAISE_SUPPRESS_SETTLE):
    if prev_pid is None or int(prev_pid) == int(target_pid):
        return
    await asyncio.sleep(settle)
    cur = AppKit.NSWorkspace.sharedWorkspace().frontmostApplication()
    if cur is None or int(cur.processIdentifier()) != int(target_pid):
        return
    prev_app = AppKit.NSRunningApplication.runningApplicationWithProcessIdentifier_(int(prev_pid))
    if prev_app is None or prev_app.isTerminated():
        return
    prev_app.activateWithOptions_(AppKit.NSApplicationActivateIgnoringOtherApps)


def _guard_raise(target_pid):
    prev = _frontmost_pid()
    if prev is None or int(prev) == int(target_pid):
        return None
    return prev


def _schedule_restore(prev_pid, target_pid):
    if prev_pid is None:
        return
    asyncio.create_task(_restore_if_target_raised(prev_pid, target_pid))


# ---------- CGEvent fallback primitives ----------

def cg_move(pid, gx, gy):
    pt = Quartz.CGPointMake(gx, gy)
    ev = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventMouseMoved, pt, Quartz.kCGMouseButtonLeft)
    Quartz.CGEventPostToPid(pid, ev)


def cg_mouse_down(pid, gx, gy):
    pt = Quartz.CGPointMake(gx, gy)
    ev = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDown, pt, Quartz.kCGMouseButtonLeft)
    Quartz.CGEventPostToPid(pid, ev)


def cg_mouse_up(pid, gx, gy):
    pt = Quartz.CGPointMake(gx, gy)
    ev = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseUp, pt, Quartz.kCGMouseButtonLeft)
    Quartz.CGEventPostToPid(pid, ev)


def cg_scroll(pid, dy, dx):
    ev = Quartz.CGEventCreateScrollWheelEvent(None, Quartz.kCGScrollEventUnitPixel, 2, int(dy), int(dx))
    Quartz.CGEventPostToPid(pid, ev)


def cg_key(pid, keycode, down):
    ev = Quartz.CGEventCreateKeyboardEvent(None, keycode, down)
    Quartz.CGEventPostToPid(pid, ev)


# ---------- Window list / screenshot (unchanged from test15) ----------

def windowList(wl):
    for v in wl:
        yield {
            'pid': v.valueForKey_('kCGWindowOwnerPID'),
            'bounds': [int(v.valueForKey_('kCGWindowBounds').valueForKey_(x)) for x in ['X', 'Y', 'Width', 'Height']],
            'wid': v.valueForKey_('kCGWindowNumber'),
            'owner': v.valueForKey_('kCGWindowOwnerName'),
            'name': v.valueForKey_('kCGWindowName'),
        }


def get_win(state):
    arr = Quartz.CGWindowListCreateDescriptionFromArray([state['wid']])
    return list(windowList(arr))[0]


async def screenshot_transmitter(ws, state):
    jpegSettings = Foundation.NSDictionary({"NSImageCompressionFactor": 0.5})
    while True:
        with objc.autorelease_pool():
            if state['wid'] is None:
                await asyncio.sleep(0.1)
                continue
            win = get_win(state)
            theRect = Quartz.NSMakeRect(*win['bounds'])
            theImage = Quartz.CGWindowListCreateImage(
                theRect,
                Quartz.kCGWindowListOptionIncludingWindow,
                state['wid'],
                Quartz.kCGWindowImageShouldBeOpaque | Quartz.kCGWindowImageNominalResolution,
            )
            rep = Quartz.NSBitmapImageRep.alloc().initWithCGImage_(theImage)
            data = rep.representationUsingType_properties_(Quartz.NSJPEGFileType, jpegSettings)
            await ws.send_bytes(data.bytes())
        for _ in range(10):
            if state['send_now']:
                state['send_now'] = False
                continue
            await asyncio.sleep(0.001)


# ---------- Dispatcher ----------

def to_global(win, nx, ny):
    x, y, w, h = win['bounds']
    return (x + w * nx, y + h * ny)


def _classify(el):
    """Return (plan, role) if el is directly handleable, else (None, role)."""
    role = ax_get(el, 'AXRole') or ''
    if role in AX_TEXT_ROLES:
        return ('focus_text', role)
    actions = ax_actions(el)
    if role in AX_PRESSABLE_ROLES and 'AXPress' in actions:
        return ('press', role)
    if role in AX_SELECTABLE_ROLES and 'AXPress' in actions:
        return ('select_press', role)
    return (None, role)


def _search_descendants(el, max_depth=3):
    """BFS for an AX-actionable descendant (text field preferred)."""
    queue = [(el, 0)]
    while queue:
        cur, d = queue.pop(0)
        if d > 0:  # don't reclassify el itself
            plan, role = _classify(cur)
            if plan is not None:
                return (plan, cur, role)
        if d >= max_depth:
            continue
        for c in (ax_get(cur, 'AXChildren') or []):
            queue.append((c, d + 1))
    return None


def plan_click(el):
    if el is None:
        return ('cg', None, None)
    plan, role = _classify(el)
    if plan is not None:
        return (plan, el, role)
    # Walk up ancestors (sidebar rows often hit an inner AXImage avatar; the
    # selectable row is a parent).
    cur = ax_parent(el)
    for _ in range(5):
        if cur is None:
            break
        p, r = _classify(cur)
        if p is not None:
            return (p, cur, r)
        cur = ax_parent(cur)
    # Walk down into descendants (click on an AXCell wrapper → AXTextField
    # lives inside).
    hit = _search_descendants(el, max_depth=3)
    if hit is not None:
        return hit
    return ('cg', el, role)


def try_ax_scroll(el, dy, dx):
    scroll = find_ancestor_with_role(el, AX_SCROLL_ROLES)
    if scroll is None:
        return False
    actions = ax_actions(scroll)
    # Pixel-scroll granularity doesn't exist in AX — best we can do is page
    # actions. For small wheel deltas we prefer the CG fallback; AX only wins
    # if dy/dx is "big enough" to feel like paging.
    page = 80
    if abs(dy) >= page:
        act = 'AXScrollDownByPage' if dy > 0 else 'AXScrollUpByPage'
        if act in actions and AS.AXUIElementPerformAction(scroll, act) == 0:
            return True
    if abs(dx) >= page:
        act = 'AXScrollRightByPage' if dx > 0 else 'AXScrollLeftByPage'
        if act in actions and AS.AXUIElementPerformAction(scroll, act) == 0:
            return True
    return False


# ---------- websocket handler ----------

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    state = {
        'wid': None,
        'pid': None,
        'app_ax': None,
        'send_now': False,
        # For click routing: on mouse_down we hit-test and plan; on mouse_up
        # we decide AX vs CG based on drag distance.
        'pending_click': None,
        # Track AX-handled keys so we can swallow the matching key_up.
        'ax_keys_down': set(),
        # Last text field we clicked. AXFocused=True doesn't always actually
        # transfer focus on Catalyst apps (the call succeeds but AXFocused-
        # UIElement still reports a parent AXGroup). Remembering the element
        # we *intended* to type into lets us write via AXValue/AXSelectedText
        # regardless of the system's focus state.
        'last_text_el': None,
    }

    with objc.autorelease_pool():
        wl1 = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID)
        for x in list(windowList(wl1)):
            await ws.send_json({
                'type': 'add_option',
                'text': f"{x['owner']} - {x['name']}",
                'value': x['wid'],
            })

    task1 = asyncio.create_task(screenshot_transmitter(ws, state))

    async for msg in ws:
        if msg.type != aiohttp.WSMsgType.TEXT:
            if msg.type == aiohttp.WSMsgType.ERROR:
                print('ws error', ws.exception())
            continue
        data = json.loads(msg.data)
        t = data.get('type')

        if t == 'set_window':
            detach_target(state['app_ax'])
            state['wid'] = int(data['wid'])
            win = get_win(state)
            state['pid'] = int(win['pid'])
            state['app_ax'] = attach_target(state['pid'])
            state['pending_click'] = None
            state['ax_keys_down'] = set()

        elif t == 'mouse_move':
            with objc.autorelease_pool():
                win = get_win(state)
                gx, gy = to_global(win, data['x'], data['y'])
                cg_move(state['pid'], gx, gy)

        elif t == 'mouse_wheel':
            with objc.autorelease_pool():
                win = get_win(state)
                # Use last known cursor for hit-testing; we just sent a move,
                # but the browser doesn't give us coords with the wheel event.
                # Accept the ambiguity and hit-test at window center — for
                # AX-scroll this is fine since we walk up to the scroll area.
                x, y, w, h = win['bounds']
                cx, cy = x + w * 0.5, y + h * 0.5
                el = hit_test(state['app_ax'], cx, cy)
                if not try_ax_scroll(el, data['deltaY'], data['deltaX']):
                    cg_scroll(state['pid'], data['deltaY'], data['deltaX'])

        elif t == 'mouse_down':
            with objc.autorelease_pool():
                win = get_win(state)
                gx, gy = to_global(win, data['x'], data['y'])
                el = hit_test(state['app_ax'], gx, gy)
                plan, target_el, role = plan_click(el)
                print(f'down @ ({gx:.0f},{gy:.0f}) → plan={plan} role={role}')

                if plan == 'focus_text':
                    # Focus now; nothing more on mouse_up.
                    ax_set(target_el, 'AXFocused', True)
                    state['last_text_el'] = target_el
                elif plan == 'cg':
                    # No AX action fits: send the real CG down now so drag
                    # starts cleanly. Guard focus.
                    prev = _guard_raise(state['pid'])
                    cg_mouse_down(state['pid'], gx, gy)
                    _schedule_restore(prev, state['pid'])

                state['pending_click'] = {
                    'down_time': time.monotonic(),
                    'down_xy': (gx, gy),
                    'plan': plan,
                    'el': target_el,
                    'role': role,
                }

        elif t == 'mouse_up':
            with objc.autorelease_pool():
                win = get_win(state)
                gx, gy = to_global(win, data['x'], data['y'])
                pc = state.pop('pending_click', None)
                moved = 0.0
                if pc is not None:
                    dx = gx - pc['down_xy'][0]
                    dy = gy - pc['down_xy'][1]
                    moved = (dx * dx + dy * dy) ** 0.5

                # A real drag: always CG regardless of plan.
                is_drag = pc is not None and (moved > 5 or (time.monotonic() - pc['down_time']) > 0.5)

                if pc is None or pc['plan'] == 'cg' or is_drag:
                    # CG path: ensure a down was sent. If the original plan
                    # was AX (focus/press/select_press) we didn't send down
                    # earlier, so send it now.
                    prev = _guard_raise(state['pid'])
                    if pc is not None and pc['plan'] in ('press', 'select_press'):
                        cg_mouse_down(state['pid'], *pc['down_xy'])
                    cg_mouse_up(state['pid'], gx, gy)
                    _schedule_restore(prev, state['pid'])
                elif pc['plan'] == 'press':
                    ok = ax_press(pc['el'])
                    print(f'  AXPress {pc["role"]}: {ok}')
                elif pc['plan'] == 'select_press':
                    fresh = hit_test(state['app_ax'], gx, gy) or pc['el']
                    ok = single_select_row(fresh)
                    print(f'  single_select {pc["role"]}: {ok} '
                          f'(selected={ax_get(fresh, "AXSelected")})')
                # 'focus_text' already handled on down.
                state['send_now'] = True

        elif t == 'key_down':
            with objc.autorelease_pool():
                key = data['key']
                app_ax = state['app_ax']
                # Prefer the element we intentionally focused via click;
                # fall back to AXFocusedUIElement only if we haven't clicked
                # a text field yet this session.
                target = state['last_text_el']
                target_role = ax_get(target, 'AXRole') if target is not None else None
                if target_role not in AX_TEXT_ROLES:
                    target = ax_get(app_ax, 'AXFocusedUIElement')
                    target_role = ax_get(target, 'AXRole') if target else None

                # Backspace → trim via AXValue.
                if key == 'Backspace' and target_role in AX_TEXT_ROLES:
                    cur = ax_get(target, 'AXValue') or ''
                    if cur and ax_set(target, 'AXValue', cur[:-1]):
                        state['ax_keys_down'].add(key)
                        state['send_now'] = True
                        continue

                # Printable single-character key + text field →
                # append via AXValue. Try AXSelectedText first (proper
                # insertion-at-cursor), fall back to full-value append if
                # the app doesn't honor AXSelectedText.
                if (target_role in AX_TEXT_ROLES
                        and isinstance(key, str)
                        and len(key) == 1):
                    before = ax_get(target, 'AXValue') or ''
                    if (ax_set(target, 'AXSelectedText', key)
                            and (ax_get(target, 'AXValue') or '') != before):
                        state['ax_keys_down'].add(key)
                        state['send_now'] = True
                        continue
                    if ax_set(target, 'AXValue', before + key):
                        state['ax_keys_down'].add(key)
                        state['send_now'] = True
                        continue

                # Fallback: CGEvent keyboard event by US-keycode map.
                code = US_keyboard.get(key)
                if code is not None:
                    cg_key(state['pid'], code, True)
                    state['send_now'] = True

        elif t == 'key_up':
            with objc.autorelease_pool():
                key = data['key']
                # If the matching down was handled via AX, swallow the up.
                if key in state['ax_keys_down']:
                    state['ax_keys_down'].discard(key)
                    continue
                code = US_keyboard.get(key)
                if code is not None:
                    cg_key(state['pid'], code, False)

    task1.cancel()
    try:
        await task1
    except asyncio.CancelledError:
        pass
    detach_target(state['app_ax'])
    print('websocket connection closed')
    return ws


# ---------- US keyboard map (same as test15) ----------

US_keyboard = {
    'a': 0, 'b': 11, 'c': 8, 'd': 2, 'e': 14, 'f': 3, 'g': 5, 'h': 4, 'i': 34,
    'j': 38, 'k': 40, 'l': 37, 'm': 46, 'n': 45, 'o': 31, 'p': 35, 'q': 12,
    'r': 15, 's': 1, 't': 17, 'u': 32, 'v': 9, 'w': 13, 'x': 7, 'y': 16, 'z': 6,
    '0': 29, '1': 18, '2': 19, '3': 20, '4': 21, '5': 23, '6': 22, '7': 26,
    '8': 28, '9': 25,
    '!': 18, '@': 19, '#': 20, '$': 21, '%': 23, '^': 22, '&': 26, '*': 28,
    '(': 25, ')': 29,
    '-': 27, '_': 27, '=': 24, '+': 24, '`': 50, '~': 50, '[': 33, ']': 30,
    '{': 33, '}': 30, ';': 41, ':': 41, "'": 39, '"': 39, ',': 43, '<': 43,
    '.': 47, '>': 47, '/': 44, '?': 44, '\\': 42, '|': 42,
    'Tab': 48, ' ': 49, 'Enter': 36, 'Backspace': 51,
    'ArrowUp': 126, 'ArrowDown': 125, 'ArrowLeft': 123, 'ArrowRight': 124,
    'Escape': 53,
}


# ---------- HTML (same interface as test15) ----------

async def hello(request):
    return web.Response(content_type='text/html', text="""
        <body>
        <style>
            #portal { width: 1200px; display: block; }
        </style>
        <select id="options">
            <option disabled selected>Select a window</option>
        </select>
        <img id="portal">
        <script>
            var ws = new WebSocket('ws://' + location.host + '/ws');
            function send(x){ ws.send(JSON.stringify(x)) }
            document.getElementById('options').onchange = e => {
                location.hash = '#' + e.target.value
                send({ type: 'set_window', wid: e.target.value })
            }
            const portal = document.getElementById('portal');
            portal.onmousemove = e => {
                let bb = portal.getBoundingClientRect()
                send({ type: 'mouse_move', x: (e.clientX - bb.x)/bb.width, y: (e.clientY - bb.y)/bb.height })
            }
            portal.onmousedown = e => {
                e.preventDefault()
                let bb = portal.getBoundingClientRect()
                send({ type: 'mouse_down', x: (e.clientX - bb.x)/bb.width, y: (e.clientY - bb.y)/bb.height })
            }
            portal.onmouseup = e => {
                e.preventDefault()
                let bb = portal.getBoundingClientRect()
                send({ type: 'mouse_up', x: (e.clientX - bb.x)/bb.width, y: (e.clientY - bb.y)/bb.height })
            }
            window.onkeydown = e => { e.preventDefault(); send({ type: 'key_down', key: e.key }) }
            window.onkeyup = e => { e.preventDefault(); send({ type: 'key_up', key: e.key }) }
            document.addEventListener('mousewheel', e => {
                e.preventDefault()
                send({ type: 'mouse_wheel', deltaY: e.deltaY, deltaX: e.deltaX })
            }, { passive: false });
            ws.onclose = () => { document.body.innerHTML = "Please refresh the page (Socket closed)" }
            ws.onmessage = function (event) {
                if (event.data instanceof Blob) {
                    portal.src = URL.createObjectURL(event.data); return;
                }
                let data = JSON.parse(event.data);
                if (data.type === 'add_option') {
                    document.getElementById('options').appendChild(new Option(data.text, data.value))
                    if ('#' + data.value === location.hash) {
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

if __name__ == '__main__':
    web.run_app(app)
