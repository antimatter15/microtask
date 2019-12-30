import Quartz
import AppKit
import time 

wl1 = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID)

def windowList(wl):
    for v in wl:
        yield {
            'pid': v.valueForKey_('kCGWindowOwnerPID'),
            'bounds': [int(v.valueForKey_('kCGWindowBounds').valueForKey_(x)) for x in ['X', 'Y', 'Width', 'Height']],
            'wid': v.valueForKey_('kCGWindowNumber'),
            'owner': v.valueForKey_('kCGWindowOwnerName'),
            'name': v.valueForKey_('kCGWindowName')
        }


app = [x for x in list(windowList(wl1)) if x['owner'] and 'Quartz' in x['owner']]

print(app)

# win = app[0]



# # Quartz.CGEventPostToPid(win['pid'], customEvent.CGEvent())

# def mouseEvent(point, nsEventType):
#     customEvent = Quartz.NSEvent.mouseEventWithType_location_modifierFlags_timestamp_windowNumber_context_eventNumber_clickCount_pressure_(
#         nsEventType, 
#         point, 
#         # AppKit.NSEventModifierFlagCommand, 
#         0,
#         AppKit.NSDate.timeIntervalSinceReferenceDate(), 
#         win['wid'], 
#         None, 
#         0, 
#         1, 
#         0
#     )

# def getEventRef(mouseButton, eventType, point):
#     theEvent = Quartz.CGEventCreateMouseEvent(None, eventType, point, mouseButton);
#     Quartz.CGEventSetType(theEvent, eventType)
#     return theEvent

# def triggerBackgroundClick(PID, point):
#     Quartz.CGEventPostToPid(PID, getEventRef(Quartz.kCGMouseButtonLeft, Quartz.kCGEventMouseMoved, point))
#     time.sleep(0.05)
#     Quartz.CGEventPostToPid(PID, getEventRef(Quartz.kCGMouseButtonLeft, Quartz.kCGEventLeftMouseDown, point))
#     time.sleep(0.05)
#     Quartz.CGEventPostToPid(PID, getEventRef(Quartz.kCGMouseButtonLeft, Quartz.kCGEventLeftMouseUp, point))
#     time.sleep(0.05)

#     # Quartz.CGEventPostToPid(PID, mouseEvent(point, AppKit.NSEventTypeMouseMoved));
#     # Quartz.CGEventPostToPid(PID, mouseEvent(point, AppKit.NSEventTypeLeftMouseDown));
#     # Quartz.CGEventPostToPid(PID, mouseEvent(point, AppKit.NSEventTypeLeftMouseUp));
#     # Quartz.CGEventPostToPid(PID, mouseEvent(point, AppKit.NSEventTypeLeftMouseDown));
#     # Quartz.CGEventPostToPid(PID, mouseEvent(point, AppKit.NSEventTypeLeftMouseUp));


# def clickMouse(PID, point):
#     moveEvent = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventMouseMoved, point, Quartz.kCGMouseButtonLeft)
#     Quartz.CGEventSetType(moveEvent, Quartz.kCGEventMouseMoved)
#     Quartz.CGEventPostToPid(PID, moveEvent)

#     time.sleep(0.1)
#     pressEvent = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDown, point, Quartz.kCGMouseButtonLeft)
#     Quartz.CGEventSetType(pressEvent, Quartz.kCGEventLeftMouseDown)
#     Quartz.CGEventSetIntegerValueField(pressEvent, Quartz.kCGMouseEventClickState, 5)
#     Quartz.CGEventPostToPid(PID, pressEvent)
#     time.sleep(0.1)

#     releaseEvent = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseUp, point, Quartz.kCGMouseButtonLeft)
#     Quartz.CGEventSetType(releaseEvent, Quartz.kCGEventLeftMouseUp)
#     Quartz.CGEventSetIntegerValueField(releaseEvent, Quartz.kCGMouseEventClickState, 5)
#     Quartz.CGEventPostToPid(PID, releaseEvent)
#     time.sleep(0.1)



#     moveEvent = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventMouseMoved, (200,200), Quartz.kCGMouseButtonLeft)
#     Quartz.CGEventSetType(moveEvent, Quartz.kCGEventMouseMoved)
#     Quartz.CGEventPostToPid(PID, moveEvent)


#     # pressEvent = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDown, point, Quartz.kCGMouseButtonLeft)
#     # Quartz.CGEventSetType(pressEvent, Quartz.kCGEventLeftMouseDown)

#     # releaseEvent = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseUp, point, Quartz.kCGMouseButtonLeft)
#     # Quartz.CGEventSetType(releaseEvent, Quartz.kCGEventLeftMouseUp)
    



#     # customEvent = Quartz.NSEvent.mouseEventWithType_location_modifierFlags_timestamp_windowNumber_context_eventNumber_clickCount_pressure_(
#     #     AppKit.NSEventTypeMouseMoved, 
#     #     point, 
#     #     0, 
#     #     AppKit.NSDate.timeIntervalSinceReferenceDate(), 
#     #     win['wid'], 
#     #     None, 
#     #     0, 
#     #     1, 
#     #     0
#     # )
#     # Quartz.CGEventPostToPid(PID, customEvent.CGEvent())

#     # NSEvent *customEvent = [NSEvent mouseEventWithType: NSEventTypeLeftMouseDown
#     #                                           location: point
#     #                                      modifierFlags: 0 | NSEventModifierFlagCommand
#     #                                          timestamp:[NSDate timeIntervalSinceReferenceDate]
#     #                                       windowNumber:[self.windowID intValue]
#     #                                            context: nil
#     #                                        eventNumber: 0
#     #                                         clickCount: 1
#     #                                           pressure: 0];

#     # customEvent = Quartz.NSEvent.mouseEventWithType_location_modifierFlags_timestamp_windowNumber_context_eventNumber_clickCount_pressure_(
#     #     AppKit.NSEventTypeLeftMouseDown, 
#     #     point, 
#     #     0 | AppKit.NSEventModifierFlagCommand, 
#     #     AppKit.NSDate.timeIntervalSinceReferenceDate(), 
#     #     win['wid'], 
#     #     None, 
#     #     0, 
#     #     1, 
#     #     0
#     # )
#     # Quartz.CGEventPostToPid(PID, customEvent.CGEvent())


#     # customEvent = Quartz.NSEvent.mouseEventWithType_location_modifierFlags_timestamp_windowNumber_context_eventNumber_clickCount_pressure_(
#     #     AppKit.NSEventTypeLeftMouseUp, 
#     #     point, 
#     #     0 | AppKit.NSEventModifierFlagCommand, 
#     #     AppKit.NSDate.timeIntervalSinceReferenceDate(), 
#     #     win['wid'], 
#     #     None, 
#     #     0, 
#     #     1, 
#     #     0
#     # )
#     # Quartz.CGEventPostToPid(PID, customEvent.CGEvent())


#     # Quartz.CGEventPost(Quartz.kCGHIDEventTap, pressEvent)
#     # Quartz.CGEventPostToPid(PID, pressEvent)
#     # # Quartz.CGEventPost(Quartz.kCGHIDEventTap, releaseEvent)
#     # Quartz.CGEventPostToPid(PID, releaseEvent)

# clickMouse(win['pid'], (100, 100))

# # def clickMouse(PID, point):

#     # event1 = Quartz.CGEventCreateMouseEvent(None, eventType, point, mouseButton)
#     # event2 = Quartz.CGEventCreateMouseEvent(None, eventType, point, mouseButton)    
#     # CGEventSetType(event1, mouseDown);
#     # CGEventSetType(event2, mouseUp);

#     # CGEventSetFlags(event1, modifiers);
#     # CGEventSetFlags(event2, modifiers)

#     # CGEventSetIntegerValueField(event1, kCGMouseEventClickState, clickCount);
#     # CGEventSetIntegerValueField(event2, kCGMouseEventClickState, clickCount);

# # triggerBackgroundClick(win['pid'], Quartz.NSMakePoint(500,500))
# # Quartz.NSMakePoint(200,200)


# # Quartz.CGEventPostToPid(win['pid'], customEvent.CGEvent())

# # keycode = 3
# # keyDown = Quartz.CGEventCreateKeyboardEvent(None, keycode, True)
# # # Release the key
# # keyUp = Quartz.CGEventCreateKeyboardEvent(None, keycode, False)

# # modFlags = 0
# # # Set modflags on keyDown (default None):
# # Quartz.CGEventSetFlags(keyDown, modFlags)
# # # Set modflags on keyUp:
# # Quartz.CGEventSetFlags(keyUp, modFlags)

# # # Post the event to the given app
# # Quartz.CGEventPostToPid(win['pid'], keyDown)
# # Quartz.CGEventPostToPid(win['pid'], keyUp)