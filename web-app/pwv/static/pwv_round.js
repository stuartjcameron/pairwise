/*
script for pwva/round 
*/

console.log('starting pwv_round.js');

var opened = fromServer.round.opened, fileList = fromServer.round.file_list,
	edits = {name: false, opened: false, judges: false, fileList: false};


click('#submit').then(submit);
click('#deleteRound').then(deleteRound);
click('#add-weighting').then(addWeighting);
listen('#selectAllUsers', 'change').then(toggleSelectAllUsers);
listen('#users td input', 'change').then(userChange);
listen('#existingRounds', 'change').then(useFilesFromExistingRound);
if (E('filelists')) {
	listen('#filelists input', 'change').then(fileListChange);
};

function addWeighting() {
//--- redirect to add weighting page (need to save settings first..)	
	window.location.href = '/pwva/new_weight?round=' + fromServer.roundId;
}

function getRoundInfoById(id) {
	var i, f = fromServer.roundsInfo;
	for (i = 0; i < f.length; i++) {
		if (f[i].id == id || "round_" + f[i].id == id) {
			return f[i];
		}
	}
}

function useFilesFromExistingRound() {
	var sel = E('existingRounds'),
		roundId = sel.options[sel.selectedIndex].value,
		roundInfo = getRoundInfoById(roundId);
	console.log('use files from existing round', sel, roundId, roundInfo);
	if (roundInfo) {
		E('contentInput').value = roundInfo.file_list.join('\n');	
	} else {
		E('contentInput').value = "";
	}
}

function fileListChange() {
	fileList = parseInt(Q('input[name="filelist"]:checked').value);
	edits.fileList = true;
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
	var dataToSubmit = {}, newName, newJudges, opened, fields = ['max_views', 'max_comparisons', 'max_views_by_user', 'max_comparisons_by_user', 'min_time', 'warn_time'], i, v, fileList;
	
	// Name
	newName = E('roundName').value;
	if (newName != fromServer.round.name) {
		if (validName(newName)) {
			dataToSubmit.name = newName;
		} else {
			showMessage("The name you have entered is not valid or already exists. Please choose another name.");
			return;
		}
	}
	
	// Round opened
	opened = E('roundOpened').checked;
	if (opened != fromServer.round.opened) {
		dataToSubmit.opened = opened;
	}
	
	// Max views and min/warn times
	for (i = 0; i < fields.length; i++) {
		v = parseInt(E(fields[i]).value);
		if (E(fields[i] + '_check').checked && !isNaN(v)) {
			dataToSubmit[fields[i]] = v;
		} else {
			dataToSubmit[fields[i]] = null;
		}
	}
	
	// Judges
	if (edits.judges) {
		console.log('submitting new judges information');
		newJudges = getTickedJudges();
		if (newJudges != "no change") {
			dataToSubmit.judges = newJudges;
		}
	}
	/*
	if (E('filelists')) {
		fileList = parseInt(Q('input[name="filelist"]:checked').value)
		if (edits.fileList && fileList != fromServer.round.fileList) {
			dataToSubmit.fileList = fileList;
		}
	}*/
	if (E('contentInput')) {
		fileList = E('contentInput').value.trim().split(/[\n,;]+/);
		for (i = 0; i < fileList.length; i++) {
			fileList[i] = fileList[i].trim()
		}
		if (!sameLists(fileList, fromServer.fileList)) {
			dataToSubmit.fileList = fileList;
		}
	}
		
	console.log('data to submit', dataToSubmit);
	post('/pwva/edit_round/' + fromServer.roundId, dataToSubmit)
			.then(succeeded, standardFail);
}
function sameLists(a, b) {
	//--- Checks if a and b have equal contents (shallow)
	// note this sorts the 2 lists in place.
	var i;
	if ((!a && b) || (a && !b) || a.length != b.length) {
		return false;	// lists of different length, or e.g. one of them is null rather than a list
	}
	a.sort();
	b.sort();	
	for (i = 0; i < a.length; i++) {
		if (a[i] !== b[i]) {
			return false;
		}
	}
	return true;	
}


function succeeded(data) {
	showMessage("The round information was updated successfully");
	console.log('succeeded', data);
	fromServer.round = data.response.newRoundInfo;
}

function roundNameExists(name) {
	for (i = 0; i < fromServer.roundsInfo.length; i++) {
		if (fromServer.roundsInfo[i].name == name) {
			return true;
		}
	}
	return false;
}

function validName(name) {
	
	if (name == "") {
		showMessage("The new round name you have entered is not valid.");
	}
	else if (roundNameExists(name)) {
		showMessage("The new round name you have selected is already used.");
	}
	else {
		return true;
	}	
}

