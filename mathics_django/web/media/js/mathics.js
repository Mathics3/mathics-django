var deleting,
	blurredElement,
	movedItem,
	clickedQuery,
	lastFocus = null,
	welcome = true;

function getLetterWidth(element) {
	const letter = document.createElement('span');

	letter.innerText = 'm';
	letter.style.fontFamily = element.style?.fontFamily || '';
	letter.style.fontSize = element.style?.fontSize || '';

	document.body.appendChild(letter);

	const width = letter.offsetWidth;

	document.body.removeChild(letter);

	return width;
}

function refreshInputSizes() {
	document.querySelectorAll('#queries ul').forEach((ul) => {
		afterProcessResult(ul, 'Rerender');
	});
}

function isEmpty(textarea) {
	return textarea.innerText.strip() === '' && !textarea.submitted;
}

function prepareText(text) {
	if (text == '') {
		text = String.fromCharCode(160);
	}

	return text;

	/*
	// Place &shy; between every two characters.
	// Problem: Copy & paste yields weird results!
	var result = '';
	for (var index = 0; index < text.length; ++index) {
	  result += text.charAt(index);
	  if (index < text.length - 1)
		result += String.fromCharCode(173); // &shy;
	}
	return result;
	*/
}

function getDimensions(math, callback) {
	var all = document.getElementById('calc_all').cloneNode(true);
	all.id = null;

	document.body.appendChild(all);
	var container = all.select('.calc_container')[0];
	container.appendChild(translateDOMElement(math));

	MathJax.Hub.Queue(['Typeset', MathJax.Hub, container]);
	MathJax.Hub.Queue(() => {
		var pos = container.cumulativeOffset();
		var next = all.select('.calc_next')[0].cumulativeOffset();
		var below = all.select('.calc_below')[0].cumulativeOffset();
		var width = next.left - pos.left + 4;
		var height = below.top - pos.top + 20;
		document.body.removeChild(all);
		callback(width, height);
	});
}

function drawMeshGradient(ctx, points) {
	function color(c, a) {
		return `rgba(${Math.round(c[0] * 255)}, ${Math.round(c[1] * 255)}, ${Math.round(c[2] * 255)}, ${a})`;
	}

	var grad1 = ctx.createLinearGradient(0, 0, 0.5, 0.5);
	grad1.addColorStop(0, color(points[0][1], 1));
	grad1.addColorStop(1, color(points[0][1], 0));
	var grad2 = ctx.createLinearGradient(1, 0, 0, 0);
	grad2.addColorStop(0, color(points[1][1], 1));
	grad2.addColorStop(1, color(points[1][1], 0));
	var grad3 = ctx.createLinearGradient(0, 1, 0, 0);
	grad3.addColorStop(0, color(points[2][1], 1));
	grad3.addColorStop(1, color(points[2][1], 0));

	ctx.save();
	ctx.setTransform(points[1][0][0] - points[0][0][0], points[1][0][1] - points[0][0][1],
		points[2][0][0] - points[0][0][0], points[2][0][1] - points[0][0][1], points[0][0][0], points[0][0][1]);

	ctx.beginPath();
	ctx.moveTo(0, 0);
	ctx.lineTo(1, 0);
	ctx.lineTo(0, 1);
	ctx.closePath();

	ctx.globalCompositeOperation = 'lighter';
	ctx.fillStyle = grad1;
	ctx.fill();
	ctx.fillStyle = grad2;
	ctx.fill();
	ctx.fillStyle = grad3;
	ctx.fill();
	ctx.restore();
}

function createMathNode(nodeName) {
	if (['svg', 'g', 'rect', 'circle', 'polyline', 'polygon', 'path', 'ellipse', 'foreignObject'].include(nodeName)) {
		return document.createElementNS('http://www.w3.org/2000/svg', nodeName);
	}
	else {
		return document.createElement(nodeName);
	}
}

var objectsPrefix = 'math_object_', objectsCount = 0, objects = {};

function translateDOMElement(element, svg) {
	if (element.nodeType == 3) {
		var text = element.nodeValue;
		return $T(text);
	}
	var dom = null;
	var nodeName = element.nodeName;
	if (nodeName != 'meshgradient') {
		dom = createMathNode(element.nodeName);
		for (var i = 0; i < element.attributes.length; ++i) {
			var attr = element.attributes[i];
			if (attr.nodeName != 'ox' && attr.nodeName != 'oy') {
				dom.setAttribute(attr.nodeName, attr.nodeValue);
			}
		}
	}
	if (nodeName == 'foreignObject') {
		dom.setAttribute('width', svg.getAttribute('width'));
		dom.setAttribute('height', svg.getAttribute('height'));
		dom.setAttribute('style', dom.getAttribute('style') + '; text-align: left; padding-left: 2px; padding-right: 2px;');
		var ox = parseFloat(element.getAttribute('ox'));
		var oy = parseFloat(element.getAttribute('oy'));
		dom.setAttribute('ox', ox);
		dom.setAttribute('oy', oy);
	}
	if (nodeName == 'mo') {
		const op = element.childNodes[0].nodeValue;

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
	if (nodeName == 'meshgradient') {
		var data = JSON.parse(element.getAttribute('data'));
		var div = document.createElementNS('http://www.w3.org/1999/xhtml', 'div');
		var foreign = document.createElementNS('http://www.w3.org/2000/svg', 'foreignObject');
		foreign.setAttribute('width', svg.getAttribute('width'));
		foreign.setAttribute('height', svg.getAttribute('height'));
		foreign.setAttribute('x', '0px');
		foreign.setAttribute('y', '0px');
		foreign.appendChild(div);

		var canvas = createMathNode('canvas');
		canvas.setAttribute('width', svg.getAttribute('width'));
		canvas.setAttribute('height', svg.getAttribute('height'));
		div.appendChild(canvas);

		var ctx = canvas.getContext('2d');

		for (var i = 0; i < data.length; ++i) {
			if (data[i].length == 3) {
				drawMeshGradient(ctx, data[i]);
			}
		}

		dom = foreign;
	}
	var object = null;
	if (nodeName == 'svg' || nodeName.toLowerCase() == 'img') {
		// create <mspace> that will contain the graphics
		object = createMathNode('mspace');
		var width, height;
		if (nodeName == 'svg' || nodeName.toLowerCase() == 'img') {
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
	if (nodeName == 'svg')
		svg = dom;
	var rows = [[]];
	$A(element.childNodes).each(function (child) {
		if (child.nodeName == 'mspace' && child.getAttribute('linebreak') == 'newline') {
			rows.push([]);
		} else {
			rows[rows.length - 1].push(child);
		}
	});
	var childParent = dom;
	if (nodeName == 'math') {
		var mstyle = createMathNode('mstyle');
		mstyle.setAttribute('displaystyle', 'true');
		dom.appendChild(mstyle);
		childParent = mstyle;
	}
	if (rows.length > 1) {
		var mtable = createMathNode('mtable');
		mtable.setAttribute('rowspacing', '0');
		mtable.setAttribute('columnalign', 'left');
		var nospace = 'cell-spacing: 0; cell-padding: 0; row-spacing: 0; row-padding: 0; border-spacing: 0; padding: 0; margin: 0';
		mtable.setAttribute('style', nospace);
		rows.forEach((row) => {
			var mtr = createMathNode('mtr');
			mtr.setAttribute('style', nospace);
			var mtd = createMathNode('mtd');
			mtd.setAttribute('style', nospace);
			row.forEach((element) => {
				var elmt = translateDOMElement(element, svg);
				if (nodeName == 'mtext') {
					// wrap element in mtext
					var outer = createMathNode('mtext');
					outer.appendChild(elmt);
					elmt = outer;
				}
				mtd.appendChild(elmt);
			});
			mtr.appendChild(mtd);
			mtable.appendChild(mtr);
		});
		if (nodeName == 'mtext') {
			// no mtable inside mtext, but mtable instead of mtext
			dom = mtable;
		} else {
			childParent.appendChild(mtable);
		}
	} else
		rows[0].forEach((element) => {
			childParent.appendChild(translateDOMElement(element, svg));
		});
	if (object) {
		var id = objectsCount++;
		object.setAttribute('id', objectsPrefix + id);
		objects[id] = dom;
		return object;
	}
	return dom;
}

function convertMathGlyphs(dom) {
	// convert mglyphs to their classic representation (<svg> or <img>), so the new mglyph logic does not make
	// anything worse in the classic Mathics frontend for now. In the long run, this code should vanish.

	const MML = 'http://www.w3.org/1998/Math/MathML';
	const glyphs = dom.getElementsByTagName('mglyph');
	for (let i = 0; i < glyphs.length; i++) {
		var glyph = glyphs[i];
		var src = glyph.getAttribute('src');
		if (src.startsWith('NUNCAMENENCONTRARASdata:image/svg+xml;base64,')) {
			var svgText = atob(src.substring(src.indexOf(',') + 1));
			var mtable = document.createElementNS(MML, 'mtable');
			mtable.innerHTML = '<mtr><mtd>' + svgText + '</mtd></mtr>';
			var svg = mtable.getElementsByTagNameNS('*', 'svg')[0];
			svg.setAttribute('width', glyph.getAttribute('width'));
			svg.setAttribute('height', glyph.getAttribute('height'));
			glyph.parentNode.replaceChild(mtable, glyph);
		} else if (src.startsWith('data:image/')) {
			var img = document.createElement('img');
			img.setAttribute('src', src);
			img.setAttribute('width', glyph.getAttribute('width'));
			img.setAttribute('height', glyph.getAttribute('height'));
			glyph.parentNode.replaceChild(img, glyph);
		}
	}
}

function createLine(value) {
	const container = document.createElement('div');

	container.innerHTML = value;

	if (container?.firstElementChild?.tagName === 'math') {
		convertMathGlyphs(container);

		return translateDOMElement(container.childNodes[0]);
	} else if (container?.firstElementChild?.tagName === 'GRAPHICS3D') {
		const div = document.createElement('div');

		drawGraphics3D(div, JSON.parse(container.firstElementChild.attributes.data.value));

		div.style.position = 'relative';
		div.style.width = '400px';
		div.style.margin = 'auto';

		return div;
	} else if (container?.firstElementChild?.tagName === 'svg') {
		container.style.position = 'relative';
		container.style.width = '400px';
		container.style.margin = 'auto';

		return container;
	} else {
		const lines = container.innerHTML.split('\n');

		const p = document.createElement('p');

		for (let i = 0; i < lines.length; ++i) {
			p.appendChild($T(prepareText(lines[i])));
			if (i < lines.length - 1) {
				p.appendChild(document.createElement('br'));
			}
		}

		return p;
	}
}

function afterProcessResult(ul, command) {
	// command is either 'Typeset' (default) or 'Rerender'
	if (!command) {
		command = 'Typeset';
	}
	MathJax.Hub.Queue([command, MathJax.Hub, ul]);
	MathJax.Hub.Queue(() => {
		// inject SVG and other non-MathML objects into corresponding <mspace>s
		ul.querySelectorAll('.mspace').forEach((mspace) => {
			var id = mspace.getAttribute('id').substr(objectsPrefix.length);
			var object = objects[id];
			mspace.appendChild(object);
		});
	});

	MathJax.Hub.Queue(['Typeset', MathJax.Hub, ul]);

	MathJax.Hub.Queue(() => {
		ul.querySelectorAll('foreignObject > span > nobr > span.math')
			.forEach((math) => {
				var content = math.childNodes[0].childNodes[0].childNodes[0];
				math.removeChild(math.childNodes[0]);
				math.insertBefore(content, math.childNodes[0]);

				if (command === 'Typeset') {
					// recalculate positions of insets based on ox/oy properties
					const foreignObject = math.parentNode.parentNode.parentNode;
					const dimensions = math.getDimensions();
					const w = dimensions.width + 4;
					const h = dimensions.height + 4;
					let x = parseFloat(foreignObject.getAttribute('x').substr());
					let y = parseFloat(foreignObject.getAttribute('y'));
					const ox = parseFloat(foreignObject.getAttribute('ox'));
					const oy = parseFloat(foreignObject.getAttribute('oy'));
					x = x - w / 2.0 - ox * w / 2.0;
					y = y - h / 2.0 + oy * h / 2.0;
					foreignObject.setAttribute('x', x + 'px');
					foreignObject.setAttribute('y', y + 'px');
				}
			});
	});
}

function setResult(ul, results) {
	results.forEach((result) => {
		const resultUl = document.createElement('ul');
		resultUl.className = 'out';

		result.out.forEach((out) => {
			const li = document.createElement('li');
			li.className = out.message ? 'message' : 'print';

			if (out.message) {
				li.innerText = out.prefix + ': ';
			}

			li.appendChild(createLine(out.text));

			resultUl.appendChild(li);
		});

		if (result.result != null) {
			const li = document.createElement('li');
			li.className = 'result';
			li.appendChild(createLine(result.result));

			resultUl.appendChild(li);
		}

		ul.appendChild($E(li, { 'class': 'out' }, resultUl));
	});
	afterProcessResult(ul);
}

function submitQuery(textarea, onfinish) {
	if (welcome) {
		document.getElementById('welcomeContainer').fade({ duration: 0.2 });
		if (document.getElementById('hideStartupMsg').checked) {
			localStorage.setItem('hideMathicsStartupMsg', 'true');
		}
		welcome = false;
		document.getElementById('logo').classList.remove('load');
	}

	textarea.li.classList.add('loading');
	document.getElementById('logo').classList.add('working');
	new Ajax.Request('/ajax/query/', {
		method: 'post',
		parameters: {
			query: textarea.value
		},
		onSuccess: (transport) => {
			textarea.ul.select('li[class!=request][class!=submitbutton]').invoke('deleteElement');
			if (!transport.responseText) {
				// a fatal Python error has occurred, e.g. on 4.4329408320439^43214234345
				// ("Fatal Python error: mp_reallocate failure")
				// -> print overflow message
				transport.responseText = '{"results": [{"out": [{"prefix": "General::noserver", "message": true, "tag": "noserver", "symbol": "General", "text": "<math><mrow><mtext>No server running.</mtext></mrow></math>"}]}]}';
			}
			var response = JSON.parse(transport.responseText);
			setResult(textarea.ul, response.results);
			textarea.submitted = true;
			textarea.results = response.results;
			var next = textarea.li.nextSibling;
			if (next) {
				next.textarea.focus();
			} else {
				createQuery();
			}
		},
		onFailure: () => {
			textarea.ul.querySelectorAll('li[class!=request]')
				.forEach((element) =>
					element.parentElement.removeChild(element)
				);

			const li = document.createElement('li');

			li.className = 'serverError';
			li.innerText = 'Sorry, an error occurred while processing your request!';

			textarea.ul.appendChild(li);
			textarea.submitted = true;
		},
		onComplete: () => {
			textarea.li.classList.remove('loading');
			document.getElementById('logo').classList.remove('working');

			if (onfinish) {
				onfinish();
			}
		}
	});
}

function getSelection() {
	// TODO
}

function keyDown(event) {
	const textArea = lastFocus;

	if (!textArea) {
		return;
	}

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
		event.preventDefault();
	}
}

function deleteMouseDown(event) {
	if (event.isLeftClick()) {
		deleting = true;
	}
}

function deleteClick() {
	if (lastFocus == this.li.textarea) {
		lastFocus = null;
	}

	this.li.deleteElement();
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
	var textarea = this;
	textarea.li.classList.add('focused');
	lastFocus = textarea;
}

function onBlur() {
	var textarea = this;
	blurredElement = textarea;
	if (!deleting && textarea.li != movedItem && isEmpty(textarea) && document.getElementById('queries').childElementCount > 1) {
		textarea.li.display = 'none';
		if (textarea == lastFocus) {
			lastFocus = null;
		}

		textarea.li.deleteElement();
	}
	textarea.li.classList.remove('focused');
}

function createSortable() {
	Position.includeScrollOffsets = true;
	Sortable.create('queries', {
		handle: 'move',
		scroll: 'document',
		scrollSensitivity: 1 // otherwise strange flying-away of item at top
	});
}

var queryIndex = 0;

function createQuery(before, noFocus, updatingAll) {
	// items need id in order for Sortable.onUpdate to work
	const li = document.createElement('li');
	li.id = 'query_' + queryIndex++;
	li.className = 'query';

	const query = document.createElement('ul');
	query.className = 'query';

	li.appendChild(query)

	const request = document.createElement('li');
	request.className = 'request';

	query.appendChild(request)

	const textArea = document.createElement('span');
	textArea.className = 'request';
	textArea.spellcheck = false;
	textArea.setAttribute('role', 'textbox');
	textArea.contentEditable = true;

	request.appendChild(textArea)

	const submitButton = document.createElement('span');
	submitButton.className = 'submitbutton';
	submitButton.title = 'Evaluate [Shift+Return]';
	submitButton.innerText = '=';

	request.appendChild(submitButton)

	const moveHandle = document.createElement('span');
	moveHandle.className = 'move';

	li.appendChild(moveHandle)

	const deleteHandle = document.createElement('span');
	deleteHandle.className = 'delete';
	deleteHandle.title = 'Delete';
	deleteHandle.innerText = '×';

	li.appendChild(deleteHandle)

	textArea.submitted = false;
	textArea.li = li;
	moveHandle.li = li;
	deleteHandle.li = li;
	li.textarea = textArea;
	li.ul = query;

	const queries = document.getElementById('queries');

	if (before) {
		queries.insertBefore(li, before);
	} else {
		queries.appendChild(li);
	}

	textArea.addEventListener('focus', onFocus);
	textArea.addEventListener('blur', onBlur);
	li.addEventListener('mousedown', queryMouseDown);
	deleteHandle.addEventListener('click', deleteClick);
	deleteHandle.addEventListener('mousedown', deleteMouseDown);
	moveHandle.addEventListener('mousedown', moveMouseDown);
	moveHandle.addEventListener('mouseup', moveMouseUp);
	document.addEventListener('mouseup', moveMouseUp);
	submitButton.addEventListener('mousedown', () => {
		if (textArea.value.strip()) {
			submitQuery(textArea);
		} else {
			textArea.focus();
		}
	});
	if (!updatingAll) {
		createSortable();
	}

	if (!noFocus) {
		textArea.focus();
	}

	return li;
}

var mouseDownEvent = null;

function documentMouseDown(event) {
	if (event.isLeftClick()) {
		if (clickedQuery) {
			clickedQuery = null;
			mouseDownEvent = null;

			return;
		}
		event.stop(); // strangely, doesn't work otherwise
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
	var offset = documentElement.cumulativeOffset();
	var y = event.pointerY() - offset.top + documentElement.scrollTop;
	var element = null;

	queries.childElements.forEach((li) => {
		// margin-top: 10px
		if (li.positionedOffset().top + 20 > y) {
			element = li;
			throw $break;
		}
	});

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
		switch (event.keyCode) {
			case 68:
			// case 67:
			case 83:
			case 79:
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
			// 	focusLast();
			// 	event.stop();
			// 	break;
			case 83: // S
				showSave();
				break;
			case 79: // O
				showOpen();
				break;
		}
	}
}

function domLoaded() {
	MathJax.Hub.Config({
		"HTML-CSS": {
			imageFont: null,
			linebreaks: { automatic: true }
		},
		MMLorHTML: {
			// the output jax that is to be preferred when both are possible
			// (set to "MML" for native MathML, "HTML" for MathJax's HTML-CSS output jax).
			prefer: {
				MSIE: "HTML",
				Firefox: "HTML",
				Opera: "HTML",
				other: "HTML"
			}
		}
	});
	MathJax.Hub.Configured();

	if (localStorage.getItem('hideMathicsStartupMsg') === 'true') {
		document.getElementById('welcome').style.display = 'none';
	}

	const queriesContainer = document.getElementById('queriesContainer');

	if (queriesContainer) {
		const list = document.createElement('ul');
		list.id = 'queries';

		queriesContainer.appendChild(list);

		const documentElement = document.getElementById('document');

		documentElement.addEventListener('mousedown', documentMouseDown);
		documentElement.addEventListener('click', documentClick);

		document.addEventListener('keydown', keyDown);
		document.addEventListener('keyup', globalKeyUp);

		if (!loadLink()) {
			createQuery();
		}
	}
}

window.addEventListener('DOMContentLoaded', domLoaded);