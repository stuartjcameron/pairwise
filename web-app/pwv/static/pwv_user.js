// 1. build table of rounds that user is a judge in
// 2. build drop down for rounds that user is not a judge in
// 3. if round selected from drop down: remove drom drop down, add to table
// 4. if remove is selected from a table row, remove from table and add to dropdown
// 5. if save changes, save name if different, email if different, and list of round IDs if they are different

makeTableAndDropdown();
var edits = {name: false, email: false, rounds: false, admin: false}, adminStatus = fromServer.account.admin;
click('#editName').then(toggleEditName);
click('#editEmail').then(toggleEditEmail);
click('#changeAdmin').then(toggleAdmin);
click('#submit').then(submit);
click('#deleteUser').then(deleteUser);

function deleteUser() {
	showMessage("Are you sure you want to delete this user? All comparisons done by this user will be deleted from the database.", {"Really delete": reallyDeleteUser, "Cancel": hideMessage});
	
}

function reallyDeleteUser() {
	get('/pwva/delete_user/' + fromServer.accountId).then(userDeleted, standardFail);
}

function userDeleted() {
	redirectWithMessage('/pwva', "User was deleted");
}

function makeTableAndDropdown() {
	var table = M('table', {id: 'roundsIn'}),
		select = M('select', {name: 'roundsOut', id: 'roundsOutSelect'}),
		countIn = 0,
		countOut = 0,
		rounds = fromServer.rounds,
		i, addUserButton;
	
	tableHeader(table);
	for (i = 0; i < rounds.length; i++) {
		if (rounds[i].judges.indexOf(fromServer.accountId) > -1) {
			addToTable(table, rounds[i]);
			countIn++;
		}
		else {
			append(select, M('option', {value: rounds[i].id}, rounds[i].name));
			// append(select, {tag: 'option', value: rounds[i].id, html: rounds[i].name});
			countOut++;
		}
	}
	empty(E('rounds'));
	
	if (countIn) {
		append('#rounds', [M('h2', "Rounds this user is included in"), table]);
		//append('#rounds', [{tag: 'h2', html: "Rounds this user is included in"}, table]);		
	}
	if (countOut) {
		addUserButton = M('button', 'Add to round'); // make({tag: 'button', html: "Add to round"});
		click(addUserButton).then(addToSelectedRound);
		append('#rounds', [
			M('h2', 'Add this user to a round'),
			select,
			addUserButton]);
	}
}

function tableHeader(table) {
	// --- Add the table header
	append(table, {tr: [{th: 'Name'}, {th: 'Created'}, {th: 'Number of comparisons'}, {th: 'Open'}, {th: null}]});
	
	
	/*append(table, [
		M('th', 'Name'),
		M('th', 'Created'),
		M('th', 'Number of comparisons'),
		M('th', 'Open'),
		M('th')
	]);
	append(table, {tag: 'tr', c: [
		{tag: 'th', html: "Name"},
		{tag: 'th', html: "Created"},
		{tag: 'th', html: "Number of comparisons"},
		{tag: 'th', html: "Open"},
		{tag: 'th'}]
		});		
		*/
}
	
function addToTable(table, r) {
	//--- Add the round as a row in the table
	var removeButton = M('button', "Remove");
	click(removeButton).then(remove);
	append(table, {tr: [{td: r.name}, {td: r.created}, {td: r.comparisons}, {td: (r.opened ? 'Yes' : 'No')}, {td: removeButton}]});
	
	
	/*append(table, {tag: 'tr', c: [
		{tag: 'td', html: r.name},
		{tag: 'td', html: r.created},
		{tag: 'td', html: r.comparisons},
		{tag: 'td', html: (r.opened ? 'Yes' : 'No')},
		{tag: 'td', c: removeButton}]});
	*/
	function remove() {
		removeJudgeFrom(r);
	}
}


function addToSelectedRound() {
	r = getRoundById(parseInt(E('roundsOutSelect').value));
	addJudgeTo(r);
}


function getRoundById(id) {
	var i, rounds = fromServer.rounds;
	for (i = 0; i < rounds.length; i++) {
		console.log('comparing', id, rounds[i]);
		if (id === rounds[i].id) {
			return rounds[i];
		}
	}
}
function toggleAdmin() {
	console.log('toggle admin');
	adminStatus = !adminStatus;
	edits.admin = true;
	set('#adminStatus', adminStatus ? 'Yes' : 'No');	
}	
	
function toggleEditName() {
	console.log('toggle editing name');
	var input;
	if (edits.name) {
		set('#accountName', fromServer.account.name);
		set('#editName', 'Edit');
		edits.name = false;
	}
	else {
		input = M('input', {type: 'text', value: fromServer.account.name});
		set('#accountName', {c: input});
		input.focus();
		input.select();
		set('#editName', 'Revert');
		edits.name = true;
	}
}


function toggleEditEmail() {
	var input;
	console.log('toggle editing email');
	if (edits.email) {
		set('#accountEmail', fromServer.account.email);
		set('#editEmail', 'Edit');
		edits.email = false;
	} else {
		input = M('input', {type: 'text', value: fromServer.account.email});
		set('#accountEmail', input);
		input.focus();
		input.select();
		set('#editEmail', 'Revert');
		edits.email = true;	
	}
}


function removeJudgeFrom(r) {
	//--- Remove judge from round r and update table and dropdown
	console.log('removing judge to round', r);
	var i = r.judges.indexOf(fromServer.accountId);
	r.judges.splice(i, 1);
	makeTableAndDropdown();
	edits.rounds = true;
}

function addJudgeTo(r) {
	//--- Add judge to round r and update table and dropdown
	console.log('adding judge to round', r);
	r.judges.push(fromServer.accountId);
	makeTableAndDropdown();
	edits.rounds = true;
}

function submit() {
	var dataToSubmit = {}, newName, newEmail;
	if (edits.name) {
		newName = Q('#accountName input').value;
		console.log('submitting new name', newName);
		if (newName != fromServer.account.name) {
			if (validName(newName)) {
				dataToSubmit.name = newName;
			}
			else {
				return;
			}
		}
	}
	if (edits.email) {
		console.log('submitting new email');
		newEmail = Q('#accountEmail input').value;
		if (newEmail != fromServer.account.email) {
			if (validEmail(newEmail)) {
				dataToSubmit.email = newEmail;
			}
			else {
				return;
			}
		}
	}
	if (edits.rounds) {
		console.log('submitting new rounds information');
		dataToSubmit.rounds = getRoundsUserIsIn();
	}
	if (edits.admin && adminStatus != fromServer.account.admin) {
		console.log('submitting new admin status');
		dataToSubmit.admin = adminStatus;
	}
	if (dataToSubmit.name || dataToSubmit.email || dataToSubmit.rounds || (dataToSubmit.admin !== undefined)) {
		post('/pwva/edit_user/' + fromServer.accountId, dataToSubmit).then(succeeded, standardFail);
	}
	else {
		showMessage("You have not actually changed anything.");
		return;
	}
}

function succeeded(data) {
	showMessage("The user information was updated successfully");
	if (edits.name) {
		fromServer.account.name = data.parameters.name;
		toggleEditName();		
	}
	if (edits.email) {
		fromServer.account.email = data.parameters.email;
		toggleEditEmail();
	}
	if (edits.admin) {
		fromServer.account.admin = adminStatus;
	}
	edits = {};
}

function validName(name) {
	if (name == "") {
		showMessage("The new user name you have entered is not valid.");
	}
	else if (fromServer.userNames.indexOf(name) > -1) {
		showMessage("The new user name you have selected is already used.");
	}
	else {
		return true;
	}	
}

function validEmail(email) {
	if (email == "" || !okayLookingEmail(email)) {
		showMessage("The new email address you have entered is not valid.");
	}
	else if (fromServer.userEmails.indexOf(email) > -1) {
		showMessage("The new email you have selected is already used.");
	}
	else {
		return true;
	}
}

function getRoundsUserIsIn() {
	var r = [], rounds = fromServer.rounds, i;
	for (i = 0; i < rounds.length; i++) {
		if (rounds[i].judges.indexOf(fromServer.accountId) > -1) {
			r.push(rounds[i].id);
		}
	}
	return r;
}
