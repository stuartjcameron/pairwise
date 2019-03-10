/*
script for pwv/round 
*/

console.log('starting pwv_round.js');


click('#submit').then(submit);

function submit() {
	var dataToSubmit = {}, content, i;
	dataToSubmit.description = E('descriptionInput').value;
	dataToSubmit.file_type = parseInt(Q('input[name="filetype"]:checked').value; 		
	content = E('contentInput').value.trim().split(/[\n,;]+/);
	for (i = 0; i < content.length; i++) {
		content[i] = content[i].trim();
	}
	console.log('file list:', content);
	dataToSubmit.file_list = content;
	post('/pairwise/add_file_list2', dataToSubmit).then(succeeded, standardFail);
}

function succeeded(data) {
	showMessage("The file list was uploaded successfully");
	console.log('succeeded', data);
}
