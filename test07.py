import AppKit
import Quartz

def get_pid_by_name(name):
    pids = []
    for window in Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID):
        pid = window['kCGWindowOwnerPID']
        ownerName = window['kCGWindowOwnerName']
        windowNumber = window['kCGWindowNumber']
        windowTitle = window.get('kCGWindowName', u'Unknown')
        geometry = window['kCGWindowBounds']
        if name in ownerName or name in windowTitle:
            pids.append(pid)
        pids = list(set(pids))
    return pids

customEvent = Quartz.NSEvent.mouseEventWithType_location_modifierFlags_timestamp_windowNumber_context_eventNumber_clickCount_pressure_(
    AppKit.NSEventTypeLeftMouseDown, 
    (100,100), 
    AppKit.NSEventModifierFlagCommand, 
    AppKit.NSDate.timeIntervalSinceReferenceDate(), 
    0, 
    None, 
    0, 
    1, 
    0
)

cgEvent = customEvent.CGEvent()

PID = get_pid_by_name('Chrome')[0]

print(Quartz.CGEventPostToPid(PID, cgEvent))