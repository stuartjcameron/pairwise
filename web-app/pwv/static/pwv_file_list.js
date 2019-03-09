/*
	PWV app file list screen
*/

console.log('starting pwv_file_list.js')

click('#deleteFileList').then(deleteFileList);

function deleteFileList(data) {
	console.log('deleting file list');
	get('/pwva/delete_file_list', {id: fromServer.id}).then(handleResult, standardFail);
}

function handleResult(data) {
	console.log('got result ok', data.response);
	if (data.response.deleted) {
		redirectWithMessage('/pwva', "The file list was deleted.");
	} else {
		showMessage("This file list could not be deleted because it is in use in one or more rounds.");
	}
}
