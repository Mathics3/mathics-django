const drawFunctions = {
	point: (element, canvasSize) => {
		const geometry = new THREE.Geometry();

		geometry.vertices = element.coords.map(
			(coordinate) => new THREE.Vector3(...coordinate[0])
		);

		return new THREE.Points(
			geometry,
			new THREE.ShaderMaterial({
				transparent: true,
				uniforms: {
					size: { value: element.pointSize * canvasSize * 0.5 },
					color: { value: new THREE.Vector4(...element.color, 1) },
				},
				vertexShader: THREE.ShaderLib.points.vertexShader,
				fragmentShader: `
					uniform vec4 color;

					void main() {
						if (length(gl_PointCoord - vec2(0.5)) > 0.5) discard;

						gl_FragColor = color;
					}
				`
			})
		);
	},
	line: (element) => {
		return new THREE.Line(
			new THREE.BufferGeometry().setFromPoints(
				element.coords.map(
					(coordinate) => new THREE.Vector3(...coordinate[0])
				)
			),
			new THREE.LineBasicMaterial({
				color: new THREE.Color(...element.color).getHex()
			})
		);
	},
	polygon: (element) => {
		let geometry;

		if (element.coords.length === 3) { // triangle (also usued in cubes)
			geometry = new THREE.Geometry();

			geometry.vertices = element.coords.map(
				(coordinate) => new THREE.Vector3(...coordinate[0])
			);

			geometry.faces.push(new THREE.Face3(0, 1, 2));
			geometry.faces.push(new THREE.Face3(0, 2, 1));
		} else {
			const polygonShape = new THREE.Shape();

			polygonShape.moveTo(...element.coords[0][0]);

			for (let i = 1; i < element.coords.length; i++) {
				polygonShape.lineTo(...element.coords[i][0]);
			}

			geometry = new THREE.ExtrudeGeometry(polygonShape, {
				depth: 0,
				steps: 0,
				bevelEnabled: false
			});
		};

		geometry.computeFaceNormals();

		return new THREE.Mesh(geometry, new THREE.MeshLambertMaterial({
			color: new THREE.Color(...element.faceColor).getHex()
		}));
	},
	sphere: (element) => {
		const spheres = new THREE.InstancedMesh(
			new THREE.SphereGeometry(element.radius, 48, 48),
			new THREE.MeshLambertMaterial({
				color: new THREE.Color(...element.faceColor).getHex()
			}),
			element.coords.length
		);

		element.coords.forEach((coordinate, i) => spheres.setMatrixAt(
			i,
			new THREE.Matrix4()
				.setPosition(new THREE.Vector3(...coordinate[0]))
		));

		return spheres;
	},
	cube: (element) => {
		const cube = new THREE.Mesh(
			new THREE.BoxGeometry(...element.size[0]),
			new THREE.MeshLambertMaterial({
				color: new THREE.Color(...element.faceColor).getHex()
			})
		);

		cube.position.set(...element.position[0]);

		return cube;
	}
};

function drawGraphics3D(container, data) {
	// data is decoded JSON data such as
	// {'elements': [{'coords': [[[1, 0, 0], null], [[1, 1, 1], null], [[0, 0, 1], null]], 'type': 'polygon', 'faceColor': [0, 0, 0, 1]}], 'axes': {}, 'extent': {'zmax': 1, 'ymax': 1, 'zmin': 0, 'xmax': 1, 'xmin': 0, 'ymin': 0}, 'lighting': []}
	// the nulls are the 'scaled' parts of coordinates that depend on the
	// size of the final graphics (see Mathematica's Scaled). TODO.

	// TODO: update the size of the container dynamically
	// (we also need some mechanism to update the enclosing <mspace>).

	// axes are created using the information in data.axes such as
	// {'axes': {'hasaxes': [true, true, false], 'ticks': [[large_ticks], [small_ticks], [tick_labels]]}

	// lights are created using the information in data.lighing such as
	// {'type': 'Ambient', 'color': [0.3, 0.2, 0.4]}
	// {'type': 'Directional', 'color': [0.3, 0.2, 0.4], 'position': [2, 0, 2]}

	// TODO: shading, handling of VertexNormals.

	let canvasSize = Math.min(400, window.innerWidth * 0.75);

	let hasAxes, isMouseDown = false,
		theta, onMouseDownTheta, phi, onMouseDownPhi;

	// where the camera is looking (initialized on center of the scene)
	const focus = new THREE.Vector3(
		0.5 * (data.extent.xmin + data.extent.xmax),
		0.5 * (data.extent.ymin + data.extent.ymax),
		0.5 * (data.extent.zmin + data.extent.zmax)
	);

	const viewPoint = new THREE.Vector3(...data.viewpoint).sub(focus);
	const radius = viewPoint.length();

	onMouseDownTheta = theta = Math.acos(viewPoint.z / radius);
	onMouseDownPhi = phi = (Math.atan2(viewPoint.y, viewPoint.x) + 2 * Math.PI) % (2 * Math.PI);

	const scene = new THREE.Scene();

	const camera = new THREE.PerspectiveCamera(
		35,           // field of view
		1,            // aspect ratio
		0.1 * radius, // near plane
		1000 * radius // far plane
	);

	function updateCameraPosition() {
		camera.position.set(
			radius * Math.sin(theta) * Math.cos(phi),
			radius * Math.sin(theta) * Math.sin(phi),
			radius * Math.cos(theta)
		).add(focus);

		camera.lookAt(focus);
	}

	updateCameraPosition();
	camera.up.copy(new THREE.Vector3(0, 0, 1));

	scene.add(camera);

	function addLight(element) {
		const colorHex = new THREE.Color(...element.color).getHex();

		let light;

		if (element.type === 'Ambient') {
			light = new THREE.AmbientLight(colorHex);
		} else if (element.type === 'Directional') {
			light = new THREE.DirectionalLight(colorHex, 1);
		} else if (element.type === 'Spot') {
			light = new THREE.SpotLight(colorHex);
			light.position.set(...element.position);
			light.target.position.set(...element.target);
			light.target.updateMatrixWorld(); // this fixes bug in THREE.js
			light.angle = element.angle;
		} else if (element.type === 'Point') {
			light = new THREE.PointLight(colorHex);
			light.position.set(...element.position);

			// add visible light sphere
			const lightSphere = new THREE.Mesh(
				new THREE.SphereGeometry(0.007 * radius, 16, 8),
				new THREE.MeshBasicMaterial({ color: colorHex })
			);
			lightSphere.position.copy(light.position);

			scene.add(lightSphere);
		} else {
			alert('Error: Internal Light Error', element.type);

			return;
		}

		return light;
	}

	function getInitialLightPosition(element) {
		// initial light position in spherical polar coordinates
		if (element.position instanceof Array) {
			const temporaryPosition = new THREE.Vector3(...element.position);

			const result = {
				radius: radius * temporaryPosition.length(),
				phi: 0,
				theta: 0
			};

			if (temporaryPosition.lenght !== 0) {
				result.phi = (Math.atan2(temporaryPosition.y, temporaryPosition.x) + 2 * Math.PI) % (2 * Math.PI);
				result.theta = Math.asin(temporaryPosition.z / result.radius);
			}

			return result;
		}
	}

	function positionLights() {
		lights.forEach((light, i) => {
			if (light instanceof THREE.DirectionalLight) {
				light.position.set(
					initialLightPosition[i].radius * Math.sin(theta + initialLightPosition[i].theta) * Math.cos(phi + initialLightPosition[i].phi),
					initialLightPosition[i].radius * Math.sin(theta + initialLightPosition[i].theta) * Math.sin(phi + initialLightPosition[i].phi),
					initialLightPosition[i].radius * Math.cos(theta + initialLightPosition[i].theta)
				).add(focus);
			}
		});
	}

	const lights = new Array(data.lighting.length);
	const initialLightPosition = new Array(data.lighting.length);

	data.lighting.forEach((light, i) => {
		initialLightPosition[i] = getInitialLightPosition(light);

		lights[i] = addLight(light);

		scene.add(lights[i]);
	});

	const boundingBox = new THREE.Mesh(new THREE.BoxGeometry(
		data.extent.xmax - data.extent.xmin,
		data.extent.ymax - data.extent.ymin,
		data.extent.zmax - data.extent.zmin
	));

	boundingBox.position.copy(focus);

	const boundingBoxEdges = new THREE.LineSegments(
		new THREE.EdgesGeometry(boundingBox.geometry),
		new THREE.LineBasicMaterial({ color: 0x666666 })
	);

	boundingBoxEdges.position.copy(focus);

	scene.add(boundingBoxEdges);

	// draw the axes
	if (data.axes.hasaxes instanceof Array) {
		hasAxes = new Array(data.axes.hasaxes[0], data.axes.hasaxes[1], data.axes.hasaxes[2]);
	} else if (data.axes.hasaxes instanceof Boolean) {
		if (data.axes) {
			hasAxes = new Array(true, true, true);
		} else {
			hasAxes = new Array(false, false, false);
		}
	} else {
		hasAxes = new Array(false, false, false);
	}

	const axesGeometry = [];
	const axesIndexes = [
		[[0, 5], [1, 4], [2, 7], [3, 6]],
		[[0, 2], [1, 3], [4, 6], [5, 7]],
		[[0, 1], [2, 3], [4, 5], [6, 7]]
	];
	const axesLines = new Array(3);

	for (let i = 0; i < 3; i++) {
		if (hasAxes[i]) {
			axesGeometry[i] = new THREE.Geometry();

			axesGeometry[i].vertices.push(new THREE.Vector3().addVectors(
				boundingBox.geometry.vertices[axesIndexes[i][0][0]], boundingBox.position
			));
			axesGeometry[i].vertices.push(new THREE.Vector3().addVectors(
				boundingBox.geometry.vertices[axesIndexes[i][0][1]], boundingBox.position
			));

			axesLines[i] = new THREE.Line(
				axesGeometry[i],
				new THREE.LineBasicMaterial({
					color: 0x000000,
					linewidth: 1.5
				})
			);

			scene.add(axesLines[i]);
		}
	}

	function positionAxes() {
		// automatic axes placement
		let nearJ, nearLenght = 10 * radius, farJ, farLenght = 0;

		const temporaryVector = new THREE.Vector3();
		for (let i = 0; i < 8; i++) {
			temporaryVector.addVectors(
				boundingBox.geometry.vertices[i],
				boundingBox.position
			).sub(camera.position);

			const temporaryLenght = temporaryVector.length();

			if (temporaryLenght < nearLenght) {
				nearLenght = temporaryLenght;
				nearJ = i;
			} else if (temporaryLenght > farLenght) {
				farLenght = temporaryLenght;
				farJ = i;
			}
		}
		for (let i = 0; i < 3; i++) {
			if (hasAxes[i]) {
				let maxJ, maxLenght = 0;

				for (let j = 0; j < 4; j++) {
					if (axesIndexes[i][j][0] !== nearJ &&
						axesIndexes[i][j][1] !== nearJ &&
						axesIndexes[i][j][0] !== farJ &&
						axesIndexes[i][j][1] !== farJ
					) {
						const edge = new THREE.Vector3().subVectors(
							toCanvasCoords(boundingBox.geometry.vertices[axesIndexes[i][j][0]]),
							toCanvasCoords(boundingBox.geometry.vertices[axesIndexes[i][j][1]])
						);
						edge.z = 0;

						if (edge.length() > maxLenght) {
							maxLenght = edge.length();
							maxJ = j;
						}
					}
				}
				axesLines[i].geometry.vertices[0].addVectors(
					boundingBox.geometry.vertices[axesIndexes[i][maxJ][0]],
					boundingBox.position
				);
				axesLines[i].geometry.vertices[1].addVectors(
					boundingBox.geometry.vertices[axesIndexes[i][maxJ][1]],
					boundingBox.position
				);
				axesLines[i].geometry.verticesNeedUpdate = true;
			}
		}

		updateAxes();
	}

	// axes ticks
	const tickMaterial = new THREE.LineBasicMaterial({
		color: 0x000000,
		linewidth: 1.2
	});
	const ticks = new Array(3),
		ticksSmall = new Array(3),
		tickLength = 0.005 * radius;

	for (let i = 0; i < 3; i++) {
		if (hasAxes[i]) {
			ticks[i] = [];

			for (let j = 0; j < data.axes.ticks[i][0].length; j++) {
				const tickGeometry = new THREE.Geometry();

				tickGeometry.vertices.push(new THREE.Vector3());
				tickGeometry.vertices.push(new THREE.Vector3());

				ticks[i].push(new THREE.Line(tickGeometry, tickMaterial));

				scene.add(ticks[i][j]);
			}

			ticksSmall[i] = [];

			for (let j = 0; j < data.axes.ticks[i][1].length; j++) {
				const tickGeometry = new THREE.Geometry();

				tickGeometry.vertices.push(new THREE.Vector3());
				tickGeometry.vertices.push(new THREE.Vector3());

				ticksSmall[i].push(new THREE.Line(tickGeometry, tickMaterial));

				scene.add(ticksSmall[i][j]);
			}
		}
	}

	function getTickDir(i) {
		const tickDir = new THREE.Vector3();

		if (i === 0) {
			if (0.25 * Math.PI < theta && theta < 0.75 * Math.PI) {
				if (axesGeometry[0].vertices[0].z > boundingBox.position.z) {
					tickDir.setZ(-tickLength);
				} else {
					tickDir.setZ(tickLength);
				}
			} else {
				if (axesGeometry[0].vertices[0].y > boundingBox.position.y) {
					tickDir.setY(-tickLength);
				} else {
					tickDir.setY(tickLength);
				}
			}
		} else if (i === 1) {
			if (0.25 * Math.PI < theta && theta < 0.75 * Math.PI) {
				if (axesGeometry[1].vertices[0].z > boundingBox.position.z) {
					tickDir.setZ(-tickLength);
				} else {
					tickDir.setZ(tickLength);
				}
			} else {
				if (axesGeometry[1].vertices[0].x > boundingBox.position.x) {
					tickDir.setX(-tickLength);
				} else {
					tickDir.setX(tickLength);
				}
			}
		} else if (i === 2) {
			if ((0.25 * Math.PI < phi && phi < 0.75 * Math.PI) || (1.25 * Math.PI < phi && phi < 1.75 * Math.PI)) {
				if (axesGeometry[2].vertices[0].x > boundingBox.position.x) {
					tickDir.setX(-tickLength);
				} else {
					tickDir.setX(tickLength);
				}
			} else {
				if (axesGeometry[2].vertices[0].y > boundingBox.position.y) {
					tickDir.setY(-tickLength);
				} else {
					tickDir.setY(tickLength);
				}
			}
		}

		return tickDir;
	}

	function updateAxes() {
		for (let i = 0; i < 3; i++) {
			if (hasAxes[i]) {
				let tickDir = getTickDir(i);

				for (let j = 0; j < data.axes.ticks[i][0].length; j++) {
					let value = data.axes.ticks[i][0][j];

					ticks[i][j].geometry.vertices[0].copy(axesGeometry[i].vertices[0]);
					ticks[i][j].geometry.vertices[1].addVectors(
						axesGeometry[i].vertices[0],
						tickDir
					);

					if (i === 0) {
						ticks[i][j].geometry.vertices[0].x = value;
						ticks[i][j].geometry.vertices[1].x = value;
					} else if (i === 1) {
						ticks[i][j].geometry.vertices[0].y = value;
						ticks[i][j].geometry.vertices[1].y = value;
					} else if (i === 2) {
						ticks[i][j].geometry.vertices[0].z = value;
						ticks[i][j].geometry.vertices[1].z = value;
					}

					ticks[i][j].geometry.verticesNeedUpdate = true;
				}

				for (let j = 0; j < data.axes.ticks[i][1].length; j++) {
					let value = data.axes.ticks[i][1][j];

					ticksSmall[i][j].geometry.vertices[0].copy(axesGeometry[i].vertices[0]);
					ticksSmall[i][j].geometry.vertices[1].addVectors(
						axesGeometry[i].vertices[0],
						tickDir.clone().multiplyScalar(0.5)
					);

					if (i === 0) {
						ticksSmall[i][j].geometry.vertices[0].x = value;
						ticksSmall[i][j].geometry.vertices[1].x = value;
					} else if (i === 1) {
						ticksSmall[i][j].geometry.vertices[0].y = value;
						ticksSmall[i][j].geometry.vertices[1].y = value;
					} else if (i === 2) {
						ticksSmall[i][j].geometry.vertices[0].z = value;
						ticksSmall[i][j].geometry.vertices[1].z = value;
					}

					ticksSmall[i][j].geometry.verticesNeedUpdate = true;
				}
			}
		}
	}

	updateAxes();

	// axes numbering using divs
	const tickNumbers = new Array(3);

	for (let i = 0; i < 3; i++) {
		if (hasAxes[i]) {
			tickNumbers[i] = new Array(data.axes.ticks[i][0].length);

			for (let j = 0; j < tickNumbers[i].length; j++) {
				let color = 'black';

				if (i < data.axes.ticks_style.length) {
					color = new THREE.Color(...data.axes.ticks_style[i])
						.getStyle();
				}

				tickNumbers[i][j] = document.createElement('div');
				tickNumbers[i][j].innerHTML = data.axes.ticks[i][2][j]
					.replace('0.', '.');

				// handle minus signs
				if (data.axes.ticks[i][0][j] >= 0) {
					tickNumbers[i][j].style.paddingLeft = '0.5em';
				} else {
					tickNumbers[i][j].style.paddingLeft = 0;
				}

				tickNumbers[i][j].style.position = 'absolute';
				tickNumbers[i][j].style.fontSize = '0.8em';
				tickNumbers[i][j].style.color = color;
				container.appendChild(tickNumbers[i][j]);
			}
		}
	}

	function toCanvasCoords(position) {
		const temporaryPosition = position.clone().applyMatrix4(
			new THREE.Matrix4().multiplyMatrices(
				camera.projectionMatrix,
				camera.matrixWorldInverse
			)
		);

		return new THREE.Vector3(
			(temporaryPosition.x + 1) * 200,
			(1 - temporaryPosition.y) * 200,
			(temporaryPosition.z + 1) * 200
		);
	}

	function positionTickNumbers() {
		for (let i = 0; i < 3; i++) {
			if (hasAxes[i]) {
				for (let j = 0; j < tickNumbers[i].length; j++) {
					const tickPosition = toCanvasCoords(
						ticks[i][j].geometry.vertices[0].clone().add(
							new THREE.Vector3().subVectors(
								ticks[i][j].geometry.vertices[0],
								ticks[i][j].geometry.vertices[1]
							).multiplyScalar(6)
						)
					).multiplyScalar(canvasSize / 400);

					// distance of the bounding box
					tickPosition.setX(tickPosition.x - 8);
					tickPosition.setY(tickPosition.y - 8);

					tickNumbers[i][j].style.position = `absolute`;
					tickNumbers[i][j].style.left = `${tickPosition.x}px`;
					tickNumbers[i][j].style.top = `${tickPosition.y}px`;

					if (tickPosition.x < 5 || tickPosition.x > 395 || tickPosition.y < 5 || tickPosition.y > 395) {
						tickNumbers[i][j].style.display = 'none';
					}
					else {
						tickNumbers[i][j].style.display = '';
					}
				}
			}
		}
	}

	// plot the primatives
	data.elements.forEach((element) => {
		scene.add(drawFunctions[element.type](element, canvasSize));
	});

	// renderer (set preserveDrawingBuffer to deal with issue of weird canvas content after switching windows)

	const renderer = new THREE.WebGLRenderer({
		antialias: true,
		preserveDrawingBuffer: true,
		alpha: true
	});

	renderer.setSize(canvasSize, canvasSize);
	renderer.setPixelRatio(window.devicePixelRatio);
	container.appendChild(renderer.domElement);

	function render() {
		positionLights();
		renderer.render(scene, camera);
	}

	function scaleInView() {
		const proj2d = new THREE.Vector3();

		let temporaryFOV = 0;

		for (let i = 0; i < 8; i++) {
			proj2d.addVectors(
				boundingBox.geometry.vertices[i],
				boundingBox.position
			).applyMatrix4(camera.matrixWorldInverse);

			temporaryFOV = Math.max(
				temporaryFOV,
				114.59 * Math.max(
					Math.abs(Math.atan(proj2d.x / proj2d.z) / camera.aspect),
					Math.abs(Math.atan(proj2d.y / proj2d.z))
				)
			);
		}

		camera.fov = temporaryFOV + 5;
		camera.updateProjectionMatrix();
	}

	function onDocumentMouseDown(event) {
		event.preventDefault();

		isMouseDown = true;
		isShiftDown = false;
		isCtrlDown = false;

		onMouseDownTheta = theta;
		onMouseDownPhi = phi;

		onMouseDownPosition.x = event.clientX;
		onMouseDownPosition.y = event.clientY;

		onMouseDownFocus = new THREE.Vector3().copy(focus);
	}

	function onDocumentMouseMove(event) {
		event.preventDefault();

		if (isMouseDown) {
			positionTickNumbers();

			if (event.shiftKey) { // pan
				if (!isShiftDown) {
					isShiftDown = true;
					onMouseDownPosition.x = event.clientX;
					onMouseDownPosition.y = event.clientY;
					autoRescale = false;
					container.style.cursor = 'move';
				}

				const cameraX = new THREE.Vector3(
					- radius * Math.cos(theta) * Math.sin(phi) * (theta < 0.5 * Math.PI ? 1 : -1),
					radius * Math.cos(theta) * Math.cos(phi) * (theta < 0.5 * Math.PI ? 1 : -1),
					0
				).normalize();

				const cameraY = new THREE.Vector3().cross(
					new THREE.Vector3()
						.sub(focus, camera.position)
						.normalize(),
					cameraX
				);

				focus.x = onMouseDownFocus.x + (radius / canvasSize) * (cameraX.x * (onMouseDownPosition.x - event.clientX) + cameraY.x * (onMouseDownPosition.y - event.clientY));
				focus.y = onMouseDownFocus.y + (radius / canvasSize) * (cameraX.y * (onMouseDownPosition.x - event.clientX) + cameraY.y * (onMouseDownPosition.y - event.clientY));
				focus.z = onMouseDownFocus.z + (radius / canvasSize) * (cameraY.z * (onMouseDownPosition.y - event.clientY));

				updateCameraPosition();
			} else if (event.ctrlKey) { // zoom
				if (!isCtrlDown) {
					isCtrlDown = true;
					onCtrlDownFov = camera.fov;
					onMouseDownPosition.x = event.clientX;
					onMouseDownPosition.y = event.clientY;
					autoRescale = false;
					container.style.cursor = 'crosshair';
				}
				camera.fov = Math.max(
					1,
					Math.min(
						onCtrlDownFov + 20 * Math.atan((event.clientY - onMouseDownPosition.y) / 50),
						150
					)
				);

				camera.updateProjectionMatrix();
			} else { // spin
				if (isCtrlDown || isShiftDown) {
					onMouseDownPosition.x = event.clientX;
					onMouseDownPosition.y = event.clientY;
					isShiftDown = false;
					isCtrlDown = false;
					container.style.cursor = 'pointer';
				}

				phi = 2 * Math.PI * (onMouseDownPosition.x - event.clientX) / canvasSize + onMouseDownPhi;
				phi = (phi + 2 * Math.PI) % (2 * Math.PI);
				theta = 2 * Math.PI * (onMouseDownPosition.y - event.clientY) / canvasSize + onMouseDownTheta;
				const epsilon = 1e-12; // prevents spinnging from getting stuck
				theta = Math.max(Math.min(Math.PI - epsilon, theta), epsilon);

				updateCameraPosition();
			}

			render();
		} else {
			container.style.cursor = 'pointer';
		}
	}

	function onDocumentMouseUp(event) {
		event.preventDefault();

		isMouseDown = false;
		container.style.cursor = 'pointer';

		if (autoRescale) {
			scaleInView();
			render();
		}

		positionAxes();
		render();
		positionTickNumbers();
	}

	// bind mouse events
	container.addEventListener('mousemove', onDocumentMouseMove);
	container.addEventListener('mousedown', onDocumentMouseDown);
	container.addEventListener('mouseup', onDocumentMouseUp);

	window.addEventListener('resize', () => {
		canvasSize = Math.min(400, window.innerWidth * 0.75);

		renderer.setPixelRatio(window.devicePixelRatio);
		renderer.setSize(canvasSize, canvasSize);

		positionTickNumbers();
	});

	const onMouseDownPosition = new THREE.Vector2();

	let autoRescale = true;

	updateCameraPosition();
	positionAxes();
	render(); // rendering twice updates camera.matrixWorldInverse so that scaleInView works properly
	scaleInView();
	render();
	positionTickNumbers();
}