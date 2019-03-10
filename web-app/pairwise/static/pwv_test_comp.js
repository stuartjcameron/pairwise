/*
	PWV app test comparison scripts
*/

console.log('starting pwv_test_comp.js')

click('.selectRound').then(selectRound);

function selectRound(data) {
	var r = parseInt(data.target.id);
	console.log('selected round', r);
	generateComparison(r);
	
}

function generateComparison(r) {
	console.log('generating comparison', r);
	get('add_comparison_admin', {round: r, test: true}).then(showResult, standardFail);
}

function showResult(request) {
	console.log('showing result', request);
	if (request.response == null) {
		append('#result', "It was not possible to generate a new test case because of the exclusion rules on this round.<br /><br />");
	} else {
		append('#result', "A test case was generated with left " + request.response.left + ", right " + request.response.right + ".");
		console.log('waiting to post...');
		post('complete_comparison_admin', {
			comparison: request.response.comparisonId,
			round: request.parameters.round,
			choice: parseInt(Math.random() * 2) + 1
		}).then(showCompleted, standardFail);
	}
}



function showCompleted(request) {
	append('#result', [
		"<br />The test case was completed with result ", 
		{'strong': request.response.choice == 1 ? "left" : "right"}, 
		"<br />Go back to the ", {a: "home screen", href: "/pairwise"}, " to view the table of comparisons.<br /><br />"]);
}
