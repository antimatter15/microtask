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
        // caret: caret,
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

        if (typeof textSelectionRangeStart === 'number') {
            if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
                let caret = getCaretFromCoordinates(el, data.clientX, data.clientY)

                el.selectionStart = Math.min(caret, textSelectionRangeStart)
                el.selectionEnd = Math.max(caret, textSelectionRangeStart)
                el.selectionDirection = caret > textSelectionRangeStart ? 'forward' : 'backward'
            }
        } else if (textSelectionRangeStart) {
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

        if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
            computeCoordinateCache(el)
            textSelectionRangeStart = getCaretFromCoordinates(el, data.clientX, data.clientY)
            el.selectionStart = textSelectionRangeStart
            el.selectionEnd = textSelectionRangeStart
        } else {
            textSelectionRangeStart = getRangeAtPoint(el, data.clientX, data.clientY)
        }

        // let sel = document.getSelection()
        // sel.removeAllRanges()
        simulateFocusStyles()
    } else if (data.type === 'mouseup') {
        let el = document.elementFromPoint(data.clientX, data.clientY)

        if (typeof textSelectionRangeStart === 'number') {
            // textSelectionRangeStart
        } else if (textSelectionRangeStart) {
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

var virtualCaret = document.createElement('div')
virtualCaret.style.position = 'fixed'
virtualCaret.style.width = '1px'
virtualCaret.style.background = 'black'
virtualCaret.style.display = 'none'
document.body.appendChild(virtualCaret)

function simulateFocusStyles() {
    while (focusInjectorSheet.cssRules.length > 0) {
        focusInjectorSheet.deleteRule(0)
    }

    let active = document.activeElement

    virtualCaret.style.display = 'none'

    if (active && active.tabIndex > -1) {
        focusInjectorSheet.addRule(cssPathToElement(active), 'outline: 2px solid #629cf4', 0)

        if (active.tagName === 'INPUT' || active.tagName === 'TEXTAREA') {
            if (active.selectionStart === active.selectionEnd) {
                let bb = active.getBoundingClientRect()
                let caret = getCaretCoordinates(active, active.selectionStart)

                virtualCaret.style.left = bb.left + caret.left + 'px'
                virtualCaret.style.top = bb.top + caret.top + 'px'
                virtualCaret.style.height = caret.height + 'px'
                virtualCaret.style.display = 'block'
            }
        }
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

// We'll copy the properties below into the mirror div.
// Note that some browsers, such as Firefox, do not concatenate properties
// into their shorthand (e.g. padding-top, padding-bottom etc. -> padding),
// so we have to list every single property explicitly.
var textInputProperties = [
    'direction', // RTL support
    'boxSizing',
    'width', // on Chrome and IE, exclude the scrollbar, so the mirror div wraps exactly as the textarea does
    'height',
    'overflowX',
    'overflowY', // copy the scrollbar for IE

    'borderTopWidth',
    'borderRightWidth',
    'borderBottomWidth',
    'borderLeftWidth',
    'borderStyle',

    'paddingTop',
    'paddingRight',
    'paddingBottom',
    'paddingLeft',

    // https://developer.mozilla.org/en-US/docs/Web/CSS/font
    'fontStyle',
    'fontVariant',
    'fontWeight',
    'fontStretch',
    'fontSize',
    'fontSizeAdjust',
    'lineHeight',
    'fontFamily',

    'textAlign',
    'textTransform',
    'textIndent',
    'textDecoration', // might not make a difference, but better be safe

    'letterSpacing',
    'wordSpacing',

    'tabSize',
    'MozTabSize',
]

// var isBrowser = typeof window !== 'undefined'
// var isFirefox =

let caretCoordinateCache = null
function computeCoordinateCache(element) {
    let cache = []
    console.time('computeCoordinateCache')
    let bb = element.getBoundingClientRect()
    for (let i = 0; i < element.value.length; i++) {
        let res = getCaretCoordinates(element, i)
        cache.push({
            x: bb.left + res.left,
            y: bb.top + res.top + res.height / 2,
        })
    }
    console.timeEnd('computeCoordinateCache')
    caretCoordinateCache = cache
}

function getCaretFromCoordinates(element, clientX, clientY) {
    function test(pos) {
        let res = caretCoordinateCache[pos]
        return Math.sqrt((res.x - clientX) ** 2 + (res.y - clientY) ** 2)
    }

    let minDistance = test(0),
        minPos = 0
    for (let i = 1; i < caretCoordinateCache.length; i++) {
        let dist = test(i)
        if (dist < minDistance) {
            minPos = i
            minDistance = dist
        }
    }
    return minPos
}

function getCaretCoordinates(element, position, options) {
    // if (!isBrowser) {
    //     throw new Error(
    //         'textarea-caret-position#getCaretCoordinates should only be called in a browser'
    //     )
    // }

    var debug = (options && options.debug) || false
    if (debug) {
        var el = document.querySelector('#input-textarea-caret-position-mirror-div')
        if (el) el.parentNode.removeChild(el)
    }

    // The mirror div will replicate the textarea's style
    var div = document.createElement('div')
    div.id = 'input-textarea-caret-position-mirror-div'
    document.body.appendChild(div)

    var style = div.style
    var computed = window.getComputedStyle ? window.getComputedStyle(element) : element.currentStyle // currentStyle for IE < 9
    var isInput = element.nodeName === 'INPUT'

    // Default textarea styles
    style.whiteSpace = 'pre-wrap'
    if (!isInput) style.wordWrap = 'break-word' // only for textarea-s

    // Position off-screen
    style.position = 'absolute' // required to return coordinates properly
    if (!debug) style.visibility = 'hidden' // not 'display: none' because we want rendering

    // Transfer the element's properties to the div
    textInputProperties.forEach(function(prop) {
        if (isInput && prop === 'lineHeight') {
            // Special case for <input>s because text is rendered centered and line height may be != height
            if (computed.boxSizing === 'border-box') {
                var height = parseInt(computed.height)
                var outerHeight =
                    parseInt(computed.paddingTop) +
                    parseInt(computed.paddingBottom) +
                    parseInt(computed.borderTopWidth) +
                    parseInt(computed.borderBottomWidth)
                var targetHeight = outerHeight + parseInt(computed.lineHeight)
                if (height > targetHeight) {
                    style.lineHeight = height - outerHeight + 'px'
                } else if (height === targetHeight) {
                    style.lineHeight = computed.lineHeight
                } else {
                    style.lineHeight = 0
                }
            } else {
                style.lineHeight = computed.height
            }
        } else {
            style[prop] = computed[prop]
        }
    })

    if (window.mozInnerScreenX != null) {
        // Firefox lies about the overflow property for textareas: https://bugzilla.mozilla.org/show_bug.cgi?id=984275
        if (element.scrollHeight > parseInt(computed.height)) style.overflowY = 'scroll'
    } else {
        style.overflow = 'hidden' // for Chrome to not render a scrollbar; IE keeps overflowY = 'scroll'
    }

    div.textContent = element.value.substring(0, position)
    // The second special handling for input type="text" vs textarea:
    // spaces need to be replaced with non-breaking spaces - http://stackoverflow.com/a/13402035/1269037
    if (isInput) div.textContent = div.textContent.replace(/\s/g, '\u00a0')

    var span = document.createElement('span')

    span.style.all = 'unset' // make sure everything is applied from the div, not from CSS selectors, not cross browser compatible :(
    span.style.lineHeight = '1em' // set the line-height relative to the div

    // Wrapping must be replicated *exactly*, including when a long word gets
    // onto the next line, with whitespace at the end of the line before (#7).
    // The  *only* reliable way to do that is to copy the *entire* rest of the
    // textarea's content into the <span> created at the caret position.
    // For inputs, just '.' would be enough, but no need to bother.
    span.textContent = element.value.substring(position) || '.' // || because a completely empty faux span doesn't render at all
    div.appendChild(span)

    var coordinates = {
        top: span.offsetTop + parseInt(computed['borderTopWidth']),
        left: span.offsetLeft + parseInt(computed['borderLeftWidth']),
        // height: parseInt(computed['lineHeight']),
        height: parseInt(getComputedStyle(span).lineHeight), // get the pixelated line-height even if it is "normal"
    }

    if (debug) {
        span.style.backgroundColor = '#aaa'
    } else {
        document.body.removeChild(div)
    }

    return coordinates
}
