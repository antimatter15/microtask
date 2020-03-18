const monitor = document.getElementById('monitor')
const container = document.getElementById('container')

let peer = new SimplePeer({
    initiator: true,
})

var port = chrome.runtime.connect({})

port.onMessage.addListener(function(data) {
    if (data.type === 'signal') {
        peer.signal(data.data)
    }
})

peer.on('signal', data => {
    port.postMessage({ type: 'signal', data: data })
})

function send(data) {
    peer.write(
        JSON.stringify({
            type: 'relay',
            payload: data,
        })
    )
}

peer.on('connect', () => {
    console.log('connected')
})

let pageWidth = 0,
    pageHeight = 0

// let textSelection

peer.on('data', function(chunk) {
    let data = JSON.parse(chunk)
    if (data.type === 'resize') {
        pageWidth = data.width
        pageHeight = data.height
        updateViewport()
    } else if (data.type === 'update') {
        container.style.cursor = data.cursor
        // textSelection = data.selection

        // console.log(data)
    } else if (data.type === 'copy') {
        navigator.clipboard.writeText(data.text).then(() => {
            console.log('injected into clipbaord')
        })
    }
})

function throttle(fn) {
    let evt
    return function(...args) {
        if (evt) clearTimeout(evt)
        evt = setTimeout(() => fn(...args), 500)
    }
}

// function sendViewport() {
//     console.log('resizing')
//     send({
//         type: 'resize',
//         width: container.offsetWidth,
//         height: container.offsetHeight,
//         deviceScaleFactor: devicePixelRatio,
//     })

// }

function serializeMouseEvent(e) {
    const bb = container.getBoundingClientRect()

    const containerAspectRatio = container.offsetWidth / container.offsetHeight
    const pageAspectRatio = pageWidth / pageHeight

    const scale =
        containerAspectRatio > pageAspectRatio
            ? pageHeight / container.offsetHeight
            : pageWidth / container.offsetWidth

    return {
        clientX: (e.clientX - bb.x) * scale,
        clientY: (e.clientY - bb.y) * scale,

        shiftKey: e.shiftKey,
        metaKey: e.metaKey,
        altKey: e.altKey,
        ctrlKey: e.ctrlKey,

        button: e.button,
        buttons: e.buttons,

        detail: e.detail,
    }
}

document.addEventListener('copy', function(e) {
    console.log('request selection')
    send({ type: 'copy' })
    e.preventDefault()
})

document.addEventListener('paste', function(e) {
    let text = e.clipboardData.getData('text/plain')

    e.preventDefault()
})

container.onmousemove = e => {
    e.preventDefault()
    send({ type: 'mousemove', ...serializeMouseEvent(e) })
}

container.oncontextmenu = e => {
    e.preventDefault()
}

container.onmousedown = e => {
    e.preventDefault()
    send({ type: 'mousedown', ...serializeMouseEvent(e) })
}

container.onmouseup = e => {
    e.preventDefault()
    send({ type: 'mouseup', ...serializeMouseEvent(e) })
}

document.addEventListener(
    'wheel',
    e => {
        e.preventDefault()

        send({
            type: 'wheel',
            ...serializeMouseEvent(e),
            deltaX: e.deltaX,
            deltaY: e.deltaY,
            deltaZ: e.deltaZ,
            deltaMode: e.deltaMode,
        })
    },
    { passive: false }
)

// window.onkeydown = window.onkeyup = window.onkeypress = event => {
//     const eventTypes = { keydown: 'keyDown', keyup: 'keyUp', keypress: 'char' }
//     const text = event.type === 'keypress' ? String.fromCharCode(event.charCode) : undefined

//     send({
//         type: 'keyboard',
//         eventType: eventTypes[event.type],
//         modifiers:
//             (event.altKey ? 1 : 0) |
//             (event.ctrlKey ? 2 : 0) |
//             (event.metaKey ? 4 : 0) |
//             (event.shiftKey ? 8 : 0),
//         text: text,
//         unmodifiedText: text ? text.toLowerCase() : undefined,
//         keyIdentifier: event.keyIdentifier,
//         code: event.code,
//         key: event.key,
//         windowsVirtualKeyCode: event.keyCode,
//         nativeVirtualKeyCode: event.keyCode,
//         autoRepeat: false,
//         isKeypad: false,
//         isSystemKey: false,
//     })
// }

peer.on('stream', stream => {
    if ('srcObject' in monitor) {
        monitor.srcObject = stream
    } else {
        monitor.src = window.URL.createObjectURL(stream) // for older browsers
    }
    monitor.play()
})

monitor.addEventListener('loadedmetadata', event => {
    updateViewport()
})

window.onresize = throttle(() => updateViewport())

function updateViewport() {
    if (pageWidth === 0 || pageHeight === 0) return
    if (monitor.videoWidth === 0 || monitor.videoHeight === 0) return

    const containerAspectRatio = container.offsetWidth / container.offsetHeight
    const videoAspectRatio = monitor.videoWidth / monitor.videoHeight
    const pageAspectRatio = pageWidth / pageHeight
    const videoScale = pageAspectRatio / videoAspectRatio

    let horizontalScale = videoAspectRatio > pageAspectRatio ? 1 / videoScale : 1
    let verticalScale = videoAspectRatio > pageAspectRatio ? 1 : videoScale

    if (containerAspectRatio > pageAspectRatio) {
        // fill the page height
        monitor.style.height = Math.round(verticalScale * container.offsetHeight) + 'px'
        monitor.style.width = 'auto'
    } else {
        // fill the page width
        monitor.style.width = Math.round(horizontalScale * container.offsetWidth) + 'px'
        monitor.style.height = 'auto'
    }

    monitor.style.marginTop =
        Math.round(Math.min(0, ((1 / videoScale - 1) * monitor.offsetHeight) / 2)) + 'px'

    monitor.style.marginLeft =
        Math.round(Math.min(0, ((videoScale - 1) * monitor.offsetWidth) / 2)) + 'px'
}
