var SYNC_SAVING = 'synchronising', SYNC_DONE = 'synchronised', SYNC_ERROR = 'error', SYNC_UNSURE = 'unsure', SYNC_NOT_STARTED = 'not started';
// var SYNC = {SYNC_SAVING: 'saving', SYNC_DONE: 'done', SYNC_ERROR: 'error', SYNC_UNSURE: 'unsure', SYNC_NOT_STARTED: 'not started'};
var comparisons = getFromLocalStorage()

//var SYNC_SAVING = 1, SYNC_DONE = 2, SYNC_ERROR = 3, SYNC_UNSURE = 4, SYNC_NOT_STARTED = 5,
//	SYNC = {1: 'saving', 2: 'done', 3: 'error', 4: 'unsure', 5: 'not started'};
	


function onSaved() {}			// Placeholders for functions defined in pairwise.js and pairwise_output.js
function onAllSaved() {}	
function onSaveError() {}
function onFinishedWithErrors() {}


/* TODO
 * Refresh or change page during synchronisation => not clear if synchronised or not.
 * When loading page, need to check these:
 * Go through comparisons from local storage
 * If status is 'synchronising', change to 'unsure'
 * 
 * Then try to save all
 * If status is 'error' attempt to resave
 * Show saving error message if any problems: There is data on this computer that has not been saved.
 * On the server side, this checks for an existing entry with matching ID first
 * (Later we can add error checking: server raises an error if entry is saved with different data, as 
 * the data is not supposed to change.)
 * 
 * 
 * 
 */


function E(id) {
	return document.getElementById(id);
}

function getFromLocalStorage() {
	if (localStorage['comparisons']) {
		return JSON.parse(localStorage['comparisons']);
	}
	return [];
}

function clearLocalStorage() {
	localStorage.comparisons = JSON.stringify([]);
	comparisons = [];
}

function saveToLocalStorage() {
	localStorage.comparisons = JSON.stringify(comparisons);
}

function removeErrorsFromLocalStorage() {
	//--- Remove cases that could not be saved to local storage due to an error
	var i, c2 = [];
	for (i = 0; i < comparisons.length; i++) {
		if (comparisons[i].syncStatus !== SYNC_ERROR) {
			c2.push(comparisons[i]);
		}
	}
	console.log((comparisons.length - c2.length), "errors were removed.", c2.length, "comparisons remain.");
	comparisons = c2;
	saveToLocalStorage();
}

function getErrors() {
	//--- Get an HTML list of the errors
	var i, r = '', c;
	for (i = 0; i < comparisons.length; i++) {
		c = comparisons[i];
		if (c.syncStatus === SYNC_ERROR) {
			r = r + "<br />Judge " + c.judge + ", round " + c.round + ", number " + c.comparisonNumber
				+ ". Error " + c.errorType + ': ' + c.errorMessage;
		}
	}
	return r;
}

function initStoredComparisons() {
	//--- For locally stored comparisons, change status from 'saving' to 'unsure',
	// when page is first loaded, as we don't know if these were actually synchronised or not
	var i;
	for (i = 0; i < comparisons.length; i++) {
		if (comparisons[i].syncStatus === SYNC_SAVING) {
			comparisons[i].syncStatus = SYNC_UNSURE;
		}
	}
}
function saveToServer() {
	//--- Save all locally stored comparisons to the server
	var saved = 0, s;
	for(var i = 0; i < comparisons.length; i++) {
		if (comparisons[i].result !== undefined) {
			s = comparisons[i].syncStatus;
			if (s === SYNC_NOT_STARTED || s === SYNC_ERROR) {
				saveItem(comparisons[i]);
				saved++;
			}
			else if (s === SYNC_UNSURE) {	
				console.log('Trying to resave comparison', i, comparisons[i]);
				saveItem(comparisons[i], true);
				saved++;
			}
		}
	}
	return saved;
}

function getSyncStatus() {
	var r = '', i;
	for(i = 0; i < comparisons.length; i++) {
		r += i + '. ' + comparisons[i].syncStatus + ';'
	}
	return r;
}


function getComparisonById(id) {
	for (var i = 0; i < comparisons.length; i++) {
		if (comparisons[i].id == id) {
			return comparisons[i];
		}
	}
}

function saveItem(comp, verify) {
	//--- Synchronise the given comparison with the online DB
	// If verify is true, then the item may already exist on the server, so the server should verify this
	// before saving
	var query, request;
	if (verify) {
		//query = serialise({hi: 'there'}, {verify: true});			// use for error testing
		query = serialise(comp, {verify: true});
		console.log('verifying');
	} else {
		//query = serialise({hi: 'there'});		// use for error testing
		query = serialise(comp);
	}
	//TODO: remove error, syncstatus before saving (but these will be ignored by server anyway)
	console.log('saving: ', comp.result, query);
	showMessage('Saving data to the server');
	request = asyncRequest("/pairwise/add_comparison?" + query);
	comp.syncStatus = SYNC_SAVING;
	comp.save = request;
	saveToLocalStorage();
	request.onreadystatechange = function() {
		var c = getComparisonById(comp.id);		// The comp object reference may have been lost, so retrieve the comparison again from the list
		console.log('comparison save status', request.readyState, request.status, request.responseText);		
		if (request.readyState == 4) {
			if (request.status == 200) {
				console.log('updating sync status for', c);
				c.syncStatus = SYNC_DONE;
				console.log('comparisons now: ', getSyncStatus());
				onSaved(JSON.parse(request.responseText));
				if (onAllSaved && getSavingStatus() == 'finished') {
					onAllSaved(JSON.parse(request.responseText));
				}
			} else {
				console.log('save error for', c);
				c.syncStatus = SYNC_ERROR;
				c.errorType = request.status;
				c.errorMessage = request.responseText;
				if (onSaveError) {
					onSaveError(c.errorType, c.errorMessage);
				}
				if (onFinishedWithErrors && getSavingStatus() == 'finished with errors') {
					onFinishedWithErrors();
				}
			}
			saveToLocalStorage();
		}
	};
}

function getSavingStatus() {
	//--- Check whether comparisons are being saved to server / have finished saving
	var saved = 0, errors = 0;
	console.log('checking saving status');
	for (var i = 0; i < comparisons.length; i++) {
		console.log(i, comparisons[i].syncStatus);
		if (comparisons[i].syncStatus) {
			if (comparisons[i].syncStatus === SYNC_SAVING) {
				console.log('status: saving');
				return 'saving';
			}
			if (comparisons[i].syncStatus === SYNC_ERROR || comparisons[i].syncStatus === SYNC_UNSURE) {
				errors++;
			} else {
				saved++;
			}
		}
	}
	if (saved > 0) {
		if (errors > 0) {
			console.log('status: finished with errors');
			return 'finished with errors';
		} else {
			console.log('status: finished');
			return 'finished';
		}
	} else {
		console.log('status: no comparisons started');
		return 'not started';
	}
}

function addRow(table, arr, cellType) {
	//--- Turn an array of values into a table row and adds it to the specified table
	// Specify cellType = 'th' to get a header row
	var tr = document.createElement('tr'),
		td;
	cellType = cellType || 'td';
	for (var i = 0; i < arr.length; i++) {
		td = document.createElement(cellType);
		td.innerHTML = arr[i];
		tr.appendChild(td);
	}
	table.appendChild(tr);
}

function serialise() {
	//--- Turn an object or series of objects into a URI encoded string for submission
	var r = "", s, k, i, obj
	for (i = 0; i < arguments.length; i++) {
		obj = arguments[i];
		for (k in obj) {
			if (obj.hasOwnProperty(k)) {
				if (r != "") {
					r += "&";
				}
				if (obj[k] instanceof Date) {
					s = obj[k].toJSON()
				} else {
					s = obj[k];
				}
				r += k + "=" + s;
			}
		}
	}
	return r;
}

function getDiv(id, className) {
	// --- Return an existing div or make it if it doesn't exist
	var r = E(id);
	if (!r) {
		r = document.createElement('div');
		r.id = id;
		document.body.appendChild(r);
	}
	r.className = className;
	return r;
}

function makeButton(content, handler, id) {
	// --- Make a button with specified content and click handler;
	// if handler is a url, then provide just a link
	var r;
	if (typeof handler === "function") {
		r = document.createElement('button');
		r.addEventListener('click', handler);
		r.type = 'button';
	} else {
		r = document.createElement('a');
		r.href = handler;
	}
	if (id) {
		r.id = id;
	}
	r.innerHTML = content;
	return r;	
}

function showMessage(messageHtml, buttons) {
	//--- Show a popup message with buttons given as a dictionary in the form {label: handler, ... }
	var div = getDiv('message'), inner = document.createElement('div'), k;
	console.log('Showing message', messageHtml);
	div.style.display = 'block';
	div.innerHTML = '';
	div.appendChild(inner);
	inner.innerHTML = messageHtml;
	for (k in buttons) {
		if (buttons.hasOwnProperty(k)) {
			div.appendChild(makeButton(k, buttons[k]));
		}
	}
}

function hideMessage() {
	getDiv('message').style.display = 'none';
}

function asyncRequest(file) {
	var request = new XMLHttpRequest;
	request.open('get', file, true);
	request.send(null);
	return request;	
}
