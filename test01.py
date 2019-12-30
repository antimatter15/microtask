# https://github.com/wangandai/mmbot/blob/e54373121ad83ebcbaef3d4e1b7efbee3bcce0cf/macro_experiment.py

from subprocess import check_output
import time
import Quartz
from Quartz import CoreGraphics
from AppKit import NSWorkspace
import Foundation


def get_pid(name):
    return check_output(["pgrep", name])


def to_unichr(s):
    nss = Foundation.NSString(s)[0]
    print(nss)
    return len(nss), list(map(ord, nss))

# # get process Id
# pid = int(get_pid("Chrome$"))
# print(pid)

my_process = next(filter(lambda x: x, [x if x.get('NSApplicationName') == 'TextEdit' else None for x in  NSWorkspace.sharedWorkspace().launchedApplications()]))

psn = Foundation.NSDictionary({
    "NSApplicationProcessSerialNumberHigh": my_process["NSApplicationProcessSerialNumberHigh"],
    "NSApplicationProcessSerialNumberLow": my_process["NSApplicationProcessSerialNumberLow"]
})
# print(type(my_process))
print(psn)
# send event to process Id
for i in range(5):
    key_down = Quartz.CGEventCreateKeyboardEvent(None, 3, True)
    key_up = Quartz.CGEventCreateKeyboardEvent(None, 3, False)

    # Quartz.CGEventKeyboardSetUnicodeString(key_down, 1, "f")
    # Quartz.CGEventKeyboardSetUnicodeString(key_up, 1, "f")
    
    print(key_down)
    print(psn)

    Quartz.CGEventPostToPSN(psn, key_down)
    Quartz.CGEventPostToPSN(psn, key_up)

    time.sleep(1)

Quartz.CFRelease(key_down)
Quartz.CFRelease(key_up)