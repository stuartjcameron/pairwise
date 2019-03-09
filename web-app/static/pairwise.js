var comparison = {}, sumWeights = 0, originalWeights = weights;
// Note: page, judge, round, weights need to be defined outside of this file

initWeights();
console.log('init sync status', getSyncStatus());
initStoredComparisons();
initListeners();
console.log('then sync status', getSyncStatus());
if (saveToServer() === 0) { // If anything is still syncing or has error in local storage, try to save to server.
	getNewFiles();		// If nothing to save then get new files straight away (otherwise this will be called
						// in onAllSaved
	enableForm();
}
//TODO: time out mechanism (it times out eventually anyway?)

function initWeights() {
	console.log('Initiating weights ', weights);
	var i;
	weights = [];
	for (i = 0; i < originalWeights.length; i++) {
		if (!hasZeroWeight(originalWeights[i][0], originalWeights[i][1])) {
			weights.push(originalWeights[i]);
			sumWeights += originalWeights[i][2];
		}
	}
	console.log('Number of pairs', weights.length, 'Sum of weights: ', sumWeights);
	
	//TODO: call this function again if round changes [for now, just tell everyone to refresh if round changes]
}

function removePairFromWeights(folder1, folder2) {
	//--- Remove the pair folder1, folder2 from the weights. Assuming weights contains no duplicates.
	var i;
	console.log('removing pair', folder1, folder2, 'from weights');
	console.log('current weights: length', weights.length, 'sum', sumWeights)
	for (i = 0; i < weights.length; i++) {
		if (weights[i][0] == folder1 && weights[i][1] == folder2) {
			sumWeights -= weights[i][2];
			weights.splice(i, 1);
			console.log('new weights: length', weights.length, 'sum', sumWeights)
			return;
		}
	}
	return false;		// pair not found
}

function removePairsFromWeights(arr) {
	// --- Remove all listed pairs from weights
	var i; 
	for (i = 0; i < arr.length; i++) {
		removePairFromWeights(arr[i][0], arr[i][1]);
	}
}

function onSaved(obj) {
	// --- A comparison has finished saving. Handle feedback from the server after saving 
	console.log('feedback from server:', obj);
	if (obj.judgedTwice && obj.judgedTwice.length) {
		removePairsFromWeights(obj.judgedTwice)
	}
}

function onAllSaved(obj) {
	// --- All comparisons have finished saving successfully
	console.log('all saved!')
	getNewFiles();
	hideMessage();
	enableForm();
}

function onFinishedWithErrors() {
	if (admin) {		
		showMessage('Unable to synchronise with the server', 
			{'Retry': saveToServer, 'View output': "/pairwise/output"});
	} else {
		showMessage('Unable to synchronise with the server', 
			{'Retry': saveToServer, 'Sign in admin and fix': logoutOutput});
	}
}

function hasZeroWeight(folder1, folder2) {
	// --- Check if a pair should have zero weight because it's already been judged once by the current judge
	// Note, some pairs should have zero weight because already seen twice by other judges. These should have already been removed from the weights
	
	var i;
	for (i = 0; i < comparisons.length; i++) {
		if (comparisons[i].judge == judge && comparisons[i].round == round 
				&& comparisons[i].folder1 == folder1 && comparisons[i].folder2 == folder2
				&& comparisons[i].choiceTime !== undefined) {
			return true;
		}
	}
	return false;
}

function initListeners() {
	E('chooseLeft').addEventListener('change', toggleSubmit);		
	E('chooseRight').addEventListener('change', toggleSubmit);
	E('submitButton').addEventListener('click', submitChoice);	
}

function getSeenPairs() {
	// --- Return a list of pairs already seen by the current user in the current round
	// [Not currently used - can remove]
	var i, r = [];
	for (i = 0; i < comparisons.length; i++) {
		if (comparisons[i].judge == judge && comparisons[i].round == round) {
			r.push([comparisons[i].folder1, comparisons[i].folder2]);
		}
	}
	console.log('pairs already seen', r);
	return r;
}

function toggleSubmit() {
	if(E('chooseLeft').checked || E('chooseRight').checked) {
		E('submitButton').disabled = false;
	}
	else {
		E('submitButton').disabled = true;
	}
}

function clearForm() {
	E('chooseLeft').checked = false;
	E('chooseRight').checked = false;
}

function disableForm() {
	E('chooseLeft').disabled = true;
	E('chooseRight').disabled = true;
	E('submitButton').disabled = true;
}

function enableForm() {
	console.log('enabling form now');
	E('chooseLeft').disabled = false;
	E('chooseRight').disabled = false;
}

function getNewFiles() {
	var t;
	console.log('getting new files');
	
	// Check if there is an incomplete comparison in the array. If so, pick the last incomplete comparison and go back to it.
	// If not, choose a new comparison.
	comparison = checkIncompleteComparison();
	
	if (comparison == undefined) {
		comparison = chooseNextFiles();
		comparisons.push(comparison);
		comparison.comparisonNumber = comparisons.length;	// assuming we can't delete comparisons!
		comparison.shownTime = new Date();
		comparison.id = comparison.shownTime.getTime() * 1000 + judge;
	}
	clearForm();
	if (compressed) {
		E('leftPdf').data = '/cpapers/' + comparison.left;
		E('rightPdf').data = '/cpapers/' + comparison.right;
	} else {
		E('leftPdf').data = '/papers/' + comparison.left;
		E('rightPdf').data = '/papers/' + comparison.right;
	}
	
	comparison.round = round;
	comparison.judge = judge;
	comparison.syncStatus = SYNC_NOT_STARTED;
	saveToLocalStorage();
	//t = setTimeout(enableForm, 3000);		// Form only available after 3s
}

function checkIncompleteComparison() {
	//--- Return the most recent incomplete comparison for the current judge and round
	//comparisons = getFromLocalStorage();
	for (var i = comparisons.length - 1; i >= 0; i--) {
		if (comparisons[i].judge == judge && comparisons[i].result == undefined && comparisons[i].round == round) {
			// New 24.9.2017: check if the comparison is in the weights before sending
			// This is to prevent an old comparison being presented when the weights file has changed
			// and no longer contains the specified folders.
			if (comparisonIsInWeights(comparisons[i])) {
				return comparisons[i];
			}
		}
	}
}

function comparisonIsInWeights(comparison) {
	console.log('checking', comparison, 'in weights', weights.length);
	for (var i = 0; i < weights.length; i++) {
		if (weights[i][0] == comparison.folder1 && weights[i][1] == comparison.folder2) {
			console.log("This comparison has weight " + weights[i][2]);
			return true;
		}
	}
	console.log('Comparison', comparison.left, comparison.right, comparison.index, "not in weights");
	return false;	
}

function choosePair() {
	var r = Math.random() * sumWeights,
		runningTotal = 0;
	console.log('random', r, 'sumWeights', sumWeights)
	for (var i = 0; i < weights.length; i++) {
		runningTotal += weights[i][2];	
		if (r < runningTotal) {
			console.log('choosing pair', i);
			return i;
		}
	}
}

function chooseNextFiles() {
	var index = choosePair(), pair = weights[index];
	if (Math.random() >= .5) {
		return {folder1: pair[0], folder2: pair[1], left: pair[0], right: pair[1], index: index};
	} else {
		return {folder1: pair[0], folder2: pair[1], left: pair[1], right: pair[0], index: index};
	}
}

function submitChoice() {
	var query, saveRequest;
	comparison.result = E('choiceForm').pairChoice.value;
	comparison.choiceTime = new Date();
	removePairFromWeights(comparison.folder1, comparison.folder2);
	saveToLocalStorage();
	disableForm();
	saveToServer();
	//TODO show message / icon that data is being saved to server
}

function updateSavingIcon() {
	// --- Check whether saving anything and update icon [not currently used]
	var status = getSavingStatus();
	if (status == 'saving') {
		console.log('STILL SAVING');
	} else if (status == 'finished') {
		console.log('ALL SAVED');
	} else {
		console.log('NOT STARTED SAVING');
	}
}
