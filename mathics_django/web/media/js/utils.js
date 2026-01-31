function submitForm(form, url, onSuccess, extraData) {
	let parameters = {};

	form = document.getElementById(form);

	form.querySelectorAll('input').forEach((input) => {
		parameters[input.name] = input.value;
	});

	form.querySelectorAll('input[type="text"]').forEach(
		(input) => input.blur()
	);

	form.querySelectorAll('input, button').forEach(
		(input) => input.disable()
	);

	new Ajax.Request(url, {
		method: 'post',
		parameters: { ...parameters, ...extraData },
		onSuccess: (transport) => {
			const response = JSON.parse(transport.responseText);

			form.querySelectorAll('ul.errorlist').forEach((element) => {
				element.parentElement.removeChild(element);
			});

			let errors = false, errorFocus = false;

			if (response.form.fieldErrors) {
				new Hash(response.form.fieldErrors).forEach((pair) => {
					errors = true;

					const errorList = document.createElement('ul'),
						input = form.querySelector(`[name="${pair.key}"]`);

					errorList.className = 'errorlist';

					pair.value.forEach((msg) => {
						const li = document.createElement('li');

						li.innerText = msg;

						errorList.appendChild(li);
					});

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

				if (!errorFocus) {
					const firstInput = form.querySelector('input');

					if (firstInput) {
						errorFocus = firstInput;
					}
				}
			}

			form.querySelectorAll('input').forEach(
				(input) => input.enable()
			);

			if (errorFocus) {
				errorFocus.activate();
			}

			if (!errors) {
				onSuccess({ ...response, values: parameters });
			}
		},
		onComplete: () => {
			form.getElementsByTagName('input').forEach(
				(input) => input.enable()
			);
		}
	});
}
