let docLoaded = false, lastSearchValue = '';

function showPage(response) {
	const doc = document.getElementById('doc');

	if (doc) {
		doc.innerHTML = response.content;
	}

	document.querySelectorAll('li.test p').forEach((test) => {
		const submitButton = document.createElement('span');
		submitButton.innerText = '=';

		const submitButtonBox = document.createElement('span');
		submitButtonBox.className = 'submitbutton';
		submitButtonBox.title = 'Run this example!';
		submitButtonBox.appendChild(submitButton);

		test.appendChild(submitButtonBox);

		test.addEventListener('mouseover',
			() => test.classList.add('focused')
		);

		test.addEventListener('mouseout',
			() => test.classList.remove('focused')
		);

		test.children[1].addEventListener('click', () => {
			setQueries([
				test.firstElementChild.innerHTML
					.replace(/\xA0/g, ' ')
					.unescapeHTML()
			]);
		});
	});

	document.querySelectorAll('ul.test').forEach((test) => {
		const id = test.id.substr(5); // 'test_...'
		const { results } = response.data[id];

		setResult(test, results);
	});
}

function loadDoc(page) {
	new Ajax.Request('/ajax/doc' + page, {
		method: 'get',
		onSuccess: (transport) => {
			docLoaded = true;

			showPage(JSON.parse(transport.responseText));

			window.scrollTo(
				0,
				document.querySelector('#doc *').offsetTop
			);
		}
	});
}

function showDoc() {
	const docLink = document.getElementById('doclink');

	document.getElementById('doc').style.display = 'block';

	document.getElementById('document').classList.add('doc');
	document.getElementById('code').classList.add('doc');

	docLink.classList.add('active');
	docLink.querySelector('i').classList.remove('fa-question-circle-o');
	docLink.querySelector('i').classList.add('fa-question-circle');

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
	docLink.querySelector('i').classList.add('fa-question-circle-o');
	docLink.querySelector('i').classList.remove('fa-question-circle');

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

window.addEventListener('DOMContentLoaded', () => {
	const search = document.getElementById('search');

	search.addEventListener('focus', searchFocus);
	search.addEventListener('blur', searchBlur);
	search.addEventListener('keydown', searchKeyDown);
	search.addEventListener('keyup', searchKeyUp);
	search.addEventListener('keyup', searchChange);
	search.value = '';

	searchBlur();
});
