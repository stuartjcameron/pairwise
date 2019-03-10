/**********
* PWV admin app - new round scripts

NO LONGER USED - DELETE
************/
console.log('Starting script: pwv_new_round.js');


var fileList = null, opened = false;
set('#submit', {disabled: true});
click('#submit').then(submitRound);
listen('#round_name', 'input').then(formChange);
click('#changeOpened').then(changeOpened);
listen('#filelists input', 'change').then(fileListChange);
adjustOpenedControl();

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

function changeOpened() {
	if (opened) {
		opened = false;
		set('#roundOpened', "No");
	} else {
		opened = true;
		set('#roundOpened', "Yes");
	}
}


function fileListChange() {
	fileList = parseInt(Q('input[name="filelist"]:checked').value);
	adjustOpenedControl();
}

function adjustOpenedControl() {
	//fileList = parseInt(Q('input[name="filelist"]:checked').value);
	if (!fileList) {
		opened = false;
		set('#roundOpened', "No");
		set('#changeOpened', {disabled: true});
	} else {
		set('#changeOpened', {disabled: false});
	}
}

function submitRound() {
	var judges = [], roundData, i, 
		userBoxes = QA('.user_checkbox'),
		fileList = parseInt(Q('input[name="filelist"]:checked').value);
	for (i = 0; i < userBoxes.length; i++) {
		if (userBoxes[i].checked) {
			judges.push(userBoxes[i].id);
		}
	}
	roundData = {
		name: E('round_name').value,
		opened: opened,
		fileList: fileList,
		judges: judges
	};
	if (validateData(roundData)) {
		console.log('submitted new round', roundData);
		post("/pairwise/add_round", roundData).then(succeeded, standardFail)
	}
	
}

function validateForm() {
	//--- Initial validation while the user is entering information
	if (E('round_name').value == "") {
		return false;
	}
	return true;	
}

function validateData(data) {
	//--- Further validation when the form is submitted
	if (fromServer.roundNames.indexOf(data.name) > -1) {
		showMessage("The name <strong>" + data.name + "</strong> has already been used.");
		return False;
	}
	return true;
}

function succeeded(data) {
	console.log('success', data);
	redirectWithMessage('/pairwise', "A new round <strong>" + data.parameters.name + "</strong> was successfully created.");
}

