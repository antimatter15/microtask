chrome.browserAction.onClicked.addListener(async function(tab) {
    await chrome.tabs.executeScript(tab.id, {
        file: 'controller.js',
    })
    let stream = await chrome.tabCapture.capture({
        audio: false,
        video: true,
    })

    let monitor = await chrome.tabs.create({
        windowId: tab.windowId,
        index: tab.index + 1,
        url: 'monitor.html',
        active: true,
    })

    // chrome.tabs.update(tab.id, {
    //     pinned: true,
    // })

    onTabActivate(tab.id, function() {
        chrome.tabs.update(monitor.id, {
            active: true,
        })
    })

    // let response = await chrome.tabs.sendMessage(tab.id, { greeting: 'hello' })
    console.log('created monitor')
    let debugId = {
        tabId: tab.id,
    }
    await chrome.debugger.attach(debugId, '1.2')

    let peer = new SimplePeer({
        initiator: false,
        stream: stream,
    })

    peer.on('signal', data => {
        chrome.tabs.sendMessage(monitor.id, {
            type: 'signal',
            data: data,
        })
    })

    peer.on('data', function(chunk) {
        let data = JSON.parse(chunk)
        console.log('got a chunk', chunk)
        if (data.type === 'resize') {
            chrome.debugger.sendCommand(debugId, 'Emulation.setDeviceMetricsOverride', {
                width: data.width,
                height: data.height,
                deviceScaleFactor: data.deviceScaleFactor,
                mobile: false,
                scale: 1,
                fitWindow: true,
            })
        } else if (data.type === 'mouse') {
            chrome.debugger.sendCommand(debugId, 'Input.dispatchMouseEvent', {
                type: data.eventType,
                x: data.x,
                y: data.y,
                modifiers: data.modifiers,
                button: data.button,
                buttons: data.buttons,
                deltaX: data.deltaX,
                deltaY: data.deltaY,
                clickCount: data.clickCount,
            })
        } else if (data.type === 'keyboard') {
            chrome.debugger.sendCommand(debugId, 'Input.dispatchKeyEvent', {
                type: data.eventType,

                modifiers: data.modifiers,
                text: data.text,
                unmodifiedText: data.unmodifiedText,
                keyIdentifier: data.keyIdentifier,
                code: data.code,
                key: data.key,
                windowsVirtualKeyCode: data.windowsVirtualKeyCode,
                nativeVirtualKeyCode: data.nativeVirtualKeyCode,
                autoRepeat: data.autoRepeat,
                isKeypad: data.isKeypad,
                isSystemKey: data.isSystemKey,
            })
        }
    })

    peer.on('close', function() {
        console.log('closing peer')
    })

    peer.on('connect', async function() {})

    onTabMessage(monitor.id, function(message, sender, sendResponse) {
        console.log(message)
        if (message.type === 'signal') {
            peer.signal(message.data)
        }
    })

    onTabClose(monitor.id, function() {
        chrome.debugger.detach(debugId)
        stream.getVideoTracks()[0].stop()
    })
})

function onTabMessage(tabId, messageHandler) {
    function onMessage(request, sender, sendResponse) {
        if (sender.tab.id === tabId) {
            messageHandler(request, sender, sendResponse)
        }
    }
    chrome.runtime.onMessage.addListener(onMessage)
    onTabClose(tabId, function() {
        chrome.runtime.onMessage.removeListener(onMessage)
    })
}

function onTabClose(tabId, handler) {
    function removeListener(removedTabId) {
        if (removedTabId === tabId) {
            handler()
        }
    }
    chrome.tabs.onRemoved.addListener(removeListener)
}

function onTabActivate(tabId, onActive) {
    function activeListener(activeInfo) {
        if (activeInfo.tabId === tabId) {
            onActive(activeInfo)
        }
    }
    chrome.tabs.onActivated.addListener(activeListener)
    onTabClose(tabId, function() {
        chrome.tabs.onActivated.removeListener(activeListener)
    })
}
