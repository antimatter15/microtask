// Unreliably, but I don't know if my problem was that the app I was 
// targeting was a flash-based app in a browser window. I was testing 
// with a drawing app built in javascript, and that was drawing well 
// while in background, but once I tried to test it with the flash-based 
// app I just couldn't get it to trigger background-clicks. 


NSEvent *customEvent = [NSEvent mouseEventWithType: NSEventTypeLeftMouseDown
                                          location: point
                                     modifierFlags: NSEventModifierFlagCommand
                                         timestamp:[NSDate timeIntervalSinceReferenceDate]
                                      windowNumber:[self.windowID intValue]
                                           context: nil
                                       eventNumber: 0
                                        clickCount: 1
                                          pressure: 0];

CGEvent = [customEvent CGEvent];
CGEventPostToPid(PID, CGEvent);