let authenticated = false, loginReason, loginNext;

function showLogin(reason, next) {
	document.getElementById('passwordSent').style.display = 'none';

	const loginReasonElement = document.getElementById('loginReason');

	if (reason) {
		loginReasonElement.style.display = 'block';
		loginReasonElement.innerText = reason;
	} else {
		loginReasonElement.style.display = 'none';
	}

	showPopup(document.getElementById('login'));

	loginNext = next;
}

function onLogin(username) {
	document.getElementById('notAuthenticated').style.display = 'none';
	document.getElementById('authenticated').style.display = 'block';
	document.getElementById('username').innerText = username;

	authenticated = true;
}

function onLogout() {
	document.getElementById('authenticated').style.display = 'none';
	document.getElementById('notAuthenticated').style.display = 'block';
	document.getElementById('username').innerText = '';

	authenticated = false;
}

function login() {
	submitForm('loginForm', '/ajax/login/', (response) => {
		const { email, result } = response.form.values;

		if (result === 'ok') {
			onLogin(email);
			hidePopup();

			if (loginNext) {
				loginNext();
			}
		} else {
			document.getElementById('passwordEmail').innerText = email;
			document.getElementById('passwordSent').style.display = 'block';
		}
	});
}

function logout() {
	new Ajax.Request('/ajax/logout/', {
		method: 'post',
		onSuccess: onLogout
	});
}

function requireLogin(reason, onLogin) {
	loginReason = reason;

	if (REQUIRE_LOGIN && !authenticated) {
		showLogin(reason, onLogin);
	} else {
		onLogin();
	}
}

function checkLogin(response) {
	if (REQUIRE_LOGIN && response.requireLogin) {
		onLogout();
		hidePopup();
		showLogin(loginReason, loginNext);

		return false;
	}

	return true;
}
