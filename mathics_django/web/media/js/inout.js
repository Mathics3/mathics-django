function showSave() {
	requireLogin('You must login to save worksheets online.', () =>
		showPopup(document.getElementById('save'))
	);
}

function openWorksheet(name) {
	hidePopup();

	new Ajax.Request('/ajax/open/', {
		method: 'post',
		parameters: { name },
		onSuccess: (transport) => {
			const response = JSON.parse(transport.responseText);

			if (document.getElementById('document').style.display !== 'none') {
				setContent(JSON.parse(response.content));
			} else {
				document.getElementById('codetext').value = response.content;
			}
		}
	});
}

function showWorksheets() {
	new Ajax.Request('/ajax/getworksheets/', {
		method: 'get',
		onSuccess: (transport) => {
			const response = JSON.parse(transport.responseText);
			const tbody = document.getElementById('openFilelist');
			tbody.innerHTML = '';

			response.worksheets.forEach((worksheet) => {
				const openWorksheetButton = document.createElement('a');
				openWorksheetButton.href = `javascript:openWorksheet("${worksheet.name}")`;
				openWorksheetButton.innerText = worksheet.name;

				const openWorksheetBox = document.createElement('td');
				openWorksheetBox.appendChild(openWorksheetButton);

				const deleteWorksheetButton = document.createElement('a');
				deleteWorksheetButton.innerText = 'Delete';
				deleteWorksheetButton.href = 'javascript:';

				const deleteWorksheetBox = document.createElement('td');
				deleteWorksheetBox.appendChild(deleteWorksheetButton);

				const row = document.createElement('tr');
				row.appendChild(openWorksheetBox);
				row.appendChild(deleteWorksheetBox);

				deleteWorksheetButton.addEventListener('click', () =>
					deleteWorksheet(row, worksheet.name)
				);

				tbody.appendChild(row);
			});

			showPopup(document.getElementById('open'));
		}
	});
}

function deleteWorksheet(element, name) {
	element.remove();

	new Ajax.Request('/ajax/delete/', {
		method: 'post',
		parameters: { name }
	});
}

function showOpen() {
	requireLogin(
		'You must login to open online worksheets.',
		showWorksheets
	);
}

function save(overwrite) {
	// can't save worksheet with empty name
	if (!document.getElementById('id_name').value.strip()) {
		return;
	}

	// if overwrite is false set it to ''
	overwrite ||= '';

	let content;

	if (document.getElementById('document').style.display !== 'none') {
		content = getContent();
	} else {
		content = document.getElementById('codetext').value;
	}

	submitForm(
		'saveForm',
		'/ajax/save/',
		(response) => {
			if (!checkLogin(response)) {
				return;
			}

			hidePopup();

			if (response.result === 'overwrite') {
				showDialog(
					'Overwrite worksheet',
					`A worksheet with the name '${response.form.values.name}' already exists. Do you want to overwrite it?`,
					'Yes, overwrite it',
					'No, cancel',
					() => save(true)
				);
			}
		},
		{ content, overwrite }
	);
}

function switchCode() {
	const documentElement = document.getElementById('document');
	const codeText = document.getElementById('codetext');
	const code = document.getElementById('code');
	const codeLink = document.getElementById('codelink');

	if (documentElement.style.display !== 'none') {
		documentElement.style.display = 'none';

		codeText.value = getContent();
		code.style.display = 'block';
		codeLink.innerText = 'Interactive mode';
	} else {
		setContent(codeText.value);

		code.style.display = 'none';
		documentElement.style.display = 'block';
		codeLink.innerText = 'View/edit code';
	}
}

function getContent() {
	const queries = [];

	const queriesElement = document.getElementById('queries');

	for (let i = 0; i < queriesElement.childElementCount; i++) {
		const { value, results } = queriesElement.children[i]
			.querySelector('textarea.request');

		queries.push({
			request: value,
			results: results
		});
	}

	return JSON.stringify(queries);
}

function setContent(content) {
	document.getElementById('queries').innerHTML = '';

	document.getElementById('welcome').style.display = 'none';

	content.forEach((item) => {
		const li = createQuery(null, true, true);

		li.textarea.value = item.request;

		if (item.results !== undefined) {
			setResult(li.ul, item.results);

			li.textarea.results = item.results;
		}
	});

	createSortable();

	refreshInputSizes();

	lastFocus = null;

	const queries = document.getElementById('queries');

	if (queries.lastChild) {
		queries.lastChild.textarea.focus();
	}
}

function createLink() {
	const queriesElement = document.getElementById('queries');

	const queries = [];

	for (let i = 0; i < queriesElement.childElementCount; i++) {
		queries.push('queries=' + encodeURIComponent(
			queriesElement.children[i].querySelector('textarea.request').value
		));
	}

	location.href = '#' + btoa(queries.join('&')); // encodeURI(query);
}

function setQueries(queries) {
	const queryList = [],
		queriesElement = document.getElementById('queries');

	queries.forEach((query) => {
		const li = createQuery(null, true, true);

		li.textarea.value = query;

		queryList.push({ li, query });
	});

	refreshInputSizes();

	function load(index) {
		if (index < queryList.length) {
			submitQuery(queryList[index].li.textarea, () => load(index + 1));
		} else {
			createSortable();
			lastFocus = null;

			if (queriesElement.lastChild) {
				queriesElement.lastChild.textarea.focus();
			}
		}
	}

	load(0);
}

function loadLink() {
	const hash = location.hash;

	if (hash && hash.length > 1) {
		const queries = [];

		atob(hash.slice(1)).split('&').forEach((param) => {
			if (param.startsWith('queries=')) {
				param = decodeURIComponent(param.slice(8));

				if (param !== '') {
					queries.push(param);
				}
			}
		});

		setQueries(queries);

		return queries.length > 0;
	} else {
		return false;
	}
}

function showGallery() {
	setQueries([
		'(**** Calculation ****)',
		'Sin[Pi]',
		'E ^ (Pi I) (* Euler\'s famous equation *)',
		'N[E, 30] (* 30-digit Numeric approximation of E *)',
		'30! (* Factorial *)',
		'% // N',
		'Sum[2 i + 1, {i, 0, 10}] (* Sum of 1st n odd numbers (n+1)**2 *)',
		'n = 8; 2 ^ # & /@ Range[0, n] (* Powers of 2 *)',
		'Total[%] (* Sum is 2 ^ n - 1 *)',

		'(**** Functions ****)',
		'(* Colatz Conjecture https://oeis.org/A006577 *)',
		'f[n_] := Module[{a=n, k=0}, While[a!=1, k++; If[EvenQ[a], a=a/2, a=a*3+1]]; k]',
		'Table[f[n], {n, 4!}]',
		'(**** Symbolic Manipulation ****)',
		'Apart[1 / (x^2 + 5x + 6)]',
		'Cancel[x / x ^ 2]',
		'Expand[(x + y)^ 3]',
		'Factor[x ^ 2 + 2 x + 1]',
		'Simplify[5*Sin[x]^2 + 5*Cos[x]^2]',
		'(**** Calculus ****)',
		'Sin\'[x]',
		'Sin\'\'[x]',
		'D[Sin[2x] + Log[x] ^ 2, x]',
		'Integrate[Tan[x] ^ 5, x]',

		'(**** Linear Algebra ****)',
		'MagicSquare = {{2, 7, 6}, {9, 5, 1}, {4, 3, 8}}; MatrixForm[MagicSquare]',
		'LinearSolve[MagicSquare, {1, 1, 1}] // MatrixForm',
		'Eigenvalues[MagicSquare]',
		'(**** Chemical Data ***)',
		'(* 2nd and 3rd Row of Periodic Table *)',
		'Grid[{Table[ElementData[i], {i, 3, 10}], Table[ElementData[i], {i, 11, 18}]}]',
		'ListLinePlot[Table[ElementData[z, "MeltingPoint"], {z, 118}]]',

		'(**** Some graphs ****)',
		'ListPlot[{Sqrt[Range[40]], Log[Range[40, 80]]}, TicksStyle->{Blue,Purple}]',
		'Plot[{Sin[x], Cos[x], Tan[x]}, {x, -3Pi, 3Pi}]',
		'Graphics[Polygon[{{150,0},{121,90},{198,35},{102,35},{179,90}}]]',

		'(* Charts: *)',
		'BarChart[{{1, 2, 3}, {2, 3, 4}}]',
		'PieChart[{30, 20, 10}, ChartLabels -> {Dogs, Cats, Fish}]',

		'(* Bouncing Ping-Pong Ball at equal time intervals *)',
		'Plot[Abs[Sin[t] / (t + 1)], {t, 0, 4 Pi}, Mesh->Full, PlotRange->{0, 1 / 2}]',

		'(* Here is a 5-blade propeller, or maybe a flower, using PolarPlot: *)',
		'PolarPlot[Cos[5t], {t, 0, Pi}]',
		'(* Also try surrounding the Cos in an Abs: PolarPlot[Abs[Cos[5t]], {t, 0, Pi}] *)',

		'Graphics[Table[Circle[{x,y}], {x, 0, 10, 2}, {y, 0, 10, 2}]]',

		'(* Target Practice. *)',
		'Graphics[Circle[], Axes-> True]',

		'(* Random dots in Sierpinski Triangle. *)',
		'vertices = {{0,0}, {1,0}, {.5, .5 Sqrt[3]}};',
		'points = NestList[.5(vertices[[ RandomInteger[{1,3}] ]] + #) &, {0.,0.}, 600];',
		'Graphics[Point[points], ImageSize->Small]',

		'Graphics[Table[{EdgeForm[{GrayLevel[0, 0.5]}], Hue[(-11+q+10r)/72, 1, 1, 0.6], Disk[(8-r){Cos[2Pi q/12], Sin [2Pi q/12]}, (8-r)/3]}, {r, 6}, {q, 12}]]',

		'(* Embedding objects in a Table. *)',
		'Table[RGBColor[1, g, 0], {g, 0, 1, 0.05}]',
		'Table[Plot[x^i Sin[j Pi x], {x, 0, 2}],{i, 2},{j, 2}]//MatrixForm',

		'(**** Image ****)',
		'jpg1 = Import["ExampleData/Einstein.jpg"]',
		'ImageChannels[jpg1]',
		'ImageColorSpace[jpg1]',

		'jpg2 = Import["ExampleData/sunflowers.jpg"]',
		'ImageColorSpace[jpg2]',
		'Binarize[jpg2]',
		'ImageColorSpace[Binarize[jpg2]]',

		'(* We also handle, GIF, TIF, and PNG, among others. *)',

		'(**** 3D Plots and Graphics ****)',

		'Graphics3D[Arrow[{{1, 1, -1}, {2, 2, 0}, {3, 3, -1}, {4, 4, 0}}]]',
		'Graphics3D[{Darker[Yellow], Sphere[{{-1, 0, 0}, {1, 0, 0}, {0, 0, Sqrt[3.]}}, 1]}]',
		// 'Graphics3D[Octahedron[{{0,0,0}, {1,1,1}}, 2]]',  // Investigate - timeout error
		'Graphics3D[{ Cylinder[{{1,1,1}, {10,10,10}}], Cylinder[{{-1,-1,-1}, {-10,-10,-10}}] }]',
		'Graphics3D[Polygon[Table[{Cos[2 Pi k/6], Sin[2 Pi k/6], 0}, {k, 0, 5}]]]',

		'(* A 3D grid of points.\n\
Orient so the long diagonal becomes a point to see the kinds of difficulties visualizing a 3D lattice in 2D: *)\n\
Graphics3D[Table[Point[{x, y, z}], {x, 5}, {y, 5}, {z, 5}]]',
		'Plot3D[Sin[x y], {x, -2, 2}, {y, -2, 2}, Mesh->Full, PlotPoints->21, TicksStyle->{Darker[Magenta], Darker[Blue]}]',
		'Plot3D[ Abs[Zeta[x + I y] ], {x, -1, 2}, {y, 2, 20}, PlotPoints->30]',

		'(**** Combinatorica: for Implementing Discrete Mathematics. ****)',
		'Needs["DiscreteMath`CombinatoricaV0.9`"]',
		'ShowGraph[K[6,6,6]]',
		'ShowGraph[ CirculantGraph[20, RandomSubset[Range[10]]] ]',
		'FerrersDiagram[RandomInteger[{0, 3}, 50]]'
	]);
}
