//--- Pairwise comparisons: Script for Output page

/*TODO
 * / Function to delete options from local storage - accessed via console only for safety...
 * / Error log
 * 
 */
initStoredComparisons();
writeComparisons();
initButtons();



function onSaved() {
	writeComparisons();
}

function onSaveError() {
	writeComparisons();	
}
function onAllSaved() {
	showMessage("Saved successfully", {'Okay': hideMessage});
	E('save-to-server').disabled = 'disabled';
}

function onFinishedWithErrors() {
	showMessage('Unable to save data to the server. Errors: <span class="error">' + getErrors() + '</span>', 
			{'Retry': saveToServer, 'Close': hideMessage});
}

function initButtons() {
	if (admin) {
		E('serverButtons').appendChild(makeButton("Output to CSV", serverToCsv));		
		// E('serverToCsv')) {	// This only appears if logged in as admin
		// E('serverToCsv').addEventListener('click', serverToCsv);		
		E('change-round').appendChild(makeButton("Submit", submitChangeRound, "submit-change-round"));
		E('submit-change-round').disabled = "disabled";
		E('round-field').addEventListener('input', allowChangeRound);
	}
	E('local-buttons').appendChild(makeButton("Save to server", saveToServer, "save-to-server"));
	E('local-buttons').appendChild(makeButton("Output to CSV", localToCsv));

	if (getSavingStatus() === 'finished') {
		E('save-to-server').disabled = 'disabled';
	}
}
function getEnteredRound() {
	return parseInt(E('round-field').value);
}

function allowChangeRound() {
	//--- User types different round into field, so allow to submit change
	var r = getEnteredRound();
	console.log('current round', round, 'new round', r);
	if (r != round && !isNaN(r)) {
		E('submit-change-round').disabled = '';
	} else {
		E('submit-change-round').disabled = 'disabled';
	}
}

function submitChangeRound() {
	var r = getEnteredRound();
	function onStateChange() {
		if (request.readyState == 4) {
			if (request.status == 200) {
				showMessage("Round changed to " + r, {'Okay': hideMessage});
				round = r;
				E('submit-change-round').disabled = 'disabled';
			} else {
				showMessage("Unable to change round", {'Retry': submitChangeRound, 'Cancel': hideMessage});
			}
		}
	}
	console.log('Changing round to', r);
	request = asyncRequest("/pairwise/set?round=" + r);
	request.onreadystatechange = onStateChange;
}
function getFileName() {
	return parseInt(Math.random() * 100000) + '.csv';
}

function serverToCsv() {
	var data = tableToArr(E('serverComparisons')),
		filename = getFileName();
	exportToCsv(filename, data);	
}

function localToCsv() {
	var data = tableToArr(E('localComparisons')),
		filename = getFileName();
	exportToCsv(filename, data);
}

function writeComparisons() {
	// --- Write the comparisons in local storage to a table
	var i, syncStatus, table = document.createElement('table'), container = E('local_comparisons'), c;
	addRow(table, ["Judge", "Round", "Comparison number", "Left", "Right", "Result", "Shown time", "Choice time", "Saved to server"], 'th');
	for (i = 0; i < comparisons.length; i++) {
		c = comparisons[i];
		if (c.choiceTime) {
			choiceTime = (new Date(c.choiceTime)).toUTCString()
		} else {
			choiceTime = 'not yet chosen';
		}
		if (c.syncStatus == SYNC_ERROR) {
			syncStatus = '<span class="moreinfo" title="' + c.errorType + ': ' + c.errorMessage + '">' + c.syncStatus + '</span>'; 
		} else {
			syncStatus = c.syncStatus;
		}
		addRow(table, [c.judge, c.round, i + 1, c.left, c.right, c.result, (new Date(c.shownTime)).toUTCString(), choiceTime, syncStatus]);
	}
	container.innerHTML = '';
	table.id = "localComparisons";
	container.appendChild(table);
}

function tableToArr(table) {
	//--- Convert HTML table content into an array of arrays
	var tr = table.getElementsByTagName('tr'), r = [], row, i, j, cells;
	for (i = 0; i < tr.length; i++) {
		cells = tr[i].children;
		row = [];
		for (j = 0; j < cells.length; j++) {
			row.push(cells[j].innerHTML)
		}
		r.push(row);
	}
	return r;
}

function exportToCsv(filename, rows) {
    var processRow = function (row) {
        var finalVal = '';
        for (var j = 0; j < row.length; j++) {
            var innerValue = row[j] === null ? '' : row[j].toString();
            if (row[j] instanceof Date) {
                innerValue = row[j].toLocaleString();
            }
            var result = innerValue.replace(/"/g, '""');
            if (result.search(/("|,|\n)/g) >= 0)
                result = '"' + result + '"';
            if (j > 0)
                finalVal += ',';
            finalVal += result;
        }
        return finalVal + '\n';
    };

    var csvFile = '';
    for (var i = 0; i < rows.length; i++) {
        csvFile += processRow(rows[i]);
    }

    var blob = new Blob([csvFile], { type: 'text/csv;charset=utf-8;' });
    if (navigator.msSaveBlob) { // IE 10+
        navigator.msSaveBlob(blob, filename);
    } else {
        var link = document.createElement("a");
        if (link.download !== undefined) { // feature detection
            // Browsers that support HTML5 download attribute
            var url = URL.createObjectURL(blob);
            link.setAttribute("href", url);
            link.setAttribute("download", filename);
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    }
}

//TODO check sync status of locally stored comparisons by checking id or judge + showntime
//TODO check save function works ok