var currentUser = null; // 'luca.masters@gmail.com';

function call_watcher()
{
	navigator.id.watch({
		loggedInUser: currentUser,
		onlogin: function(assertion) {
			alert('Called login!');
			// A user has logged in! Here you need to:
			// 1. Send the assertion to your backend for verification and to create a session.
			// 2. Update your UI.
			$.ajax({
				type: 'POST',
				url: '/persona_login', // app.route
				data: {assertion: assertion},
				success: function(res, status, xhr) {alert('Logged in.'); window.location.reload(); },
				error: function(xhr, status, err) {
					//navigator.id.logout();
					alert("Login failure: " + err);
				}
			});
		},
		onlogout: function() {
				alert('Hey!');
			// A user has logged out! Here you need to:
			// Tear down the user's session by redirecting the user or making a call to your backend.
			// Also, make sure loggedInUser will get set to null on the next page load.
			// (That's a literal JavaScript null. Not false, 0, or undefined. null.)
			$.ajax({
				type: 'POST',
				url: '/persona_logout', // This is a URL on your website.
				success: function(res, status, xhr) { window.location.reload(); },
				error: function(xhr, status, err) { alert('a=' + arguments.callee.caller.caller.caller); alert("Logout failure: " + err); }
			});
		}
	});
}

