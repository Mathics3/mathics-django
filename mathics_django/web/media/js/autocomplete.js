
function TrieNode(key) {
	this.key = key;
	this.parent = null;
	this.children = {};
	this.end = false;
}

TrieNode.prototype.getWord = function() {
	var output = [];
	var node = this;
	while (node !== null) {
		output.unshift(node.key);
		node = node.parent;
	}
	return output.join('');
};

function Trie() {
	this.root = new TrieNode(null);
}

// time complexity: O(k), k = word length
Trie.prototype.insert = function(word) {
	var node = this.root;
	
	for(var i = 0; i < word.length; i++) {
		if (!node.children[word[i]]) {
			node.children[word[i]] = new TrieNode(word[i]);
			node.children[word[i]].parent = node;
		}
	
		node = node.children[word[i]];
	
		if (i == word.length - 1) {
			node.end = true;
		}
	}
};

// time complexity: O(k), k = word length
Trie.prototype.contains = function(word) {
	var node = this.root;
	
	for(var i = 0; i < word.length; i++) {
		if (node.children[word[i]]) {
			node = node.children[word[i]];
		} else {
			return false;
		}
	}
	
	return node.end;
};

// time complexity: O(p + n), p = prefix length, n = number of child paths
Trie.prototype.find = function(prefix) {
	var node = this.root;
	var output = [];
	
	for(var i = 0; i < prefix.length; i++) {
		if (node.children[prefix[i]]) {
			node = node.children[prefix[i]];
		} else {
			return output;
		}
	}
	
	findAllWords(node, output);
	
	return output;
};

function findAllWords(node, arr) {
	if (node.end) {
		arr.unshift(node.getWord());
	}
	
	for (var child in node.children) {
		findAllWords(node.children[child], arr);
	}
}

function isAlphabetic(ch) {
	return /[a-zA-Z]/.test(ch);
}

function getExtremeIndex(str, i, left) {
	if (left) {
		while(isAlphabetic(str.charAt(i--)));
		i += 2;
	} else {
		while(isAlphabetic(str.charAt(i++)));
		i -= 1;
	}
	return i;
}

function hungryReplace(text, replacement, i) {
	// Replaces left and right until it hits a nonalphabetic character
	
	// If text[i] is not alphabetic, then shift it down one
	if (!isAlphabetic(text.charAt(i))) {
		i -= 1;
	}
	
	let replaceRange = (s, start, end, substitute) => {
		return s.substring(0, start) + substitute + s.substring(end);
	}
	
	let low = getExtremeIndex(text, i, true);
	let high = getExtremeIndex(text, i, false);
	
	return replaceRange(text, low, high, replacement);
}

function addChildren(root, children) {
	children.forEach(x => {
		root.appendChild(x);
	});
}

function elementWithInnerText(tag, text) {
	div = document.createElement(tag);
	div.innerText = text;
	div.style.backgroundColor = 'gray';
	return div;
}

function autocomplete(e) {
	let pos = e.target.selectionStart;
	let text = e.target.value;
	
	let currChar = text.charAt(pos - 1);
  
	dropdown.innerHTML = '';
	dropdown.size = '0';
	dropdown.style.display = 'none';

	if (isAlphabetic(currChar)) {
		let current = currChar;
		let i = pos - 2;
		while(isAlphabetic(text.charAt(i)))
			current += text.charAt(i--);
		current = current.split('').reverse().join('');
	  
		let candidates = trie.find(current);
		console.log(candidates);
		addChildren(dropdown,
			candidates
			  .map(x => elementWithInnerText('option', x)));

		const length = candidates.length;
		dropdown.size = (length <= 12 ? length : 12);
		if (length > 0)
		  dropdown.style.display = 'block';

		// If key is pressed, select a candidate
		if (e.key === 'Alt') {
			idx = (idx + 1) % candidates.length;
		} else if (e.key === 'Escape') {
			e.preventDefault();
			let replacement = candidates[idx];
			e.target.value = hungryReplace(text, replacement, pos - 1);
			dropdown.style.display = 'none';
		}
	} else {
		idx = 0;
		current = '';
	}

	if(dropdown.children[idx])
    	dropdown.children[idx].selected = true;
}
  
let current = '';
let idx = 0;
let dropdown;
let trie = new Trie();

new Ajax.Request('/ajax/names', {
	method: 'get',
	onSuccess: function(transport) {
		let doc = transport.responseText.evalJSON().content;
		
		doc.forEach(x => {
			x = x.split('`').slice(1).join('`')
			trie.insert(x);
		});
	}
});