// Via pastie: https://stackoverflow.com/a/857434

#import "EventForwardingView.h"

#import "Globals.h"


#define PID     7197   // The process ID of the process that events should be forwarded to (get from Quartz Debug)
#define WID     6390   // The window ID of the window of the process that events are being forwarded to (get from Quartz Debug)


@implementation EventForwardingView

- (void)mouseDown: (NSEvent *)event {[self forwardEvent: event];}
- (void)rightMouseDown: (NSEvent *)event {[self forwardEvent: event];}
- (void)otherMouseDown: (NSEvent *)event {[self forwardEvent: event];}
- (void)mouseUp: (NSEvent *)event {[self forwardEvent: event];}
- (void)rightMouseUp: (NSEvent *)event {[self forwardEvent: event];}
- (void)otherMouseUp: (NSEvent *)event {[self forwardEvent: event];}
- (void)mouseMoved: (NSEvent *)event {[self forwardEvent: event];}
- (void)mouseDragged: (NSEvent *)event {[self forwardEvent: event];}
- (void)rightMouseDragged: (NSEvent *)event {[self forwardEvent: event];}
- (void)otherMouseDragged: (NSEvent *)event {[self forwardEvent: event];}

- (void)forwardEvent: (NSEvent *)event
{                                         


    ProcessSerialNumber psn;
    CGEventRef CGEvent;
    NSEvent *customEvent;

    customEvent = [NSEvent mouseEventWithType: [event type]
                                     location: [event locationInWindow]
                                modifierFlags: [event modifierFlags] | NSCommandKeyMask
                                    timestamp: [event timestamp]
                                 windowNumber: WID
                                      context: nil
                                  eventNumber: 0
                                   clickCount: 1
                                     pressure: 0];

    CGEvent = [customEvent CGEvent];

    NSAssert(GetProcessForPID(PID, &psn) == noErr, @"GetProcessForPID failed!");

    CGEventPostToPSN(&psn, CGEvent);

}

@end