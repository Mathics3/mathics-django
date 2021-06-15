function grayOut(visible, zindex) {
	zindex = zindex || 50;

	let dark = document.getElementById('dark');

	if (!dark) {
		// the dark layer doesn't exist, it's never been created. So we'll
		// create it here and apply some basic styles.
		// if you are getting errors in IE see: http://support.microsoft.com/default.aspx/kb/927917

		const node = document.createElement('div');

		node.className = 'dark';
		node.id = 'dark';
		node.display = 'none';

		document.body.appendChild(node);

		dark = node;
	}

	if (visible) {
		dark.style.zIndex = zindex;
		dark.style.backgroundColor = '#000000';
		dark.style.opacity = (70 / 100);
	} else {
		dark.style.display = 'none';
	}
}

let popup;

function showPopup(element) {
	const container = document.createElement('div');
	container.className = 'popupContainer';

	const div = document.createElement('div');
	div.className = 'popup';

	const frameContainer = document.createElement('div');
	frameContainer.className = 'popupFrameContainer';

	const frame = document.createElement('iframe');
	frame.className = 'popupFrame';

	element.style.display = 'block';

	div.appendChild(element);
	container.appendChild(div);
	document.body.appendChild(container);

	frame.style.width = div.offsetWidth + 'px';
	frame.style.height = div.offsetHeight + 'px';

	frameContainer.appendChild(frame);

	grayOut(true, 9);

	frame.scrollIntoView();

	const submit = element.querySelector('input.submit, button.submit');

	const onSubmit = (event) => {
		if (event.key === 'Enter') {
			submit.onclick();
		}
	};
	if (submit && submit.onclick) {
		document.addEventListener('keydown', onSubmit);
	}

	const cancel = element.querySelector('input.cancel, button.cancel');
	const onCancel = (event) => {
		if (event.key === 'Escape') {
			cancel.onclick();
		}
	};
	if (cancel && cancel.onclick) {
		document.addEventListener('keydown', onCancel);
	}

	element.querySelector('input')?.focus();

	popup = [[container, frameContainer], onSubmit, onCancel];

	return popup;
}

function hidePopup() {
	var containers = popup[0];
	var onSubmit = popup[1];
	var onCancel = popup[2];

	containers.forEach((item) => {
		item.style.display = 'none';
	});

	grayOut(false);

	document.removeEventListener('keydown', onSubmit);
	document.removeEventListener('keydown', onCancel);

	popup = null;
}

var dialogYesCallback;

function showDialog(title, text, yesCaption, noCaption, yesCallback) {
	const dialog = document.getElementById('dialog');

	dialog.getElementsByTagName('h1')[0].innerText = title;
	dialog.getElementsByTagName('p')[0].innerText = text;
	dialog.querySelector('input.submit').value = yesCaption;
	dialog.querySelector('input.cancel').value = noCaption;

	dialogYesCallback = yesCallback;

	dialogPopup = showPopup(dialog);

	return dialogPopup;
}