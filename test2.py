# https://github.com/oreon/textgen/blob/72f15dcb70d8bcec3cfe355b43161dd67f593888/screen.py

import pyautogui
import time
import os
import Quartz
import objc
cnt = 0

# pid = 6845  # get/input a real pid from somewhere for the target app.
# point = Quartz.CGPoint()
# point.x = 1075 # get a target x from somewhere
# point.y = 745  # likewise, your target y from somewhere
# left_mouse_down_event = Quartz.CGEventCreateMouseEvent(objc.NULL, Quartz.kCGEventLeftMouseDown, point, Quartz.kCGMouseButtonLeft)
# left_mouse_up_event = Quartz.CGEventCreateMouseEvent(objc.NULL, Quartz.kCGEventLeftMouseUp, point, Quartz.kCGMouseButtonLeft)
#
# print ( Quartz.CGEventPostToPid(pid, left_mouse_down_event) )
# Quartz.CGEventPostToPid(pid, left_mouse_up_event)
#
# #pid = 2253 # get/input a real pid from somewhere for the target app.
# type_a_key_down_event = Quartz.CGEventCreateKeyboardEvent(objc.NULL, 0, True)
# type_a_key_up_event = Quartz.CGEventCreateKeyboardEvent(objc.NULL, 0, False)
#
# Quartz.CGEventPostToPid(pid, type_a_key_down_event)
# Quartz.CGEventPostToPid(pid, type_a_key_up_event)`