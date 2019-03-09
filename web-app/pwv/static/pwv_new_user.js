/**********
* PWV admin app - new user scripts
************/
console.log('Starting script: pwv_new_user.js');

set('#submit', {disabled: true});
click('#submit').then(submitUser);
listen('#userName', 'input').then(formChange);
listen('#emailAddress', 'input').then(formChange);


function formChange() {
	console.log('form changed');
	if (validateForm()) {
		if (E('submit').disabled == true) {
			set('#submit', {disabled: false});
		}
	}
	else {
		if (E('submit').disabled == false) {
			set('#submit', {disabled: true});
		}
	}	
}


function submitUser() {
	var judges = [], userData;
	userData = {
		name: E('userName').value,
		email: E('emailAddress').value,
		admin: E('admin').checked
	};
	if (validateData(userData)) {
		console.log('submitted new user', userData);
		post("/pwva/add_user", userData).then(succeeded, standardFail)
	}	
}

function validateForm() {
	//--- Initial validation while the user is entering information
	var name = E('userName').value,
		email = E('emailAddress').value;
	return name != "" && email != "" && okayLookingEmail(email);
}

function validateData(data) {
	//--- Further validation when the form is submitted
	if (fromServer.names.indexOf(data.name) > -1) {
		showMessage("The name <strong>" + data.name + "</strong> has already been used.");
		return False;
	}
	if (fromServer.emails.indexOf(data.email) > -1) {
		showMessage("The email <strong>" + data.email + "</strong> is already in the database.");
		return False;
	}
	return true;
}

function succeeded(data) {
	console.log('success', data);
	redirectWithMessage('/pwva', "A new user <strong>" + data.parameters.name + "</strong> was successfully created.");
}




