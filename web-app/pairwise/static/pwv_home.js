/**********
* PWV admin app - home page scripts
************/

click("#remove_test_comps").then(removeTestComps);
addTodaysWorkLink();


if (E('comparisonsControl')) {
	tableControl('#comparisonsControl', makeComparisonsTable, 'pairwise/get_comparisons', fromServer.comparisonsCount);
}

function removeTestComps() {
	get("/pairwise/remove_test_comps").then(succeeded, standardFail)
}
function succeeded(data) {
	console.log('succeeded in removing test comps', data);
	redirectWithMessage("/pairwise", "Test comparisons have been deleted from the database.");
}
function makeComparisonsTable(comparisons) {
	var table = E('comparisons'), html, i, c;
	console.log('making the table with this data:', comparisons);
	html = "<tr><th>Judge</th><th>Round</th><th>Left</th><th>Right</th><th>Result</th><th>Shown time</th><th>Choice time</th></tr>";
	for (i = 0; i < comparisons.length; i++) {
		c = comparisons[i];
		console.log('makeComparisonsTable: adding', i, c);
		html += "<tr><td>" + c.judge + "</td><td>" + c.round + "</td><td>" + c.left + "</td><td>" + c.right + "</td><td>"
			+c.result + "</td><td>" + c.created + "</td><td>" + c.completed + "</td></tr>"
	}
	table.innerHTML = html;
	
}

function addTodaysWorkLink() {
	//--- Add a link to the page showing today's work (depends on local timezone)
	var offset = new Date().getTimezoneOffset() / 60,
		query = toQuery({timezone: offset});
	append('#comparisons_panel', {tag: 'a', href: '/pairwise/todayswork?' + query, c: "Show today's work"});	
}


function tableControl(controls, makeTable, command, count) {
	//--- Add controls to a table of database entities
	var itemsPerPage = fromServer.itemsPerPage,
		controls = Q(controls),
		page = 1;
	updateControls();
	function firstItem(p) {
		return (p - 1) * itemsPerPage + 1;
	}
	function lastItem(p) {
		return Math.min(p * itemsPerPage, count);
	}
	function numberOfPages() {
		return parseInt(count / itemsPerPage + .5);
	}
	function updateControls() {
		var n = numberOfPages(), p, control, a, b, c;
		if (count <= itemsPerPage) {
			set(controls, "Showing all " + count);
		}
		set(controls, "Showing " + firstItem(page) + "-" + lastItem(page) + " (out of " + count + ") ");
		if (page > 1) {
			control = M('span', {className: 'tableControl'}, "&lt; Previous Page");
			click(control).then(previousPage);
			append(controls, ' ', control);
		}
		if (page < n) {
			control = M('span', {className: 'tableControl'}, "Next page &gt;");
			append(controls, ' ', control);
			click(control).then(nextPage);
			
		}
		for (p = 1; p <= n; p++) {
			if (p != page) {
				control = M('span', {className: 'tableControl'}, firstItem(p) + "-" + lastItem(p));
				click(control).then(showPage, {page: p});
				append(controls, ' ', control);
			}
		}
	}
	function nextPage() {
		showPage({page: page + 1});		
	}
	
	function previousPage() {
		showPage({page: page - 1});		
	}
	function showPage(d) {
		var p = d.page;
		console.log('show page', p);
		get(command, {page: p}).then(succeeded, standardFail);		
	}
	
	function succeeded(data) {
		//--- Response provides new count and the set of items for the page sent.
		console.log('succeeded: server response', data);
		makeTable(data.response.entities);
		page = data.parameters.page;
		count = data.response.count;
		updateControls();	
	}
	
	function fail() {
		showMessage("It was not possible to connect to the server. Please try again later.");		
	}
}
