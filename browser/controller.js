// chrome.runtime.sendMessage({ greeting: 'hello' }, function(response) {
//     console.log(response.farewell)
// })

chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
    console.log(sender.tab ? 'from a content script:' + sender.tab.url : 'from the extension')
    // if (request.greeting == 'hello') sendResponse({ farewell: 'goodbye' })
})

// function setFavicon(url) {
//     // https://stackoverflow.com/a/260876/205784
//     var link = document.createElement('link')
//     link.rel = 'shortcut icon'
//     link.href = url
//     document.getElementsByTagName('head')[0].appendChild(link)
// }

// setFavicon(chrome.extension.getURL('icon.png'))
