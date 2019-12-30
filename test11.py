import Quartz
import AppKit
import time 



WID = 7543
PID = 3460

point = Quartz.CGPointMake(117.3, 797)

print(point)

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
Quartz.CGEventPostToPid(PID, customEvent.CGEvent());

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
print(customEvent.description())
Quartz.CGEventPostToPid(PID, customEvent.CGEvent());