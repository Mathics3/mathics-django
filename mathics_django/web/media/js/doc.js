var docLoaded = false, lastSearchValue = '';

function showPage(response) {
	const doc = document.getElementById('doc');

	if (doc) {
		doc.updateDOM(response.content);
	}

	document.querySelectorAll('li.test p').forEach((test) => {
		test.insert($E('span',
			{ class: 'submitbutton', title: 'Run this example!' },
			submitButton = $E('span', $T('='))
		));

		test.addEventListener('mouseover', () => {
			test.classList.add('focused');
		});
		test.addEventListener('mouseout', () => {
			test.classList.remove('focused');
		});

		test.children[1].addEventListener('click', () => {
			var query = test.firstElementChild.innerHTML;
			query = query.replace(/\xA0/g, ' ');
			query = query.unescapeHTML();
			setQueries([query]);
		});
	});

	document.querySelectorAll('ul.test').forEach((test) => {
		var id = test.id.substr(5); // 'test_...'
		var data = response.data[id];
		setResult(test, data.results);
	});
}

function loadDoc(page) {
	new Ajax.Request('/ajax/doc' + page, {
		method: 'get',
		onSuccess: (transport) => {
			docLoaded = true;
			showPage(JSON.parse(transport.responseText));
			document.querySelector('#doc *').scrollIntoView();
		}
	});
}

function showDoc() {
	const docLink = document.getElementById('doclink');

	document.getElementById('doc').style.display = 'block';

	document.getElementById('document').classList.add('doc');
	document.getElementById('code').classList.add('doc');

	docLink.classList.add('active');
	docLink.select('i')[0].classList.remove('fa-question-circle-o');
	docLink.select('i')[0].classList.add('fa-question-circle');

	document.getElementById('search').classList.add('shown');

	if (!docLoaded) {
		loadDoc('/');
	}
}

function hideDoc() {
	const docLink = document.getElementById('doclink');

	document.getElementById('doc').style.display = 'none';

	document.getElementById('document').classList.remove('doc');
	document.getElementById('code').classList.remove('doc');

	docLink.classList.remove('active');
	docLink.getElementsByTagName('i')[0].classList.add('fa-question-circle-o');
	docLink.getElementsByTagName('i')[0].classList.remove('fa-question-circle');

	document.getElementById('search').classList.remove('shown');
}

function toggleDoc() {
	if (document.getElementById('doc').style.display !== 'none') {
		hideDoc();
	} else {
		showDoc();
	}
	document.getElementById('search').select();
}

function searchChange() {
	const search = document.getElementById('search');

	const query = search.value.strip();

	if (!search.hasClassName('empty')) {
		if (query) {
			new Ajax.Request('/ajax/doc/search/', {
				method: 'get',
				parameters: { query },
				onSuccess: (transport) => {
					docLoaded = true;
					showPage(JSON.parse(transport.responseText));
					showDoc();
				}
			});
		} else if (lastSearchValue != '') {
			hideDoc();
			loadDoc('/');
		}
		lastSearchValue = query;
	} else {
		lastSearchValue = '';
	}
}

function searchFocus() {
	const search = document.getElementById('search');

	if (search.hasClassName('empty')) {
		search.value = '';
		search.classList.remove('empty');
	}
}

function searchBlur() {
	const search = document.getElementById('search');

	if (!search.value) {
		search.classList.add('empty');
		search.value = "\uf002";
	}
}

function searchKeyUp(event) {
	if (event.key === 'Escape') {
		event.stop();
		document.getElementById('search').value = '';
		hideDoc();
		loadDoc('/');
		focusLast();
	}
}

function searchKeyDown(event) {
	if (isGlobalKey(event)) {
		event.stop();
	}
}

function initDoc() {
	const search = document.getElementById('search');

	search.addEventListener('focus', searchFocus);
	search.addEventListener('blur', searchBlur);
	search.addEventListener('keydown', searchKeyDown);
	search.addEventListener('keyup', searchKeyUp);
	search.addEventListener('keyup', searchChange);
	search.value = '';

	searchBlur();
}

window.addEventListener('DOMContentLoaded', initDoc);