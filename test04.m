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