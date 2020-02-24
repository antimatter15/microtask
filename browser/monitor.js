const monitor = document.getElementById('monitor')
const container = document.getElementById('container')

let peer = new SimplePeer({
    initiator: true,
})

peer.on('signal', data => {
    console.log('got signal', data)
    chrome.runtime.sendMessage({ type: 'signal', data: data })
})

function send(data) {
    peer.write(JSON.stringify(data))
}

peer.on('connect', () => {
    console.log('connected')
})

function throttle(fn) {
    let evt
    return function(...args) {
        if (evt) clearTimeout(evt)
        evt = setTimeout(() => fn(...args), 500)
    }
}

function sendViewport() {
    console.log('resizing')
    send({
        type: 'resize',
        width: container.offsetWidth,
        height: container.offsetHeight,
        deviceScaleFactor: devicePixelRatio,
    })

    const containerAspectRatio = container.offsetWidth / container.offsetHeight
    const videoAspectRatio = monitor.videoWidth / monitor.videoHeight
    const videoScale = containerAspectRatio / videoAspectRatio

    if (videoAspectRatio > containerAspectRatio) {
        // we will have letterboxes on the side

        monitor.style.height = container.offsetHeight + 'px'
        monitor.style.width = 'auto'
        monitor.style.marginLeft =
            Math.round((-container.offsetWidth * (1 / videoScale - 1)) / 2) + 'px'
        monitor.style.marginTop = '0px'
    } else {
        // we will have letterboxes on the top
        monitor.style.height = 'auto'
        monitor.style.width = container.offsetWidth + 'px'
        monitor.style.marginLeft = '0px'
        monitor.style.marginTop =
            Math.round((-container.offsetHeight * (videoScale - 1)) / 2) + 'px'
    }
}

container.onmousemove = e => {
    e.preventDefault()
    const bb = container.getBoundingClientRect()
    send({
        type: 'mouse',
        eventType: 'mouseMoved',
        x: e.clientX - bb.x,
        y: e.clientY - bb.y,
    })
}

container.oncontextmenu = e => {
    e.preventDefault()
}

container.onmousedown = e => {
    e.preventDefault()
    const bb = container.getBoundingClientRect()
    const buttons = { 0: 'none', 1: 'left', 2: 'middle', 3: 'right' }
    send({
        type: 'mouse',
        eventType: 'mousePressed',
        button: buttons[e.which],
        buttons: e.which,
        modifiers:
            (e.altKey ? 1 : 0) | (e.ctrlKey ? 2 : 0) | (e.metaKey ? 4 : 0) | (e.shiftKey ? 8 : 0),
        x: e.clientX - bb.x,
        y: e.clientY - bb.y,
        clickCount: 1,
    })
}

container.onmouseup = e => {
    e.preventDefault()
    const bb = container.getBoundingClientRect()
    const buttons = { 0: 'none', 1: 'left', 2: 'middle', 3: 'right' }
    send({
        type: 'mouse',
        eventType: 'mouseReleased',
        buttons: e.which,
        modifiers:
            (e.altKey ? 1 : 0) | (e.ctrlKey ? 2 : 0) | (e.metaKey ? 4 : 0) | (e.shiftKey ? 8 : 0),
        button: buttons[e.which],
        x: e.clientX - bb.x,
        y: e.clientY - bb.y,
        clickCount: 1,
    })
}

document.addEventListener(
    'mousewheel',
    e => {
        e.preventDefault()
        console.log(e.deltaX)
        send({
            type: 'mouse',
            eventType: 'mouseWheel',
            modifiers:
                (e.altKey ? 1 : 0) |
                (e.ctrlKey ? 2 : 0) |
                (e.metaKey ? 4 : 0) |
                (e.shiftKey ? 8 : 0),
            x: 0,
            y: 0,
            deltaX: e.deltaX,
            deltaY: e.deltaY,
        })
    },
    { passive: false }
)

window.onkeydown = window.onkeyup = window.onkeypress = event => {
    const eventTypes = { keydown: 'keyDown', keyup: 'keyUp', keypress: 'char' }
    const text = event.type === 'keypress' ? String.fromCharCode(event.charCode) : undefined

    send({
        type: 'keyboard',
        eventType: eventTypes[event.type],
        modifiers:
            (event.altKey ? 1 : 0) |
            (event.ctrlKey ? 2 : 0) |
            (event.metaKey ? 4 : 0) |
            (event.shiftKey ? 8 : 0),
        text: text,
        unmodifiedText: text ? text.toLowerCase() : undefined,
        keyIdentifier: event.keyIdentifier,
        code: event.code,
        key: event.key,
        windowsVirtualKeyCode: event.keyCode,
        nativeVirtualKeyCode: event.keyCode,
        autoRepeat: false,
        isKeypad: false,
        isSystemKey: false,
    })
}

window.onresize = throttle(() => sendViewport())

chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
    if (request.type === 'signal') {
        peer.signal(request.data)
    }
    // console.log(sender.tab ? 'from a content script:' + sender.tab.url : 'from the extension')
})

peer.on('stream', stream => {
    if ('srcObject' in monitor) {
        monitor.srcObject = stream
    } else {
        monitor.src = window.URL.createObjectURL(stream) // for older browsers
    }
    monitor.play()
    sendViewport()
    console.log(monitor.videoWidth, monitor.videoHeight)
})
