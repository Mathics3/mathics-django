Element.addMethods({
	deleteElement: function (element) {
		if (element.parentNode) {
			element.parentNode.removeChild(element);
		}
	},
	scrollIntoView: function (element) {
		const offset = element.cumulativeOffset();
		window.scrollTo(offset.left, offset.top);
	}
});

function submitForm(form, url, onSuccess, extraData) {
	let parameters = {};

	form = document.getElementById(form);

	form.querySelectorAll('input').forEach((input) => {
		parameters[input.name] = input.value;
	});

	form.querySelectorAll('input[type="text"]').forEach((input) => {
		input.blur();
	});

	form.querySelectorAll('input, button').forEach((input) => {
		input.disable();
	});

	if (!extraData) {
		extraData = {};
	}

	parameters = new Hash(parameters).merge(extraData);

	new Ajax.Request(url, {
		method: 'post',
		parameters,
		onSuccess: (transport) => {
			const response = JSON.parse(transport.responseText);

			form.querySelectorAll('ul.errorlist').forEach((element) => {
				element.parentElement.removeChild(element);
			});

			let errors = false, errorFocus = false;
			if (response.form.fieldErrors) {
				new Hash(response.form.fieldErrors).forEach((pair) => {
					errors = true;

					const errorList = document.createElement('ul');
					errorList.className = 'errorlist';

					const input = form.querySelector('[name="' + pair.key + '"]');
					pair.value.forEach((msg) => {
						const li = document.createElement('li');
						li.innerText = msg;
						errorList.appendChild(li);
					});
					input.insert({ before: errorList });
					if (!errorFocus) {
						errorFocus = input;
					}
				});
			}
			if (response.form.generalErrors) {
				const errorlist = document.createElement('ul');
				errorlist.className = 'errorlist';

				response.form.generalErrors.forEach((msg) => {
					errors = true;

					const li = document.createElement('li');
					li.innerText = msg;

					errorlist.appendChild(li);
				});

				form.insert({ top: errorlist });
				if (!errorFocus) {
					const firstInput = form.querySelector('input');
					if (firstInput) {
						errorFocus = firstInput;
					}
				}
			}
			form.querySelectorAll('input').forEach((input) => {
				input.enable();
			});
			if (errorFocus) {
				errorFocus.activate();
			}
			if (!errors) {
				response.values = parameters;
				onSuccess(response);
			}
		},
		onComplete: () => {
			form.getElementsByTagName('input').forEach((input) => {
				input.enable();
			});
		}
	});
}
