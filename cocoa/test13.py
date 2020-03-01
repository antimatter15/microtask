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


for x in list(windowList(wl1)):
    if x['owner'] and 'Sublime' in x['owner']:
        print(x)

        theRect = Quartz.NSMakeRect(*x['bounds'])
        theImage = Quartz.CGWindowListCreateImage(
            theRect, 
            Quartz.kCGWindowListOptionIncludingWindow, 
            x['wid'], 
            Quartz.kCGWindowImageDefault);

        bitmapRep = Quartz.NSBitmapImageRep.alloc().initWithCGImage_(theImage)
        # nsImage = Quartz.NSImage.alloc().init()
        # nsImage.addRepresentation_(bitmapRep)
        # nsImage.setCacheMode_(Quartz.NSImageCacheNever)

        # print(nsImage)


        pngData = bitmapRep.representationUsingType_properties_(Quartz.NSPNGFileType, None)

        pngData.writeToFile_atomically_("screenie.png", True)
        # NSBitmapImageRep *bitmapRep = [[NSBitmapImageRep alloc] initWithCGImage:screenShot];
        # NSImage *image = [[NSImage alloc] init];
        # [image addRepresentation:bitmapRep];
        # [image setCacheMode:NSImageCacheNever];