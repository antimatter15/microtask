chrome.browserAction.onClicked.addListener(async function(tab) {
    let stream = await chrome.tabCapture.capture({
        audio: true,
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

    // onTabActivate(tab.id, function() {
    //     chrome.tabs.update(monitor.id, {
    //         active: true,
    //     })
    // })

    let port
    let peer

    onTabPort(tab.id, function(newPort) {
        if (port) port.disconnect()
        port = newPort

        port.onMessage.addListener(function(data) {
            if (data.type === 'relay') {
                peer.write(JSON.stringify(data.payload))
            }
        })
    })

    function installContentScript() {
        chrome.tabs.executeScript(tab.id, {
            file: 'lib/syn.js',
        })
        chrome.tabs.executeScript(tab.id, {
            file: 'controller.js',
        })
    }
    // re-run content script when tab reloads
    onTabLoad(tab.id, function() {
        installContentScript()
    })

    onTabPort(monitor.id, function(monitorPort) {
        // re-run content script when monitor reloads
        installContentScript()

        peer = new SimplePeer({
            initiator: false,
            stream: stream,
        })

        peer.on('signal', data => {
            monitorPort.postMessage({
                type: 'signal',
                data: data,
            })
        })

        peer.on('data', function(chunk) {
            let data = JSON.parse(chunk)

            if (data.type === 'relay') {
                port.postMessage(data.payload)
            }
        })

        peer.on('close', function() {
            console.log('closing peer')
        })

        peer.on('connect', async function() {
            console.log('peer connected')
        })

        monitorPort.onMessage.addListener(function(data) {
            if (data.type === 'signal') {
                peer.signal(data.data)
            }
        })

        monitorPort.onDisconnect.addListener(function() {
            peer.destroy()
        })
    })

    onTabClose(monitor.id, function() {
        for (let track of stream.getVideoTracks()) {
            track.stop()
        }
        port.destroy()
    })
})

function onTabPort(tabId, portHandler) {
    function onPort(port) {
        if (port.sender.tab.id === tabId) {
            portHandler(port)
        }
    }
    chrome.runtime.onConnect.addListener(onPort)
    onTabClose(tabId, function() {
        chrome.runtime.onConnect.removeListener(onMessage)
    })
}

// function onTabMessage(tabId, messageHandler) {
//     function onMessage(request, sender, sendResponse) {
//         if (sender.tab.id === tabId) {
//             messageHandler(request, sender, sendResponse)
//         }
//     }
//     chrome.runtime.onMessage.addListener(onMessage)
//     onTabClose(tabId, function() {
//         chrome.runtime.onMessage.removeListener(onMessage)
//     })
// }

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

function onTabLoad(tabId, onLoad) {
    function onTabUpdate(updatedTabId, changeInfo, tab) {
        if (updatedTabId === tabId && changeInfo.status === 'complete') {
            onLoad(tab)
        }
    }
    chrome.tabs.onUpdated.addListener(onTabUpdate)
    onTabClose(tabId, function() {
        chrome.tabs.onUpdated.removeListener(onMessage)
    })
}
