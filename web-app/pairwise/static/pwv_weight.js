/*
script for pairwise/new_weight and pairwise_weight
*/

console.log('starting pwv_weight.js');

var fileLists = {1: fromServer.weight.left.slice(), 2: fromServer.weight.right.slice()},
	roundPage = '/pairwise/round/' + fromServer.round.id;

click('#submit').then(submit);
click('#cancel').then(cancel);
if (E('delete')) {
	click('#delete').then(deleteWeight);
}
click('#reset').then(reset);
click('#revert1').then(revert, {side: 1});
click('#revert2').then(revert, {side: 2});
click('#apply-filter1').then(applyFilter, {side: 1});
click('#apply-filter2').then(applyFilter, {side: 2});
listen('#file-list1', 'input').then(getFileList, {side: 1});
listen('#file-list2', 'input').then(getFileList, {side: 2});

function revert(data) {
//--- Revert the file list on the specified side to the full list associated with this round
	fileLists[data.side] = fromServer.fileList;
	E('filter1').value = '';
	E('filter2').value = '';
	update();
}

function submit() {
	var left_ok, right_ok;
	console.log('submit');
	getFileList({side: 1});
	getFileList({side: 2});
	left_ok = checkFileList(1);
	right_ok = checkFileList(2);
	if (!left_ok && !right_ok) {
    	showMessage("Neither file list is valid. Please edit both.")
    } else if (!left_ok) {
        showMessage("The left file list is not valid. Please edit and try again.")
    } else if (!right_ok) {
        showMessage("The right file list is not valid. Please edit and try again.")
    } else {
        post('/pairwise/edit_weight', {
    		weightId: fromServer.id,
    		roundId: fromServer.round.id,
    		left: fileLists[1],
    		right: fileLists[2],
    		weight: E('weightWeight').value,
    		name: E('weightName').value
    	}).then(succeeded, standardFail);
    }
}
	
	
function getFileList(data) {
	//--- Read file lists from textareas in case they have changed manually
	var i, content;
	console.log('reading file lists on side', data.side);
	content = E('file-list' + data.side).value.trim().split(/[\n,;]+/);
	for (i = 0; i < content.length; i++) {
		content[i] = content[i].trim();
	}
	fileLists[data.side] = content;
	updateLengths();
}

function checkFileList(side) {
    //--- Check whether files in given file list are all in server.fileList
    var i;
    for (i = 0; i < fileLists[side].length; i++) {
        if (server.fileList.indexOf(fileLists[side][i]) == -1) {
            return false;
        }
    }
    return true;
}

function succeeded(data) {
	console.log('succeeded', data);
	redirectWithMessage(roundPage, "The weighting scheme <strong>" + data.parameters.name + "</strong> was saved successfully.");
}

function reset() {
	//--- Reset file lists, name, weight, to values from server and blank filters
	console.log('reset');
	fileLists = {1: fromServer.weight.left.slice(), 2: fromServer.weight.right.slice()};
	E('weightName').value = fromServer.weight.name;
	E('weightWeight').value = fromServer.weight.weight;
	E('filter1').value = '';
	E('filter2').value = '';
	update();
}

function update() {
	//--- Update file lists display
	E('file-list1').value = fileLists[1].join('\n');
	E('file-list2').value = fileLists[2].join('\n');
	updateLengths();
}

function updateLengths() {
	set('#nfiles1', fileLists[1].length);
	set('#nfiles2', fileLists[2].length);
}

function cancel() {
	console.log('cancel');
	if (fromServer.newWeight) {
		//--- If the weight is new, then cancel also deletes it
		get('/pairwise/delete_weight', {round: fromServer.round.id, weight: fromServer.id}).then(goBack, standardFail);
	} else {
		//--- If the weight is not new, simply return to the round page without saving anything
		goBack();
	}
}
function goBack() {
	//--- Return to round page
	window.location.href = roundPage;
}

function deleteWeight() {
	//--- Delete weight button only appears if the weight is not new
	console.log('delete');
	showMessage("Are you sure you want to delete this weighting? Comparisons using it will not be deleted.",
		{"Really delete": reallyDelete, "Cancel": hideMessage});
}

function reallyDelete() {
	get('/pairwise/delete_weight', {round: fromServer.round.id, weight: fromServer.id}).then(weightDeleted, standardFail);
}

function weightDeleted() {
	redirectWithMessage(roundPage, "Weighting <strong>" + fromServer.weight.name + "</strong> was deleted");
}

function applyFilter(data) {
	var side = data.side,
		filter = E('filter' + side).value;
	console.log('apply filter', data, filter);
	regex = globStringToRegex(filter);
	fileLists[side] = fileLists[side].filter(function(s) { return s.match(regex)});
	update();
}

// Regex functions from https://stackoverflow.com/a/13818704/567595
function globStringToRegex(str) {
    return new RegExp(preg_quote(str).replace(/\\\*/g, '.*').replace(/\\\?/g, '.'), 'g');
}
function preg_quote (str, delimiter) {
    // http://kevin.vanzonneveld.net
    // +   original by: booeyOH
    // +   improved by: Ates Goral (http://magnetiq.com)
    // +   improved by: Kevin van Zonneveld (http://kevin.vanzonneveld.net)
    // +   bugfixed by: Onno Marsman
    // +   improved by: Brett Zamir (http://brett-zamir.me)
    // *     example 1: preg_quote("$40");
    // *     returns 1: '\$40'
    // *     example 2: preg_quote("*RRRING* Hello?");
    // *     returns 2: '\*RRRING\* Hello\?'
    // *     example 3: preg_quote("\\.+*?[^]$(){}=!<>|:");
    // *     returns 3: '\\\.\+\*\?\[\^\]\$\(\)\{\}\=\!\<\>\|\:'
    return (str + '').replace(new RegExp('[.\\\\+*?\\[\\^\\]$(){}=!<>|:\\' + (delimiter || '') + '-]', 'g'), '\\$&');
}
