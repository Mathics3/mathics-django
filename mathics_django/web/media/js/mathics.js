// TODO: getSelection function
// -*- mode: js; js-indent-level: 4; -*-


let deleting,
    blurredElement,
    movedItem,
    clickedQuery,
    lastFocus = null,
    welcome = true,
    queryIndex = 0,
    mouseDownEvent = null,
    timeout = -1;

function getLetterWidth(element) {
    const letter = document.createElement('span');
    letter.innerText = 'm';
    letter.style.fontFamily = element.style.fontFamily;
    letter.style.fontSize = element.style.fontSize;

    document.body.appendChild(letter);

    const width = letter.getWidth();

    document.body.removeChild(letter);

    return width;
}

function refreshInputSize(textarea) {
    const letterWidth = getLetterWidth(textarea),
          width = textarea.clientWidth,
          lines = textarea.value.split('\n');

    let lineCount = 0;

    lines.forEach((line) => {
        lineCount += Math.ceil((line.length + 1) * letterWidth / width);
    });

    textarea.rows = lineCount;
}

function refreshInputSizes() {
    document.querySelectorAll('textarea.request').forEach(
        (textarea) => refreshInputSize(textarea)
    );
}

function inputChange() {
    refreshInputSize(this);
}

function isEmpty(textarea) {
    return textarea.value.strip() == '' && !textarea.submitted;
}

function prepareText(text) {
    return text.replaceAll(" ", "&nbsp;");
}

function getDimensions(math, callback) {
    const all = document.getElementById('calc_all').cloneNode(true);
    all.id = null;

    document.body.appendChild(all);
    const container = all.querySelector('.calc_container');
    container.appendChild(translateDOMElement(math));

    MathJax.Hub.Queue(['Typeset', MathJax.Hub, container]);
    MathJax.Hub.Queue(() => {
        const containerOffsetLeft = container.offsetLeft,
              containerOffsetTop = container.offsetTop,
              nextOffsetLeft = all.querySelector('.calc_next').offsetLeft,
              belowOffsetTop = all.querySelector('.calc_below').offsetTop;

        const width = nextOffsetLeft - containerOffsetLeft + 4,
              height = belowOffsetTop - containerOffsetTop + 20;

        all.remove();

        callback(width, height);
    });
}

function createMathNode(nodeName) {
    if (['svg', 'g', 'rect', 'circle', 'polyline', 'polygon', 'path', 'ellipse', 'foreignObject'].include(nodeName)) {
        return document.createElementNS("http://www.w3.org/2000/svg", nodeName);
    }

    return document.createElement(nodeName);
}

let objectsPrefix = 'math_object_', objectsCount = 0, objects = {};

function translateDOMElement(element, svg) {
    if (element.nodeType === 3) {
        return document.createTextNode(element.nodeValue);
    }
    const nodeName = element.nodeName;

    let dom = null;

    if (nodeName !== 'meshgradient' && nodeName !== 'graphics3d') {
        dom = createMathNode(element.nodeName);

        for (let i = 0; i < element.attributes.length; i++) {
            const attr = element.attributes[i];

            if (attr.nodeName != 'ox' && attr.nodeName != 'oy') {
                dom.setAttribute(attr.nodeName, attr.nodeValue);
            }
        }
    }

    if (nodeName === 'foreignObject') {
        dom.setAttribute('width', svg.getAttribute('width'));
        dom.setAttribute('height', svg.getAttribute('height'));
        dom.setAttribute('style', dom.getAttribute('style') + '; text-align: left; padding-left: 2px; padding-right: 2px;');

        dom.setAttribute('ox', parseFloat(element.getAttribute('ox')));
        dom.setAttribute('oy', parseFloat(element.getAttribute('oy')));
    }

    if (nodeName === 'mo') {
        const op = element.firstChild.nodeValue;

        if (op === '[' ||
            op === ']' ||
            op === '{' ||
            op === '}' ||
            op === String.fromCharCode(12314) ||
            op === String.fromCharCode(12315)
           ) {
            dom.setAttribute('maxsize', '3');
        }
    }

    let object = null;

    if (nodeName === 'graphics3d') {
        const data = JSON.parse(element.getAttribute('data')),
              div = document.createElement('div');

        drawGraphics3d(div, data);

        dom = div;
    }

    if (nodeName === 'svg' || nodeName === 'graphics3d' || nodeName.toLowerCase() === 'img') {
        // create <mspace> that will contain the graphics
        object = createMathNode('mspace');

        let width, height;

        if (nodeName === 'svg' || nodeName.toLowerCase() === 'img') {
            width = dom.getAttribute('width');
            height = dom.getAttribute('height');

            if (!width.endsWith('px')) {
                width += 'px';
            }

            if (!height.endsWith('px')) {
                height += 'px';
            }
        } else {
            // TODO: calculate appropriate height and recalculate on every view change
            width = height = '400px';
        }

        object.setAttribute('width', width);
        object.setAttribute('height', height);
    }

    if (nodeName === 'svg') {
        svg = dom;
    }

    let rows = [[]];

    element.childNodes.forEach((child) => {
        if (child.nodeName == 'mspace' && child.getAttribute('linebreak') == 'newline') {
            rows.push([]);
        } else {
            rows[rows.length - 1].push(child);
        }
    });

function convertMathGlyphs(dom) {
    // convert mglyphs to their classic representation (<svg> or <img>), so the new mglyph logic does not make
    // anything worse in the classic Mathics frontend for now. In the long run, this code should vanish.

    var MML = "http://www.w3.org/1998/Math/MathML";
    var glyphs = dom.getElementsByTagName("mglyph");
    for (var i = 0; i < glyphs.length; i++) {
        var glyph = glyphs[i];
        var src = glyph.getAttribute('src');
        if (src.startsWith('NUNCAMENENCONTRARASdata:image/svg+xml;base64,')) {
            var svgText = atob(src.substring(src.indexOf(",") + 1));
            var mtable =document.createElementNS(MML, "mtable");
            mtable.innerHTML = '<mtr><mtd>' + svgText + '</mtd></mtr>';
            var svg = mtable.getElementsByTagNameNS("*", "svg")[0];
            svg.setAttribute('width', glyph.getAttribute('width'));
            svg.setAttribute('height', glyph.getAttribute('height'));
            glyph.parentNode.replaceChild(mtable, glyph);
        } else if (src.startsWith('data:image/')) {
            var img = document.createElement('img');
            img.setAttribute('src', src)
            img.setAttribute('width', glyph.getAttribute('width'));
            img.setAttribute('height', glyph.getAttribute('height'));
            img.setAttribute('style', 'position:absolute; top:50%;');
            glyph.parentNode.replaceChild(img, glyph);
        }
    } else {
        rows[0].forEach(
            (element) => childParent.appendChild(
                translateDOMElement(element, svg)
            )
        );
    }

    if (object) {
        const id = objectsCount++;

        object.setAttribute('id', objectsPrefix + id);
        objects[id] = dom;

        return object;
    }

    return dom;
}

function createLine(value) {
    const container = document.createElement('div');
    container.innerHTML = value;
    if (container?.firstElementChild?.tagName === 'math') {
        return translateDOMElement(container.firstChild);
    } else if (container?.firstElementChild?.tagName === 'GRAPHICS3D') {
        const div = document.createElement('div');
	var json_data_value = JSON.parse(container.firstElementChild.attributes.data.value);
	div.style.backgroundColor = json_data_value["background_color"];
	if ("tooltip_text" in json_data_value){
	    div.title = json_data_value["tooltip_text"];
	}
        drawGraphics3d(div, json_data_value);

        div.style.overflow = 'hidden';
        div.style.position = 'relative';
        div.style.margin = 'auto';

        return div;
    } else if (container?.firstElementChild?.tagName === 'svg') {
        container.firstElementChild.style.display = 'block';
        container.firstElementChild.style.width = '100%';
        container.firstElementChild.style.maxWidth = '400px';
        container.firstElementChild.style.margin = 'auto';

        return container;
    } else {
        const lines = container.innerText.split('\n');
        const p = document.createElement('p');
        p.className = 'string';
	if(lines.length>1){
	    p.style.textAlign = 'justify';
	}

        for (let i = 0; i < lines.length; i++) {
	    newline = prepareText(lines[i]);
            p.innerHTML += newline;

            if (i < lines.length - 1) {
                p.appendChild(document.createElement('br'));
            }
        }
        return p;
    }
}

function afterProcessResult(list, command) {
    // command is either 'Typeset' (default) or 'Rerender'
    command ||= 'Typeset';

    MathJax.Hub.Queue([command, MathJax.Hub, list]);
    MathJax.Hub.Queue(() => {
        // inject SVG and other non-MathML objects into corresponding <mspace>s
        list.querySelectorAll('.mspace').forEach((mspace) => {
            const id = mspace.getAttribute('id').substr(objectsPrefix.length);

            mspace.appendChild(objects[id]);
        });
    });

    if (!MathJax.Hub.Browser.isOpera) {
        // Opera 11.01 Build 1190 on Mac OS X 10.5.8 crashes on this call for Plot[x,{x,0,1}]
        // => leave inner MathML untouched
        MathJax.Hub.Queue(['Typeset', MathJax.Hub, list]);
    }

    MathJax.Hub.Queue(() => {
        list.querySelectorAll('foreignObject > span > nobr > span.math')
            .forEach((math) => {
                const content = math.firstChild.firstChild.firstChild;

                math.removeChild(math.firstChild);
                math.insertBefore(content, math.firstChild);

                if (command === 'Typeset') {
                    // recalculate positions of insets based on ox/oy properties
                    const foreignObject = math.parentNode.parentNode.parentNode,
                          dimensions = math.getDimensions();

                    const ox = parseFloat(foreignObject.getAttribute('ox')),
                          oy = parseFloat(foreignObject.getAttribute('oy')),
                          width = dimensions.width + 4,
                          height = dimensions.height + 4;

                    let x = parseFloat(foreignObject.getAttribute('x').substr()),
                        y = parseFloat(foreignObject.getAttribute('y'));

                    x = x - width / 2.0 - ox * width / 2.0;
                    y = y - height / 2.0 + oy * height / 2.0;

                    foreignObject.setAttribute('x', x + 'px');
                    foreignObject.setAttribute('y', y + 'px');
                }
            });
    });
}

function setResult(list, results) {
    // Formats Django cell "results" and add that onto "list".

    const resultList = document.createElement('ul');
    resultList.className = 'out';

    resultList.style.display = 'none';

    const li = document.createElement('li');
    li.className = 'out';

    let format = null;
    let first_out = null;
    let result = null;
    let out = null;
    if (results.length == 1) {
        result = results[0];
        if ("form" in result) {
            format = result.form;
        }
        if ("out" in result) {
            out = result.out;
            if (out.length > 0) {
                first_out = out[0];
            }
        }
    }
    if (format == "Syntax Error") {

        /*
          Handle a Syntax error.

          FIXME: turn this function. It is used for other messages as well
        */

        // Create and populate message's classification part...
        const bold = document.createElement('b');
        bold.className = "message"
        bold.innerText = first_out.prefix
        resultList.appendChild(bold);


        // Create and populate warning or error message...
        const p = document.createElement('p');
        p.innerText = first_out.text;

        // Add warnning or error message to a list element in a block (which is CSS styled with a nice
        // frame around it).
        resultList.appendChild(p);
        resultList.style.display = 'block';
        li.appendChild(resultList);
        list.appendChild(li);

    } else if (format == "Python Exception") {

        /* Format a Python Exception. DRY with Syntax error.
           Note that here, first_out.text is an Array of traceback lines.
        */
        // Create and populate the message classification part.
        const bold = document.createElement('b');
        bold.className = "message";

        bold.innerText = first_out.prefix + ": " + first_out.text[0];
        resultList.appendChild(bold);

        // Now add Traceback lines. Start at index 1.

        // FIXME: redo with better formatting, (a table?) with parsed entries.
        const pre = document.createElement('pre');
        // Last line repeats information from the first line;
        // first line was included above.
        pre.innerHTML = result.out[0].text.slice(1, -1).join("");

        resultList.appendChild(pre);
        resultList.style.display = 'block';
        li.appendChild(resultList);
        list.appendChild(li);

    } else if (first_out && "tag" in first_out) {

        /* There was some sort of warning or error message produced.
           There could be output (in "result") as well. Often this the same
           as the input.

           DRY this with the other messages above.
        */

        // First the message classification line
        const bold = document.createElement('b');
        bold.className = "message";
        bold.innerText = first_out.symbol + ": " + first_out.tag;
        resultList.appendChild(bold);

        // Next populate warning or error message...
        const pre = document.createElement('p');
        // Remove gratuitous surrounding quotes.
        pre.innerHTML = first_out.text.slice(1, -1);
        resultList.appendChild(pre);

        // Finally include the returned result.
        if (result.result) {
            const li = document.createElement('li');
            li.className = 'result';
            li.appendChild(createLine(result.result));
            resultList.appendChild(li);

        }

        resultList.style.display = 'block';
        li.appendChild(resultList);
        list.appendChild(li);

    } else {
        results.forEach((result) => {

            result.out.forEach((out) => {
                const li = document.createElement('li');
                li.className = out.message ? 'message' : 'print';

                if (out.message) {
                    li.innerText += out.prefix + ': ';
                }

                li.appendChild(createLine(out.text.slice(1,-1)));

                resultList.appendChild(li);
            });

            if (result.result) {
                const li = document.createElement('li');
                li.className = 'result';
                li.appendChild(createLine(result.result));

                resultList.appendChild(li);
                resultList.style.display = 'block';
            }

            if (result.out.length) {
                resultList.style.display = 'block';
            }
        });

        // Add this to a list element in a block (which is CSS styled with a nice
        // frame around it.
        li.appendChild(resultList);
        list.appendChild(li);

        // rocky: I think this is gross that we post-process the list. But, for now, so be it.
        afterProcessResult(list);
    }
}

function submitQuery(element, onfinish, query) {
    if (welcome) {
        document.getElementById('welcomeContainer')?.fade({ duration: 0.2 });

        if (document.getElementById('hideStartupMsg')?.checked) {
            localStorage.setItem('hideMathicsStartupMsg', 'true');
        }

        welcome = false;
        document.getElementById('logo').classList.remove('load');
    }

    element.li?.classList.add('loading');
    document.getElementById('logo')?.classList.add('working');

    new Ajax.Request('/ajax/query/', {
        method: 'post',
        parameters: { query: query || element.value },
        onSuccess: (transport) => {
            if (element.ul) {
                element.ul.select('li[class!=request][class!=submitbutton]')
                    .forEach((element) => element.remove());

                if (!transport.responseText) {
                    // a fatal Python error has occurred, e.g. on 4.4329408320439^43214234345
                    // ("Fatal Python error: mp_reallocate failure")
                    // -> print overflow message
                    transport.responseText = '{"results": [{"out": [{"prefix": "General::noserver", "message": true, "tag": "noserver", "symbol": "General", "text": "<math><mrow><mtext>No server running.</mtext></mrow></math>"}]}]}';
                }

                const response = JSON.parse(transport.responseText);

                setResult(element.ul, response.results);
                element.submitted = true;
                element.results = response.results;

                const next = element.li.nextSibling;

                if (next) {
                    next.textarea.focus();
                } else {
                    createQuery();
                }
            }
        },
        onFailure: () => {
            element?.ul.select('li[class!=request]')
                .forEach((element) => element.remove());

            const li = document.createElement('li');
            li.className = 'serverError';
            li.innerText = 'Sorry, an error occurred while processing your request!';

            element?.ul.appendChild(li);
            element.submitted = true;
        },
        onComplete: () => {
            element?.li.classList.remove('loading');
            document.getElementById('logo')?.classList.remove('working');

            if (onfinish) {
                onfinish();
            }
        }
    });
}

function keyDown(event) {
    const textArea = lastFocus;

    if (!textArea) {
        return;
    }

    refreshInputSize(textArea);

    if (event.key === 'Enter' && (event.shiftKey || event.location === 3)) {
        event.stop();

        if (textArea.value.strip()) {
            submitQuery(textArea);
        }
    } else if (event.key === 'ArrowUp') {
        if (textArea.selectionStart === 0 && textArea.selectionEnd === 0) {
            if (isEmpty(textArea)) {
                if (textArea.li.previousSibling) {
                    textArea.li.previousSibling.textarea.focus();
                }
            } else {
                createQuery(textArea.li);
            }
        }
    } else if (event.key === 'ArrowDown') {
        if (textArea.selectionStart === textArea.value.length && textArea.selectionEnd === textArea.selectionStart) {
            if (isEmpty(textArea)) {
                if (textArea.li.nextSibling) {
                    textArea.li.nextSibling.textarea.focus();
                }
            } else {
                createQuery(textArea.li.nextSibling);
            }
        }
    } else if (isGlobalKey(event)) {
        event.stop();
        event.stopPropagation();
        event.preventDefault();
    }
}

function deleteMouseDown(event) {
    if (event.isLeftClick()) {
        deleting = true;
    }
}

function deleteClick() {
    if (lastFocus === this.li.textarea) {
        lastFocus = null;
    }

    this.li.remove();
    deleting = false;

    if (blurredElement) {
        blurredElement.focus();
        blurredElement = null;
    }

    if (document.getElementById('queries').childElementCount === 0) {
        createQuery();
    }
}

function moveMouseDown() {
    movedItem = this.li;
    movedItem.addClassName('moving');
}

function moveMouseUp() {
    if (movedItem) {
        movedItem.classList.remove('moving');
        movedItem.textarea.focus();
        movedItem = null;
    }
}

function onFocus() {
    this.li.classList.add('focused');
    lastFocus = this;
}

function onBlur() {
    blurredElement = this;

    if (!deleting &&
        this.li != movedItem &&
        isEmpty(this) &&
        document.getElementById('queries').childElementCount > 1
       ) {
        this.li.display = 'none';

        if (this == lastFocus) {
            lastFocus = null;
        }

        this.li.remove();
    }

    this.li.classList.remove('focused');
}

function createSortable() {
    Position.includeScrollOffsets = true;
    Sortable.create('queries', {
        handle: 'move',
        scroll: 'document',
        scrollSensitivity: 1 // otherwise strange flying-away of item at top
    });
}

function createQuery(beforeElement, noFocus, updatingAll) {
    const textarea = document.createElement('textarea');
    textarea.className = 'request';
    textarea.spellcheck = false;
    textarea.rows = 1;

    const submitButton = document.createElement('span');
    submitButton.innerText = '=';

    const submitButtonBox = document.createElement('span');
    submitButtonBox.className = 'submitbutton';
    submitButtonBox.title = 'Evaluate [Shift+Return]';
    submitButtonBox.appendChild(submitButton);

    const request = document.createElement('li');
    request.className = 'request';
    request.appendChild(textarea);
    request.appendChild(submitButtonBox);

    const ul = document.createElement('ul');
    ul.className = 'query';
    ul.appendChild(request);

    const moveHandle = document.createElement('span');
    moveHandle.className = 'move';

    const deleteHandle = document.createElement('span');
    deleteHandle.className = 'delete';
    deleteHandle.title = 'Delete';
    deleteHandle.innerText = '×';

    // items need id in order for Sortable.onUpdate to work.
    const li = document.createElement('li');
    li.id = 'query_' + queryIndex++;
    li.className = 'query';
    li.appendChild(ul);
    li.appendChild(moveHandle);
    li.appendChild(deleteHandle);

    textarea.ul = ul;
    textarea.li = li;
    textarea.submitted = false;
    moveHandle.li = li;
    deleteHandle.li = li;
    li.textarea = textarea;
    li.ul = ul;

    const queries = document.getElementById('queries');

    if (beforeElement) {
        queries.insertBefore(li, beforeElement);
    } else {
        queries.appendChild(li);
    }

    if (!updatingAll) {
        refreshInputSize(textarea);
    }

    textarea.addEventListener('keyup', inputChange);
    textarea.addEventListener('focus', onFocus);
    textarea.addEventListener('blur', onBlur);
    li.addEventListener('mousedown', queryMouseDown);
    deleteHandle.addEventListener('click', deleteClick);
    deleteHandle.addEventListener('mousedown', deleteMouseDown);
    moveHandle.addEventListener('mousedown', moveMouseDown);
    document.addEventListener('mouseup', moveMouseUp);
    submitButton.addEventListener('mousedown', () => {
        if (textarea.value.strip()) {
            submitQuery(textarea);
        } else {
            textarea.focus();
        }
    });

    if (!updatingAll) {
        createSortable();
    }

    if (!noFocus) {
        textarea.focus();
    }

    return li;
}

function documentMouseDown(event) {
    if (event.isLeftClick()) {
        if (clickedQuery) {
            clickedQuery = null;
            mouseDownEvent = null;

            return;
        }

        mouseDownEvent = event;
    }
}

function documentClick(event) {
    const queries = document.getElementById('queries');

    // in Firefox, mousedown also fires when user clicks scrollbars.
    // -> listen to click
    event = mouseDownEvent;

    if (!event) {
        return;
    }

    if (queries.childElementCount === 1 && isEmpty(queries.firstElementChild.textarea)) {
        queries.firstElementChild.textarea.focus();

        return;
    }

    const documentElement = document.getElementById('document');
    const y = event.pointerY() - documentElement.offsetTop + documentElement.scrollTop;

    let element = null;

    for (let i = 0; i < queries.childElementCount; i++) {
        // margin-top: 10px
        if (queries.children[i].positionedOffset().top + 20 > y) {
            element = queries.children[i];

            break;
        }
    }

    createQuery(element);
}

function queryMouseDown() {
    clickedQuery = this;
}

function focusLast() {
    if (lastFocus) {
        lastFocus.focus();
    } else {
        createQuery();
    }
}

function isGlobalKey(event) {
    if (event.ctrlKey) {
        const key = event.key.toLowerCase();

        if (key === 'd' || key === 's' || key === 'o') {
            return true;
        }
    }

    return false;
}

function globalKeyUp(event) {
    if (!popup && event.ctrlKey) {
        switch (event.keyCode) {
        case 68: // D
            showDoc();
            document.getElementById('search').select();
            event.stop();

            break;
        // case 67: // C
        //      focusLast();
        //      event.stop();
        //
        //      break;
        case 83: // S
            event.stop();
            event.stopPropagation();
            event.preventDefault();
            showSave();

            break;
        case 79: // O
            event.stop();
            event.stopPropagation();
            event.preventDefault();
            showOpen();

            break;
        }
    }
}

function domLoaded() {
    MathJax.Hub.Config({
        'HTML-CSS': {
            imageFont: null,
            linebreaks: {
                automatic: true,
                width: '70% container'
            }
        },
        MMLorHTML: {
            // the output jax that is to be preferred when both are possible
            // (set to 'MML' for native MathML, 'HTML' for MathJax's HTML-CSS output jax).
            prefer: {
                MSIE: 'HTML',
                Firefox: 'HTML',
                Opera: 'HTML',
                other: 'HTML'
            }
        }
    });

    MathJax.Hub.Configured();

    if (localStorage.getItem('hideMathicsStartupMsg') === 'true') {
        document.getElementById('welcome').style.display = 'none';
    }

    const queriesContainer = document.getElementById('queriesContainer');

    if (queriesContainer) {
        const queries = document.createElement('ul'),
              documentElement = document.getElementById('document');

        queries.id = 'queries';

        queriesContainer.appendChild(queries);

        documentElement.addEventListener('mousedown', documentMouseDown);
        documentElement.addEventListener('click', documentClick);

        document.addEventListener('keydown', keyDown);
        window.addEventListener('keydown', globalKeyUp);
        window.addEventListener('keyup', globalKeyUp);

        if (!loadLink()) {
            createQuery();
        }
    }
}

window.addEventListener('DOMContentLoaded', domLoaded);
window.addEventListener('resize', refreshInputSizes);

window.addEventListener('resize', function () {
    if (timeout >= 0) {
        // the user is still resizing so postpone the action further
        window.clearTimeout(timeout);
    }

    timeout = window.setTimeout(function () {
        document.querySelectorAll('#queries ul').forEach((ul) => {
            afterProcessResult(ul, 'Rerender');
        });

        timeout = -1; // reset the timeout
    }, 500);
});
