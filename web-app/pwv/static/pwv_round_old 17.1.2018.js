/*
script for pwv/round 
*/

console.log('starting pwv_round.js');

var opened = fromServer.round.opened, fileList = fromServer.round.file_list,
	edits = {name: false, opened: false, judges: false, fileList: false};

adjustOpenedControl();	
	
click('#editName').then(toggleEditName);
click('#changeOpened').then(changeOpened);
click('#submit').then(submit);
click('#deleteRound').then(deleteRound);
listen('#selectAllUsers', 'change').then(toggleSelectAllUsers);
listen('#users td input', 'change').then(userChange);
if (E('filelists')) {
	listen('#filelists input', 'change').then(fileListChange);
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

function fileListChange() {
	fileList = parseInt(Q('input[name="filelist"]:checked').value);
	edits.fileList = true;
	adjustOpenedControl();
}
	
	


//click('#selectAllUsers').then(toggleSelectAllUsers);

//TODO: check for change in judges input list

function deleteRound() {
	showMessage("Are you sure you want to delete this round? All comparisons within this round will be deleted from the database.", {"Really delete": reallyDeleteRound, "Cancel": hideMessage});
	
}
function reallyDeleteRound() {
	get('/pwva/delete_round/' + fromServer.roundId).then(roundDeleted, standardFail);
	
	// TODO: allow an undo (round and the comparisons in it are marked for deletion but not actually removed until later)
}

function roundDeleted() {
	redirectWithMessage('/pwva', "Round <strong>" + fromServer.round.name + "</strong> was deleted");
}
	
function toggleEditName() {
	console.log('toggle editing name');
	var input;
	if (edits.name) {
		set('#roundName', fromServer.round.name);
		set('#editName', 'Edit');
		edits.name = false;
	}
	else {
		input = make({tag: 'input', type: 'text', value: fromServer.round.name});
		set('#roundName', input);
		input.focus();
		input.select();
		set('#editName', 'Revert');
		edits.name = true;
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
	edits.opened = true;
}

function getTickedJudges() {
	var tickBoxes = QA("#users td input"), i, r = [], id, changed = false;
	for (i = 0; i < tickBoxes.length; i++) {
		id = parseInt(tickBoxes[i].id);
		if (tickBoxes[i].checked) {
			if (fromServer.round.judges.indexOf(id) == -1) {
				changed = true;
			}
			r.push(parseInt(tickBoxes[i].id));
		} else {
			if (fromServer.round.judges.indexOf(id) > -1) {
				changed = true;
			}			
		}
	}
	if (changed) {
		return r;
	} else {
		return "no change";
	}
}

function userChange(data) {
	console.log('user change', data);
	if (!data.target.checked) {
		set('#selectAllUsers', {checked: false});
	}
	edits.judges = true;
}

function toggleSelectAllUsers() {
	var tickBoxes = QA('#users td input');
	console.log('toggle select all users');
	function allSelected() {
		var i;
		for (i = 0; i < tickBoxes.length; i++) {
			if (!tickBoxes[i].checked) {
				return false;
			}
		}
		return true;
	}
	
	function changeAll(newStatus) {
		var i;
		for (i = 0; i < tickBoxes.length; i++) {
			tickBoxes[i].checked = newStatus;
		}
		edits.judges = true;
	/*
		function changeSelectAllBox() {
			Q('#selectAllUsers').checked = newStatus;
		}
		
		setTimeout(changeSelectAllBox, 10);
		*/	
	}
	
	if (allSelected()) {
		changeAll(false);
	} else {
		changeAll(true);
	}
}

function submit() {
	var dataToSubmit = {}, newName, newJudges;
	if (edits.name) {
		newName = Q('#roundName input').value;
		console.log('submitting new name', newName);
		if (newName != fromServer.round.name) {
			if (validName(newName)) {
				dataToSubmit.name = newName;
			}
			else {
				return;
			}
		}
	}
	
	if (opened != fromServer.round.opened) {
		dataToSubmit.opened = opened;
	}
	
	if (edits.judges) {
		console.log('submitting new judges information');
		newJudges = getTickedJudges();
		if (newJudges != "no change") {
			dataToSubmit.judges = newJudges;
		}
	}
	
	if (edits.fileList && fileList != fromServer.round.fileList) {
		dataToSubmit.fileList = fileList;
	}
	console.log('data to submit', dataToSubmit);
	if (dataToSubmit.name || (dataToSubmit.opened != null) || dataToSubmit.judges ||
			dataToSubmit.fileList) {
		post('/pwva/edit_round/' + fromServer.roundId, dataToSubmit)
			.then(succeeded, standardFail);
	}
	else {
		showMessage("You have not actually changed anything.");
		return;
	}
}

function succeeded(data) {
	showMessage("The round information was updated successfully");
	if (edits.name) {
		fromServer.round.name = data.parameters.name;
		toggleEditName();		
	}
	if (edits.opened) {
		fromServer.round.opened = data.parameters.opened;
	}
	if (edits.judges) {
		fromServer.round.judges = data.parameters.judges;
	}
	if (edits.fileList) {
		fromServer.round.fileList = data.parameters.fileList;
	}
}

function validName(name) {
	if (name == "") {
		showMessage("The new round name you have entered is not valid.");
	}
	else if (fromServer.roundNames.indexOf(name) > -1) {
		showMessage("The new round name you have selected is already used.");
	}
	else {
		return true;
	}	
}

