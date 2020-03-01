if (typeof onDispose !== 'undefined') onDispose()
if (typeof port !== 'undefined') port.disconnect()

var port = chrome.runtime.connect({})

port.onMessage.addListener(function(data) {
    onMessage(data)
})

port.onDisconnect.addListener(function() {
    onDispose()
})

var nubbin = document.createElement('div')
nubbin.style.position = 'fixed'
nubbin.style.background = 'green'
nubbin.style.width = '30px'
nubbin.style.height = '30px'
nubbin.style.borderRadius = '30px'
nubbin.style.zIndex = '99999999999'
document.body.appendChild(nubbin)

var style = document.createElement('style')
document.head.appendChild(style)
var sheet = style.sheet

function send(data) {
    port.postMessage({
        type: 'relay',
        payload: data,
    })
}

function getAncestors(el) {
    let parents = []
    while (el) {
        parents.push(el)
        el = el.parentNode
    }
    return parents
}

function cssPath(el) {
    var names = []
    while (el.parentNode) {
        if (el.id) {
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

function simulateMouseHover(el) {
    let ancestors = getAncestors(el)

    while (sheet.cssRules.length > 0) {
        sheet.deleteRule(0)
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
                        sheet.addRule(cssPath(anc), rule.style.cssText, 0)
                    }
                }
            }
        }
    }
}

function onMessage(data) {
    if (data.type === 'mouse') {
        // nubbin.style.left = data.x + 'px'
        // nubbin.style.top = data.y + 'px'

        let el = document.elementFromPoint(data.x, data.y)

        simulateMouseHover(el)

        if (data.eventType === 'mouseReleased') {
            syn.click(el, {
                clientX: data.x,
                clientY: data.y,
            })
        }
    } else if (data.type === 'keyboard' && data.eventType === 'keyUp') {
        let key = Object.keys(syn.keycodes).find(k => syn.keycodes[k] == data.nativeVirtualKeyCode)
        // console.log(key, data)
        if (key) {
            syn.key(document.activeElement, key)
        }
    }
}

function onResize() {
    send({
        type: 'resize',
        width: innerWidth,
        height: innerHeight,
    })
}

window.addEventListener('resize', onResize)
onResize()

var onDispose = function() {
    window.removeEventListener('resize', onResize)
    document.body.removeChild(nubbin)
}

// function setFavicon(url) {
//     // https://stackoverflow.com/a/260876/205784
//     var link = document.createElement('link')
//     link.rel = 'shortcut icon'
//     link.href = url
//     document.getElementsByTagName('head')[0].appendChild(link)
// }

// setFavicon(chrome.extension.getURL('icon.png'))
