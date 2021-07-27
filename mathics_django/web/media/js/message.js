let popup, dialogYesCallback;

function grayOut(visible, zindex) {
	let dark = document.getElementById('dark');

	if (!dark) {
		// the dark layer  never been created, so we'll create it

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

function showPopup(element) {
	const container = document.createElement('div'),
		div = document.createElement('div'),
		frameContainer = document.createElement('div'),
		frame = document.createElement('iframe');

	container.className = 'popupContainer';

	div.className = 'popup';

	frameContainer.className = 'popupFrameContainer';

	frame.className = 'popupFrame';

	element.style.display = 'block';

	div.appendChild(element);
	container.appendChild(div);
	document.body.appendChild(container);

	frame.style.width = div.offsetWidth + 'px';
	frame.style.height = div.offsetHeight + 'px';

	frameContainer.appendChild(frame);

	grayOut(true, 9);

	window.scrollTo(0, frame.offsetTop);

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
	const [containers, onSubmit, onCancel] = popup;

	containers.forEach((item) => {
		item.style.display = 'none';
	});

	grayOut(false);

	document.removeEventListener('keydown', onSubmit);
	document.removeEventListener('keydown', onCancel);

	popup = null;
}

function showDialog(title, text, yesCaption, noCaption, yesCallback) {
	const dialog = document.getElementById('dialog');

	dialog.querySelector('h1').innerText = title;
	dialog.querySelector('p').innerText = text;
	dialog.querySelector('input.submit').value = yesCaption;
	dialog.querySelector('input.cancel').value = noCaption;

	dialogYesCallback = yesCallback;

	dialogPopup = showPopup(dialog);

	return dialogPopup;
}
