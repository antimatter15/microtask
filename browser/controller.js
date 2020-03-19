if (typeof onDispose !== 'undefined') onDispose()
if (typeof port !== 'undefined') port.disconnect()

var port = chrome.runtime.connect({})

port.onMessage.addListener(function(data) {
    onMessage(data)
})

port.onDisconnect.addListener(function() {
    onDispose()
})

// var nubbin = document.createElement('div')
// nubbin.style.position = 'fixed'
// nubbin.style.background = 'green'
// nubbin.style.width = '30px'
// nubbin.style.height = '30px'
// nubbin.style.borderRadius = '30px'
// nubbin.style.zIndex = '99999999999'
// document.body.appendChild(nubbin)

function send(data) {
    port.postMessage({
        type: 'relay',
        payload: data,
    })
}

// let currentState = {
//     cursor: 'default'
// }

// let mouseDownElement
let mouseDownPosition
let clickCount = 1
let lastClickTime = 0
let textSelectionRangeStart

function sendUpdate(el, data) {
    let cursor
    if (el && el !== window) {
        let computedElementStyles = window.getComputedStyle(el)
        let cursorValue = computedElementStyles.getPropertyValue('cursor')
        let cursorTextRange = getRangeAtPoint(el, data.clientX, data.clientY)
        cursor = cursorValue === 'auto' && cursorTextRange ? 'text' : cursorValue
    }

    send({
        type: 'update',
        cursor: cursor,
        // selection: ,
    })
}

function throttle(fn, delay = 500) {
    let evt
    return function(...args) {
        if (evt) clearTimeout(evt)
        evt = setTimeout(() => fn(...args), delay)
    }
}

let sendThrottledUpdate = throttle(sendUpdate, 10)

setInterval(() => {
    simulateFocusStyles()
}, 100)

function onMessage(data) {
    if (data.type === 'mousemove') {
        let el = document.elementFromPoint(data.clientX, data.clientY)

        simulateMouseHoverStyles(el)
        simulateFocusStyles()

        sendThrottledUpdate(el, data)
        // TODO: mouseover, mouseout, mouseenter, mouseleave

        // https://stackoverflow.com/a/18730705/205784

        if (textSelectionRangeStart) {
            let range = getRangeAtPoint(el, data.clientX, data.clientY)
            if (range) {
                let sel = document.getSelection()
                sel.removeAllRanges()

                sel.setBaseAndExtent(
                    textSelectionRangeStart.startContainer,
                    textSelectionRangeStart.startOffset,
                    range.startContainer,
                    range.startOffset
                )
            }
        }
    } else if (data.type === 'wheel') {
        let el = document.elementFromPoint(data.clientX, data.clientY)

        // TODO: emit mousewheel event as well
        // https://developer.mozilla.org/en-US/docs/Web/API/Element/mousewheel_event
        let wheelEvent = new WheelEvent('wheel', {
            // EventInit https://developer.mozilla.org/en-US/docs/Web/API/Event/Event
            bubbles: true,
            cancelable: true,
            composed: false,

            // UIEvent: https://developer.mozilla.org/en-US/docs/Web/API/UIEvent/UIEvent
            view: el.ownerDocument.defaultView,
            detail: data.detail,

            // MouseEvent: https://developer.mozilla.org/en-US/docs/Web/API/MouseEvent/MouseEvent
            screenX: 100 + data.clientX,
            screenY: 100 + data.clientY,

            clientX: data.clientX,
            clientY: data.clientY,

            ctrlKey: data.ctrlKey,
            shiftKey: data.shiftKey,
            altKey: data.altKey,
            metaKey: data.metaKey,

            button: data.button,
            buttons: data.buttons,
            relatedTarget: null,

            // WheelEvent: https://developer.mozilla.org/en-US/docs/Web/API/WheelEvent/WheelEvent
            deltaX: data.deltaX,
            deltaY: data.deltaY,
            deltaZ: data.deltaZ,
            deltaMode: data.deltaMode,
        })

        if (el.dispatchEvent(wheelEvent)) {
            // event wasnt canceled lets do the default action

            // data.deltaY

            // let cur = el
            // while (cur) {
            //     if (data.deltaY > 0) {
            //         if (cur.scrollTop + cur.offsetHeight < cur.scrollHeight) {
            //             let oldScrollTop = cur.scrollTop
            //             cur.scrollTop += data.deltaY
            //             if (cur.scrollTop != oldScrollTop) break
            //         }
            //     } else {
            //         if (cur.scrollTop > 0) {
            //             let oldScrollTop = cur.scrollTop
            //             cur.scrollTop += data.deltaY
            //             if (cur.scrollTop != oldScrollTop) break
            //         }
            //     }

            //     if (cur === document.documentElement) break

            //     cur = cur.offsetParent

            //     if (!cur) cur = document.documentElement
            // }

            document.documentElement.scrollTop += data.deltaY
            document.documentElement.scrollLeft += data.deltaX
        }
    } else if (data.type === 'mousedown') {
        let el = document.elementFromPoint(data.clientX, data.clientY)

        let mouseDownEvent = new MouseEvent('mousedown', {
            // EventInit https://developer.mozilla.org/en-US/docs/Web/API/Event/Event
            bubbles: true,
            cancelable: true,
            composed: false,

            // UIEvent: https://developer.mozilla.org/en-US/docs/Web/API/UIEvent/UIEvent
            view: el.ownerDocument.defaultView,
            detail: data.detail,

            // MouseEvent: https://developer.mozilla.org/en-US/docs/Web/API/MouseEvent/MouseEvent
            screenX: 100 + data.clientX,
            screenY: 100 + data.clientY,

            clientX: data.clientX,
            clientY: data.clientY,

            ctrlKey: data.ctrlKey,
            shiftKey: data.shiftKey,
            altKey: data.altKey,
            metaKey: data.metaKey,

            button: data.button,
            buttons: data.buttons,
            relatedTarget: null,
        })

        // mouseDownElement = null
        mouseDownPosition = null
        if (el.dispatchEvent(mouseDownEvent)) {
            // mouseDownElement = el
            mouseDownPosition = [mouseDownEvent.clientX, mouseDownEvent.clientY]

            document.activeElement.blur()
            el.focus()
        }

        textSelectionRangeStart = getRangeAtPoint(el, data.clientX, data.clientY)
        // let sel = document.getSelection()
        // sel.removeAllRanges()
        simulateFocusStyles()
    } else if (data.type === 'mouseup') {
        let el = document.elementFromPoint(data.clientX, data.clientY)

        if (textSelectionRangeStart) {
            let range = getRangeAtPoint(el, data.clientX, data.clientY)
            if (range) {
                let sel = document.getSelection()
                sel.removeAllRanges()

                sel.setBaseAndExtent(
                    textSelectionRangeStart.startContainer,
                    textSelectionRangeStart.startOffset,
                    range.startContainer,
                    range.startOffset
                )
            }
        }
        textSelectionRangeStart = null
        if (Date.now() - lastClickTime > 500) clickCount = 0
        clickCount++
        lastClickTime = Date.now()

        let eventArgs = {
            // EventInit https://developer.mozilla.org/en-US/docs/Web/API/Event/Event
            bubbles: true,
            cancelable: true,
            composed: false,

            // UIEvent: https://developer.mozilla.org/en-US/docs/Web/API/UIEvent/UIEvent
            view: el.ownerDocument.defaultView,
            detail: clickCount,

            // MouseEvent: https://developer.mozilla.org/en-US/docs/Web/API/MouseEvent/MouseEvent
            screenX: 100 + data.clientX,
            screenY: 100 + data.clientY,

            clientX: data.clientX,
            clientY: data.clientY,

            ctrlKey: data.ctrlKey,
            shiftKey: data.shiftKey,
            altKey: data.altKey,
            metaKey: data.metaKey,

            button: data.button,
            buttons: data.buttons,
            relatedTarget: null,
        }
        let mouseUpEvent = new MouseEvent('mouseup', eventArgs)
        if (!el.dispatchEvent(mouseUpEvent)) {
            // mouseUp was cancelled
        }

        // not a click if different element than mousedown
        if (
            !(
                mouseDownPosition &&
                Math.abs(mouseUpEvent.clientX - mouseDownPosition[0]) < 5 &&
                Math.abs(mouseUpEvent.clientY - mouseDownPosition[1]) < 5
            )
        ) {
            lastClickTime = 0
            return
        }

        if (eventArgs.detail === 2) {
            // select word
            let range = getRangeAtPoint(el, data.clientX, data.clientY)
            if (range) {
                let sel = document.getSelection()
                sel.removeAllRanges()
                sel.addRange(range)
                console.log('range', range)

                sel.modify('move', 'backward', 'word')
                sel.modify('extend', 'forward', 'word')
            }
        } else if (eventArgs.detail == 3) {
            // select paragraph
            let range = getRangeAtPoint(el, data.clientX, data.clientY)
            if (range) {
                let sel = document.getSelection()
                sel.removeAllRanges()
                sel.addRange(range)
                sel.modify('extend', 'forward', 'paragraphboundary')
                sel.modify('extend', 'backward', 'paragraphboundary')
            }
        }

        let clickEvent = new MouseEvent('click', eventArgs)
        if (el.dispatchEvent(clickEvent)) {
        }

        if (eventArgs.detail === 2) {
            let dblClickEvent = new MouseEvent('dblclick', eventArgs)
            if (el.dispatchEvent(dblClickEvent)) {
                // double click was cancelled
            }
        }
        simulateFocusStyles()
        sendThrottledUpdate(el, data)
    } else if (data.type === 'copy') {
        send({ type: 'copy', text: window.getSelection().toString() })
    } else if (data.type === 'keydown') {
        let el = document.activeElement || document.body
        while (el.tagName === 'IFRAME') {
            el = el.contentDocument.activeElement
        }

        console.log(el)
        let eventArgs = {
            // EventInit https://developer.mozilla.org/en-US/docs/Web/API/Event/Event
            bubbles: true,
            cancelable: true,
            composed: false,

            // UIEvent: https://developer.mozilla.org/en-US/docs/Web/API/UIEvent/UIEvent
            view: el.ownerDocument.defaultView,
            detail: data.detail,

            // KeyboardEvent: https://developer.mozilla.org/en-US/docs/Web/API/KeyboardEvent/KeyboardEvent
            key: data.key,
            code: data.code,
            location: data.location,
            ctrlKey: data.ctrlKey,
            shiftKey: data.shiftKey,
            altKey: data.altKey,
            metaKey: data.metaKey,
            repeat: data.repeat,
            keyCode: data.keyCode,
            detail: data.detail,
            charCode: data.charCode,
            which: data.which,
            isComposing: data.isComposing,
        }

        let keyDownEvent = new KeyboardEvent('keydown', eventArgs)
        if (!el.dispatchEvent(keyDownEvent)) {
            // keydown was cancelled
        }

        let beforeInputEvent = new KeyboardEvent('beforeinput', eventArgs)
        if (!el.dispatchEvent(beforeInputEvent)) {
            // keydown was cancelled
        }

        // TODO: change keyCode to the ascii lowercase/uppercase version
        // also filter out modifier keys:
        // https://developer.mozilla.org/en-US/docs/Web/API/Document/keypress_event

        let inputEvent = new KeyboardEvent('input', eventArgs)
        if (!el.dispatchEvent(inputEvent)) {
            // keydown was cancelled
        }
    } else if (data.type === 'keypress') {
        let el = document.activeElement || document.body
        while (el.tagName === 'IFRAME') {
            el = el.contentDocument.activeElement
        }

        console.log(el)
        let eventArgs = {
            // EventInit https://developer.mozilla.org/en-US/docs/Web/API/Event/Event
            bubbles: true,
            cancelable: true,
            composed: false,

            // UIEvent: https://developer.mozilla.org/en-US/docs/Web/API/UIEvent/UIEvent
            view: el.ownerDocument.defaultView,
            detail: data.detail,

            // KeyboardEvent: https://developer.mozilla.org/en-US/docs/Web/API/KeyboardEvent/KeyboardEvent
            key: data.key,
            code: data.code,
            location: data.location,
            ctrlKey: data.ctrlKey,
            shiftKey: data.shiftKey,
            altKey: data.altKey,
            metaKey: data.metaKey,
            repeat: data.repeat,
            keyCode: data.keyCode,
            detail: data.detail,
            charCode: data.charCode,
            which: data.which,
            isComposing: data.isComposing,
        }

        let keyPressEvent = new KeyboardEvent('keypress', eventArgs)
        if (!el.dispatchEvent(keyPressEvent)) {
            // keydown was cancelled
        }
    }
}

// https://stackoverflow.com/a/18730705/205784

function onResize() {
    send({
        type: 'resize',
        width: innerWidth,
        height: innerHeight,
    })
}

window.addEventListener('resize', onResize)
onResize()

function onDispose() {
    window.removeEventListener('resize', onResize)
    // document.body.removeChild(nubbin)
}

// function setFavicon(url) {
//     // https://stackoverflow.com/a/260876/205784
//     var link = document.createElement('link')
//     link.rel = 'shortcut icon'
//     link.href = url
//     document.getElementsByTagName('head')[0].appendChild(link)
// }

// setFavicon(chrome.extension.getURL('icon.png'))

function getAncestors(el) {
    let parents = []
    while (el) {
        parents.push(el)
        el = el.parentNode
    }
    return parents
}

function cssPathToElement(el) {
    var names = []
    while (el.parentNode) {
        if (el.id && /^\w*[a-z]\w*$/.test(el.id)) {
            names.unshift('#' + el.id)
            break
        } else {
            if (el == el.ownerDocument.documentElement) names.unshift(el.tagName)
            else {
                for (
                    var c = 1, e = el;
                    e.previousElementSibling;
                    e = e.previousElementSibling, c++
                );
                names.unshift(el.tagName + ':nth-child(' + c + ')')
            }
            el = el.parentNode
        }
    }
    return names.join(' > ')
}

var focusInjector = document.createElement('style')
document.head.appendChild(focusInjector)
var focusInjectorSheet = focusInjector.sheet

function simulateFocusStyles() {
    while (focusInjectorSheet.cssRules.length > 0) {
        focusInjectorSheet.deleteRule(0)
    }

    if (document.activeElement && document.activeElement.tabIndex > -1) {
        focusInjectorSheet.addRule(
            cssPathToElement(document.activeElement),
            'outline: 2px solid #629cf4',
            0
        )
    }
}

var mouseHoverInjector = document.createElement('style')
document.head.appendChild(mouseHoverInjector)
var injectorSheet = mouseHoverInjector.sheet

function simulateMouseHoverStyles(el) {
    let ancestors = getAncestors(el)

    while (injectorSheet.cssRules.length > 0) {
        injectorSheet.deleteRule(0)
    }

    for (let ss of document.styleSheets) {
        let rules
        try {
            rules = ss.cssRules
        } catch (err) {
            continue
        }
        for (let rule of rules) {
            if (!rule.selectorText || !rule.cssText) continue
            if (rule.selectorText.includes(':hover')) {
                let modifiedSelector = rule.selectorText.replace(/:hover/g, '')
                for (let anc of ancestors) {
                    if (anc && anc.matches && anc.matches(modifiedSelector)) {
                        injectorSheet.addRule(cssPathToElement(anc), rule.style.cssText, 0)
                    }
                }
            }
        }
    }
}

function getRangeAtPoint(elem, x, y) {
    if (elem.nodeType == elem.TEXT_NODE) {
        var range = elem.ownerDocument.createRange()
        range.selectNodeContents(elem)
        var currentPos = 0
        var endPos = range.endOffset
        while (currentPos + 1 < endPos) {
            range.setStart(elem, currentPos)
            range.setEnd(elem, currentPos + 1)
            let bb = range.getBoundingClientRect()
            if (bb.left <= x && bb.right >= x && bb.top <= y && bb.bottom >= y) {
                return range
            }
            currentPos += 1
        }
    } else {
        for (var i = 0; i < elem.childNodes.length; i++) {
            var range = elem.childNodes[i].ownerDocument.createRange()
            range.selectNodeContents(elem.childNodes[i])
            let bb = range.getBoundingClientRect()
            if (bb.left <= x && bb.right >= x && bb.top <= y && bb.bottom >= y) {
                let rp = getRangeAtPoint(elem.childNodes[i], x, y)
                if (rp) return rp
            }
        }
    }
    return null
}
