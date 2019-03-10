/************
* Pairwise Video Comparison - admin app
* Common functions 
*****************/



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


function makeButton(content, handler, id) {
	// --- Make a button with specified content and click handler;
	// if handler is a url, then provide just a link
	var r;
	if (typeof handler === "function") {
		r = M('button', content);
		click(r).then(handler);
	} else {
		r = M('a', content, {href: handler});
	}
	if (id) {
		r.id = id;
	}
	return r;	
}

function showMessage(messageHtml, buttons) {
	//--- Show a popup message with buttons given as a dictionary in the form {label: handler, ... }
	var div = E('message');
	if (!buttons) {
		buttons = {Okay: hideMessage};
	}
	if (!div) {
		div = M('div', {id: 'message'}); 
		append(document.body, div);
	}
	set(div, {display: 'block', c: {'div': messageHtml, className: 'inner'}});
	// set(div, {display: 'block', c: M('div', {className: "inner"}, messageHtml)});
	for (k in buttons) {
		if (buttons.hasOwnProperty(k)) {
			append(div, makeButton(k, buttons[k]));
			//div.appendChild(makeButton(k, buttons[k]));
		}
	}
}

function hideMessage() {
	if (E('message')) {
		E('message').style.display = 'none';
	}
}

function redirectWithMessage(page, message) {
	// --- Redirect to a new page and store a message to be shown on the new page
	cookie.set('pwvMessage', message);
	window.location.href = page;
}

function showInitMessage() {
	// --- Show a message stored from the previous page
	var message = cookie.get('pwvMessage');
	if (message != "") {
		showMessage(message, {Okay: hideMessage});
		cookie.erase('pwvMessage');
	}
}

showInitMessage();		// run this at the start on all pages in this app

var regUtils = (function() {
	var lineBreaks = new RegExp(/<\/(h.|p|div|li|ul)>|<br.*?>/g),
		lineBreakRep = "[pwv programme; insert line break here]",
		tagBody = '(?:[^"\'>]|"[^"]*"|\'[^\']*\')*',
		tagOrComment = new RegExp(
		'<(?:'
		// Comment body.
		+ '!--(?:(?:-*[^->])*--+|-?)'
		// Special "raw text" elements whose content should be elided.
		+ '|script\\b' + tagBody + '>[\\s\\S]*?</script\\s*'
		+ '|style\\b' + tagBody + '>[\\s\\S]*?</style\\s*'
		// Regular name + doctype <!DOCTYPE..., and allow uppercase
		+ '|!?/?[a-zA-Z]'
		+ tagBody
		+ ')>',
		'gi');
	function removeTags(html) {
		var oldHtml;
		do {
			oldHtml = html;
			html = html.replace(tagOrComment, '');
		} while (html !== oldHtml);
		console.log('remove tags results', html.replace(/</g, '&lt;'));
		return html.replace(/</g, '&lt;');
	}
	
	function cleanWithBreaks(html) {
		html = html.replace(lineBreaks, lineBreakRep);	// identify and mark line breaks
		html = html.replace(new RegExp("<title>.*?<\/title>"), "");	// remove title
		html = removeTags(html);						// remove all tags
		html = html.split(lineBreakRep).join("<br />");	// replace marks with line breaks
		console.log('clean with breaks result', html);
		return html;
		// TODO: ideally ensure that there aren't multiple line breaks
	}
	return {removeTags: removeTags, cleanWithBreaks: cleanWithBreaks};
})();
			

function standardFail(data) {
	//--- Provides a standard function that can be used in case of failure of an
	// xmlhttprequest
	var error;
	console.log('fail', data);
	if (data.request.status == 0) {
		showMessage("Sorry, the data was not saved. The application could not contact the server. Please check your internet connection and try again.", {Okay: hideMessage});
	}
	else {	
		error = '<div class="errorMessage"><h1>' + data.request.status + " (" 
			+ data.request.statusText + ")</h1>" 
			+ regUtils.cleanWithBreaks(data.request.responseText)
			+ '</div>';	
		showMessage("Sorry, the data was not saved. The server returned the following error message: " + error, {Okay: hideMessage});
	}
}

function okayLookingEmail(s) {
	//--- Check an email is of the form something@something, regardless of dots etc.
	s = s.split('@');
	return s.length == 2 && s[0] != "" && s[1] != "";
	
}



