/*
DOM MANIPULATION LIBRARY
 */
 
var counter = 0, cmax = 300;
 
//--- Shorthand for some common functions
function E(id) {
	return document.getElementById(id);
}
/*
// Not sure if this is useful currently... 
function Q(s) {
	// --- Returns an array or element list matching the query
	
	if (s.tagName) {
		return [s];
	}
	return document.querySelectorAll(s);
}
*/

function Q(s) {	
	return (typeof s === "string") ? document.querySelector(s) : s;
}

function QA(s) {
	return (typeof s === "string") ? document.querySelectorAll(s) : [s];
	// TODO: also allow a node list
}


// Later, use requirejs / ecmascript modules to import these rather than just putting them
// in the global namespace directly

function removeNode(node) {
	if (typeof node === "string") node = Q(node);
	node.parentNode.removeChild(node);
}

function empty(node) {
	while (node.firstChild) {
		node.removeChild(node.firstChild);
	}
}

function set_OLD(q, content) {
	//--- if content is a string, sets q.innerHTML to the string
	// if content is a dictionary-like object, set attributes from it
	// if content is a node or an object with a tag attribute, append it 
	// if content is a list of nodes, append them
	
	var el = Q(q), k;
	//console.log('lib-setting', q, content, el, counter);
	//if (counter++ > cmax) return
	if (content == null) {
		empty(el);
	} else if (typeof content === "string") {  
		el.innerHTML = content;		
	} else if (typeof content === "object" && (content instanceof Node || content.length || content.tag)) {
		empty(el);
		append(el, content);
	} else {
		for (k in content) {
			if (content.hasOwnProperty(k) && k !== 'tag') {
				if (k === 'html') {
					el.innerHTML = content[k];		
				} else if (k === 'c' || k === 'children' || k === 'child') {
					empty(el);
					append(el, content[k]);
				} else if (k in el.style) {
					el.style[k] = content[k];					
				} else {
					el[k] = content[k];		// TODO: check, may need to use setAttribute in some cases
				}
			}
		}
	}
	return el;
}


/* 
set, make/M and append functions

Currently revising them to make them slightly simpler and more consistent.
Objects of the form {tag: p, html: "hi there"} are no longer accepted
Instead use M("p", "hi there")

This is better but consider further changes:
- better to treat the tag name as just another property? Maybe not as the tag is compulsory, and if we want to be able
to make divs more quickly we can easily make a separate Mdiv function for that
- not entirely easy to translate from Py to js.
- objects of the following form could be stored as variables in python, and readily translated in js:
	
	{"tag": "div", "id": "my_widget", c: ["Some text to add", {"tag": "strong", "c": "some bold text"}, button]}
	
	=> M('div', {id: "my_widget"}, ["Some text to add", M("strong", "some bold text"), button])


- also consider two abbreviated syntaxes:
	append(table, [
		M('th', 'Name'),
		M('th', 'Created'),
		M('th', 'Number of comparisons'),
		M('th', 'Open'),
		M('th')
	]);
	
	=> 
	append(table, {th: "Name", className: 'nameHead'}, {th: 'Created'}, {th: "Number of comparisons"}, {th: "Open"}, {th: ""});
	OR append(table, {tag: "th", c: "Name", className: "nameHead"}, etc.)

	
*/



function set(q, settings) {
	//--- set attributes of an element based on a dictionary like object
	
	var el = Q(q), k;
	console.log('set', q, settings);
	if (typeof settings === "string" || typeof settings === "number" || settings instanceof Node || settings.length) { 
		empty(el);
		append(el, settings);
	} else {
		for (k in settings) {
			if (settings.hasOwnProperty(k)) {
				if (k === 'c') {
					empty(el);
					append(el, settings.c);
				} else if (k in el.style) {
					el.style[k] = settings[k];					
				} else {
					el[k] = settings[k];		// TODO: check, may need to use setAttribute in some cases
				}
			}
		}
	}
	return el;
}

var HTMLTAGS = ["a", "abbr", "address", "area", "article", "aside", "audio", "b", "base", "bdi", "bdo", "blockquote", "body", "br",
	"button", "canvas", "caption", "cite", "code", "col", "colgroup", "datalist", "dd", "del", "details", "dfn", "dialog",
	"div", "dl", "dt", "em", "embed", "fieldset", "figcaption", "figure", "footer", "form", "h1", "h2", "h3", "h4", "h5", "h6",
	"head", "header", "hr", "html", "i", "iframe", "img", "input", "ins", "kbd", "label", "legend", "li", "link", "main",
	"map", 	"mark", "menu", "menuitem", "meta", "meter", "nav", "noscript", "object", "ol", "optgroup", "option", "output",
	"p", "param", "picture", "pre", "progress", "q", "rp", "rt", "ruby", "s", "samp", "script", "section", "select", "small",
	"source", "span", "strong", "style", "sub", "summary", "sup", "table", "tbody", "td", "textarea", "tfoot", "th", "thead",
	"time", "title", "tr", "track", "u", "ul", "var", "video", "wbr"];

function makeFromObj(obj) {
	/*--- Turn an object into a new element
		Two possible formats: 1. {th: "My table header", className: "myClassName"} 
		2. {tag: "th", c: "My table header", className: "myClassName"} 
		In each case the content that is given can include either a string (added to the innerHTML), or an object, or 
		a series of objects, or a node, or a series of nodes.
	*/
	var k, settings;
	console.log('makeFromObj', obj);
	for (k in obj) {
		if (obj.hasOwnProperty(k)) {
			if (k === "tag") {
				settings = shallowCopy(obj)
				delete settings.tag;
				return M(obj.tag, settings);
			} else if (HTMLTAGS.indexOf(k) > -1) {
				settings = shallowCopy(obj);
				delete settings[k];
				return M(k, settings, obj[k]);
			}
		}
	}	
}

function append(q, content) {
	var el = Q(q), i, made;
	//--- Append a node or list of nodes to the parent element
	// If a string is given instead of a node, treat it as html
	
	
	if (arguments.length > 2) {
		content = [content];
		for (i = 2; i < arguments.length; i++) {
			content.push(arguments[i]);
		}
	}
	if (typeof content === "string" || typeof content === "number") {
		el.insertAdjacentHTML('beforeend', content);	// el.innerHTML += content;
	} else if (content instanceof Node) {
		el.appendChild(content);
	} else if (!content.length) {
		el.appendChild(makeFromObj(content));
	} else if (content.length) {
		console.log('appending multiple items', content);
		for (i = 0; i < content.length; i++) {
			if (typeof content[i] === "string" || typeof content === "number") {
				el.insertAdjacentHTML('beforeend', content[i]);	// el.innerHTML += content[i];
				//console.log(i, 'is string. innerhtml is "' + el.innerHTML + '"');
			} else if (content[i] instanceof Node) {
				console.log(i, 'is node');
				el.appendChild(content[i]);
			} else {
				console.log(i, 'is object');
				el.appendChild(makeFromObj(content[i]))
			}
		}
	} 
}

function edit(q, content, settings) {
	// --- This is similar to set_OLD. Not sure if it will be useful or not.
	var el = Q(q), appended;
	if (typeof content === "string" || content instanceof Node || content.length) {
		empty(el);
		append(el, content);
	} else if (!settings) {
		settings = content;
	}
	if (settings) {
		set(el, settings);
	}
}

function M(tag, settings, content) {
	// --- Makes a new element with the specified tag
	// Settings is a dictionary of settings to be set on the element
	// Content is a string, node, or list of nodes that will be appended to the new element
	// If the 2nd argument looks more like content than settings and the 3rd argument is not given, then treat the 2nd arg as content.
	var el = document.createElement(tag);
	console.log('M', tag, settings, content);
	if (settings && !content && ((typeof settings === "string") || settings instanceof Node || settings.length)) {
		content = settings;
	} else if (settings) {
		set(el, settings);
	}
	if (content) {
		append(el, content);
	}
	return el;
}


function makeDiv(content, settings) {
	//--- Shorthand to make divs quickly. Maybe redundant
	return M('div', content, settings);
}


function make_OLD(obj) {
	//--- Make an element given an object of the form {tag: 'div', html: "This is the content", etc.}
	var el = document.createElement(obj.tag || 'div'),
		content;
	if (obj instanceof Node || obj.length || typeof obj === "string") {
		return set(el, obj);
	}
	else {
		content = shallowCopy(obj);
		delete(content.tag);
		return set(el, content);
	}
}


function append_OLD(el, nodes) {
	el = Q(el);
	console.log('appending', el, nodes, counter);
	
	//if (counter++ > cmax) return
	//--- Append a node or list of nodes to the parent element
	// If a string is given instead of a node, convert it to a text node
	// If it is an object with a tag attribute, make the node
	if (!nodes.forEach) {
		nodes = [nodes];
	}
	
	nodes.forEach(function(node) {
		if (typeof node === 'string') {
			el.appendChild(document.createTextNode(node));
		} else if (node.tag && !(node instanceof Node)) {
			el.appendChild(make(node));		
		} else {
			el.appendChild(node);
		}
	});
}



/* Not sure if this may also be useful...
function multiset(q, listOfContent) {
	var els = Q(q);
	for (var i = 0; i < els.length; i++) {
		

	}
}
*/


/*
EXTRACTING DATA FROM THE DOM
*/
function getData(el, propertyName) {
	//--- Get the data property from an element by checking its parent elements until it is found
	while (el !== document.body) {
		if (el.dataset && el.dataset[propertyName]) {
			return el.dataset[propertyName];
		} else {
			el = el.parentElement;
		}
	}
}

var DomTemplate = (function() {
	//--- Extend an object constructor, adding methods that allow it both to get data from the DOM 
	// and put data to the DOM, using an element template. The template can either be displayed on the page
	// or newly created
	
	function attach(cls_, template, processForOutput) {
		extend(cls_.prototype, {
			getClass: function() {
				return cls_;
			},
			template: template.cloneNode(true),
			init: init,
			renderEl: renderEl,
			makeEl: makeEl,
			listen: listen,
			output: processForOutput,
			q: querySelector,
			set: _set
		});
		extend(cls_, {
			fromEls: fromEls,
			click: click_,
			parent: template.parentNode,
			list: [],
			listeners: []
		});
	}
	
	// Convenience functions for manipulating dom elements: querySelector and set
	function querySelector(q) {
		return this.el.querySelector(q);
	}
	
	function _set(q, content) {
		//console.log('setting', 'this', this, 'this.el', this.el, 'q', q, 'content', content);
		return set(this.el.querySelector(q), content);
	}
	
	function init(data) {
		extend(this, data);
		this.cls = this.getClass();
		this.cls.list.push(this);
	}
	
	// TODO: also need a delete function, which removes the object from the list and
	// if appropriate, its attached element from the parent
		
	function renderEl(position) {
		// Render at the specified position
		// TODO: note the position (currently we just render all at the end)
		var el = this.makeEl();
		this.cls.parent.appendChild(el);
		this.listen();
		//click(this.el.querySelector(k)).then([this, listeners[k]]);
	}
	
	function listen() {
		var i, el;
		if (!this.el) {
			console.log('no element defined yet for', this);
			return;
		}
		for (i = 0; i < this.cls.listeners.length; i++) {
			el = this.el.querySelector(this.cls.listeners[i].query);
			console.log('about to listen', el, this.cls.listeners[i], this.cls.listeners[i].query, this.el);		
			click(el).then([this, this.cls.listeners[i].callBack]);
		}
	}
	
	function makeEl() {
		console.log('trying to makeEl');
		if (!this.el) {
			this.el = this.template.cloneNode(true);
		}
		console.log('this.el', this, this.el);
		this.output();	// user-supplied function that fills in the data
		return this.el;
	}

	// Class functions
	function fromEls(q, process) {
		//--- Use the constructor to convert a DOM query into a series of objects
		// process if specified is a function that will be called on each object after creating it
		// TODO: need similar way of attaching an existing DOM to an existing object.
		var els = document.querySelectorAll(q), obj, i, cls = this;
		cls.prototype.processFromEl = process;
		cls.list = [];
		for (i = 0; i < els.length; i++) {
			obj = new cls();
			obj.el = els[i];
			obj.listen();
			if (obj.processFromEl) {
				obj.processFromEl();
			}
		}
		return cls.list;
	}
	
	function click_(query, callBack) {
		var cls = this;
		cls.listeners.push({query: query, callBack: callBack});
		cls.list.forEach(function(entry) {
			entry.listen();
		});
	}
		
	return {
		attach: attach
	};
})();


/*
ANIMATION
 */

var animations = (function () {
	//--- Module for managing roster of animations
	// animations.start(anim)	-- add the given animation object to the roster and start playing it
	// animations.roster		-- array containing the roster of animations

	var self = {
		roster: [],
		start: start
	};
	function start (animation) {
		console.log('starting new anim', animation.step, animation.duration, animation.data);
		self.roster.push(animation);
		if (self.roster.length == 1) {
			window.requestAnimationFrame(step);
		}
	}

	function step(t) {
		self.roster = self.roster.filter(function(animation) {
			return animation.stepOrStop(t);
		});
		if (self.roster.length) {
			window.requestAnimationFrame(step);
		}
	}
	return self;
})();

function Animation(step, duration, data) {
	this._step = step;
	this.data = data;
	this.duration = duration;
	this.start = performance.now();
	this.stop = this.start + duration;
	animations.start(this);
}

Animation.prototype.stepOrStop = function (t) {
	//--- If animation has not finished, call _step and return true; if it has finished then call _then
	// This allows to call active animations and filter out the ones that have finished
	// The underlying step function can return 'stop' to stop before the duration has finished.

	if (t < this.stop) {
		return this._step(t - this.start, this.data) !== 'stop';
	} else if (this._then) {
		this._then(this.data);
	}
};

Animation.prototype.then = function (func) {
	this._then = func;
};

function swipe(el, duration) {
	var startHeight = el.offsetHeight;
	el.style.overflow = 'hidden';
	function step(t) {
		el.style.height = startHeight * (1 - t / duration) + 'px';
	}
	return new Animation(step, duration);
}

function fade(el, duration) {
	var startOpacity = 1;
	function step(t) {
		el.style.opacity = (1 - t / duration) * startOpacity;
	}
	return new Animation(step, duration);
}

/*
EVENT LISTENERS
 */

var GETDATA = {};		// constant for when we need to look up data from html
 
function listen(selector, type) {
	console.log('listening', selector, type, QA(selector));
	return {
		baseTargets: QA(selector),
		type: type,
		then: listenThen
	};
}

function listenThen(func, data) {
	var i;
	if (!data) {
		data = {};
	}
	data.baseTargets = this.baseTargets;
	data.type = this.type;
	func = parseFunction(func);
	for (i = 0; i < this.baseTargets.length; i++) {
		addListener(this.baseTargets[i], this.type, func, data);		
	}
}
function addListener(baseTarget, type, func, data) {
	data = fillData(baseTarget, data);
	data.baseTarget = baseTarget;
	baseTarget.addEventListener(type, function(ev) {
		return func.func.apply(func.thisArg, [extend({
			event: ev,
			target: ev.target
		}, data)]);
	});
}


function fillData(el, obj) {
	//--- Returns a shallow copy of an object with any GETDATA values replaced by data extracted
	// from the DOM.
	// TODO [check whether still using this anywhere! may delete]
	var k, r = {};
	for (k in obj) {
		if (obj.hasOwnProperty(k)) {
			if (obj[k] === GETDATA) {
				r[k] = getData(el, k);
			} else {
				r[k] = obj[k];
			}
		}
	}
	return r;	
}

function click(selector) {
	return listen(selector, 'click');
}

function get(url, parameters) {
	fullUrl = url;
	//TODO: check first if url already contains parameters and additional parameters have been given
	if (parameters) {
		fullUrl += '?' + toQuery(parameters);
	}
	return {
		url: url,
		fullUrl: fullUrl,
		parameters: parameters,
		then: requestThen,
		method: "GET"
	};
}

function post(url, parameters) {
	fullUrl = url;
	return {
		url: url,
		fullUrl: fullUrl,
		parameters: parameters,
		then: requestThen,
		method: "POST"
	};
}

function requestThen(success, fail, data) {
	var request = new XMLHttpRequest();
	success = parseFunction(success);
	fail = parseFunction(fail);
	data = data || {};
	request.open(this.method, this.fullUrl, true);
	extend(data, {
		request: request,
		url: this.url,
		parameters: this.parameters
	});
	console.log('basic data is', data);
	request.onreadystatechange = function () {
		if (request.readyState == 4) {
			if (request.status == 200) {
				console.log('good request', request.responseText);
				// Action to be performed when the document is read;
				data.response = JSON.parse(request.responseText);
				//TODO: handle if json parse fails
				success.func.apply(success.thisArg, [data]);
			}
			else {
				data.response = request.responseText;
				fail.func.apply(fail.thisArg, [data]);
			}
		}
	};
	//TODO: check if I can use bind or call the function directly here instead:
	// (success.thisArg).(success.func)(data) --?
	if (this.method == "POST") {
		request.setRequestHeader('Content-Type', 'application/json');
		request.send(JSON.stringify(this.parameters));
		console.log('POSTing the following', JSON.stringify(this.parameters));
	}
	else {
		request.send();
	}
	return request;
}

/*
STRING MANIPULATION
 */

function toQuery() {
	//--- Turn an object or series of objects into a URI encoded string for submission
	// n.b. can replace this with the one from _ community
	var r = "",
	s,
	k,
	i,
	obj;
	for (i = 0; i < arguments.length; i++) {
		obj = arguments[i];
		for (k in obj) {
			if (obj.hasOwnProperty(k)) {
				if (r !== "") {
					r += "&";
				}
				if (obj[k]instanceof Date) {
					s = obj[k].toJSON();
				} else {
					s = obj[k];
				}
				r += k + "=" + s;
			}
		}
	}
	return r;
}

function camelCase(string) {
	return  string.replace(/-([a-z])/g, function (g) { return g[1].toUpperCase(); });
}

/*
OBJECT MANIPULATION
 */
 

	
function extend(a, b) {
	// Shallow merge all properties of b into a, replacing them if duplicated
	// returns a
	for (var k in b) {
		if (b.hasOwnProperty(k)) {
			a[k] = b[k];
		}
	}
	return a;
}

function shallowCopy(a) {
	// Return a shallow copy of a dict-like object
	return extend({}, a);
}

function toArray(a) {
	//--- Turn some array-like thing into an array
	var i, r = [];
	for (i = 0; i < a.length; i++) {
		r.push(a[i]);
	}
	return r;
}

function parseFunction(func) {
	//--- Accept a two-part array instead of a function, in order to bind the function to an object
	if (func[0] && func[1]) {
		return {
			thisArg: func[0],
			func: func[1]
		};
	}
	return {
		thisArg: null,
		func: func
	};
}


/*
COOKIES AND LOCAL DATA 
*/

// altered from https://www.w3schools.com/js/js_cookies.asp and 
// http://rickyrosario.com/blog/javascript-cookie-utility/
var cookie = (function() {
	function set(cname, cvalue, exdays) {
		var d, expires;
		if (exdays) {
			d = new Date()
			d.setTime(d.getTime() + (exdays * 24 * 60 * 60 * 1000));
			document.cookie = cname + "=" + cvalue + ";expires=" + d.toUTCString() + ";path=/";
		} else {
			document.cookie = cname + "=" + cvalue + ";path=/";
		}
	}
	function get(cname) {
		var name = cname + "=",
			ca = document.cookie.split(';'),
			i, c;
		for(i = 0; i < ca.length; i++) {
			c = ca[i];
			while (c.charAt(0) == ' ') {
				c = c.substring(1);
			}
			if (c.indexOf(name) == 0) {
				return c.substring(name.length, c.length);
			}
		}
		return "";
	}
	
	function erase(cname) {
		set(cname, "", -1)
	}
	return {set: set, get: get, erase: erase}
})();

