# DOM Events to simulate

Focus events

-   focus
-   blur
-   focusin
-   focusout

Form events

-   reset
-   submit

Text composition

-   compositionstart
-   compositionupdate
-   compositionend

View events

-   scroll

Clipboard events

-   cut
-   copy
-   paste

Keyboard events

-   keydown
-   keypress
-   keyup

Mouse events

-   auxclick
-   click
-   contextmenu
-   dblclick
-   mousedown
-   mouseenter
-   mouseleave
-   mousemove
-   mouseover
-   mouseout
-   mouseup
-   select

-   wheel
-   mousewheel
-   DOMMouseScroll

Drag and drop

-   drag
-   dragend
-   dragenter
-   dragstart
-   dragleave
-   dragover
-   drop

Pointer events

-   pointerover
-   pointerenter
-   pointerdown
-   pointermove
-   pointerup
-   pointercancel
-   pointerout
-   pointerleave

Value change events

-   input
-   change

# Cursor

This is relatively easy, we can just forward over the `getComputedStyle` of `cursor` of the
currently active element.

# Clipboard

We should constantly send over the text which has been selected.

# Keyboard events

1. keydown
2. beforeinput
3. keypress
4. input
5. keyup

`keydown`, `beforeinput`, `input` repeat when the key is held down on certain platforms.

The target is the focused element if anything is focused, otherwise it is the body if available, and
otherwise the root element.

https://www.w3.org/TR/uievents/#events-keyboard-event-order

# Mouse events

This is tricky because we essentially only get mousemoves and have to simulate all the auxilary
events on elements as appropriate.

1. mousemove
2. mouseover
3. mouseenter
4. mousemove
5. mouseout
6. mouseleave

# Clicks

We also have to deal with text selection, which starts with a `mousedown` and continues until a
`mouseup`.

To a certain extent, we can just capture all of these events and forward them over. The only caveat
is that we have to remember the sequence of events because if an event handler cancels one of them,
we need to cancel the rest of the sequence.

1. mousedown
2. contextmenu
3. mouseup
4. click

5. mousedown
6. mouseup
7. click
8. dblclick

# Goals

We just want this to work on "most" web applications. Hopefully that's not too ridiculously
difficult.

-   Google Docs
-   Google Sheets
-   Figma
-   Onshape
-   EasyEDA
-   Asana
-   Slack
-   Facebook

# Google Docs

Google docs uses an iframe to handle all key events. If `document.activeElement` is an `iframe` then
we should recurse down to that iframe's `contentDocument` and then create a key event for its
`activeElement`.

If there is a site that uses cross-domain iframes then we might have to worry about communicating
between content scripts to handle this.
