const drawFunctions = {
	point: (element) => {
		const geometry = new THREE.Geometry();

		element.coords.forEach((coordinate) => {
			geometry.vertices.push(new THREE.Vector3(...coordinate[0]));
		});

		return new THREE.ParticleSystem(
			geometry,
			new THREE.ParticleBasicMaterial({
				color: new THREE.Color().setRGB(...element.color).getHex(),
				size: 0.05
			})
		);
	},
	line: (element) => {
		const geometry = new THREE.Geometry();

		element.coords.forEach((coordinate) => {
			geometry.vertices.push(new THREE.Vector3(...coordinate[0]));
		});

		const line = new THREE.Line(
			geometry,
			new THREE.LineBasicMaterial({
				color: new THREE.Color().setRGB(...element.color).getHex(),
				overdraw: true
			})
		);

		// these three lines prevent grid from being put on the wrong side
		line.material.polygonOffset = true;
		line.material.polygonOffsetFactor = 1;
		line.material.polygonOffsetUnits = 1;

		return line;
	},
	polygon: (element) => {
		let geometry, material;

		const point1 = new THREE.Vector4(...element.coords[0][0]);
		const point2 = new THREE.Vector4(...element.coords[1][0]);
		const point3 = new THREE.Vector4(...element.coords[2][0]);

		if (element.coords.length === 3) { // fast return
			geometry = new THREE.Geometry();

			geometry.vertices.push(point1);
			geometry.vertices.push(point2);
			geometry.vertices.push(point3);

			geometry.faces.push(new THREE.Face3(0, 1, 2));
			geometry.faces.push(new THREE.Face3(0, 2, 1));
		} else {
			// TODO: check the 3 points are not colinear

			const vector1 = new THREE.Vector3().sub(point2, point1);
			const vector2 = new THREE.Vector3().sub(point3, point1);
			const vector3 = new THREE.Vector3().cross(vector1, vector2); // normal vector

			const normal = new THREE.Vector4(vector3.x, vector3.y, vector3.z, -vector3.dot(point1)); // point p on the plane iff p.normal = 0

			// point closest to origin - translation
			const nearest = new THREE.Vector3(
				normal.x * normal.w / (normal.x ** 2 + normal.y ** 2 + normal.z ** 2),
				normal.y * normal.w / (normal.x ** 2 + normal.y ** 2 + normal.z ** 2),
				normal.z * normal.w / (normal.x ** 2 + normal.y ** 2 + normal.z ** 2)
			);

			// angles to the z axis - rotaton
			const thetax = Math.acos(normal.z / Math.sqrt(normal.y * normal.y + normal.z ** 2));
			const thetay = Math.acos(normal.z / Math.sqrt(normal.x * normal.x + normal.z ** 2));

			// linear transformation matrix - rotation + translation
			const linearTransformation = new THREE.Matrix4()
				.makeTranslation(-nearest.x, -nearest.y, -nearest.z)
				.multiplySelf(new THREE.Matrix4().makeRotationX(thetax))
				.multiplySelf(new THREE.Matrix4().makeRotationY(thetay));

			const polygonPath = new THREE.Path();

			element.coords.forEach((coordinate, i) => {
				let temporaryVector = new THREE.Vector4(...coordinate[0], 1);

				linearTransformation.multiplyVector4(temporaryVector);

				if (i === 0) {
					polygonPath.moveTo(temporaryVector.x, temporaryVector.y);
				} else {
					polygonPath.lineTo(temporaryVector.x, temporaryVector.y);
				}
			});

			polygonPath.lineTo(polygonPath.curves[0].v1.x, polygonPath.curves[0].v1.y); // close the curve

			geometry = new THREE.ExtrudeGeometry(polygonPath.toShapes(), {
				amount: 0.0,
				steps: 0,
				bevelEnabled: false
			});

			// undo the linear transformation
			geometry.vertices.forEach((vertice, i) => {
				vertice.set(...element.coords[i][0]);
			});
		}

		geometry.computeFaceNormals();

		const color = new THREE.Color().setRGB(...element.faceColor);

		if (Detector.webgl) {
			material = new THREE.MeshPhongMaterial({
				color: color.getHex(),
				transparent: true
			});
		} else {
			material = new THREE.MeshLambertMaterial({
				color: color.getHex(),
				transparent: true,
				overdraw: true
			});
		}

		return new THREE.Mesh(geometry, material);
	},
	sphere: (element) => {
		const geometry = new THREE.Geometry();

		for (let i = 0; i < element.coords.length; i++) {
			const temporarySphere = new THREE.Mesh(
				new THREE.SphereGeometry(element.radius, 48, 48)
			);

			temporarySphere.position.set(...element.coords[i][0]);

			THREE.GeometryUtils.merge(geometry, temporarySphere);
		}

		geometry.computeFaceNormals();

		return new THREE.Mesh(
			geometry,
			new THREE.MeshPhongMaterial({
				color: new THREE.Color().setRGB(...element.faceColor).getHex(),
				transparent: true
			})
		);
	},
	cube: (element) => {
		const cube = new THREE.Mesh(
			new THREE.CubeGeometry(...element.size[0]),
			new THREE.MeshPhongMaterial({
				color: new THREE.Color().setRGB(...element.faceColor).getHex(),
				transparent: true
			})
		);

		cube.position.set(...element.position[0]);

		return cube;
	}
};

function drawGraphics3D(container, data) {
	// data is decoded JSON data such as
	// {'elements': [{'coords': [[[1.0, 0.0, 0.0], null], [[1.0, 1.0, 1.0], null], [[0.0, 0.0, 1.0], null]], 'type': 'polygon', 'faceColor': [0, 0, 0, 1]}], 'axes': {}, 'extent': {'zmax': 1.0, 'ymax': 1.0, 'zmin': 0.0, 'xmax': 1.0, 'xmin': 0.0, 'ymin': 0.0}, 'lighting': []}
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

	var renderer, boundingBox, hasAxes,
		isMouseDown = false, onMouseDownPosition,
		theta, onMouseDownTheta, phi, onMouseDownPhi;

	// center of the scene
	const center = new THREE.Vector3(
		0.5 * (data.extent.xmin + data.extent.xmax),
		0.5 * (data.extent.ymin + data.extent.ymax),
		0.5 * (data.extent.zmin + data.extent.zmax));

	// where the camera is looking
	const focus = center.clone();

	const viewPoint = new THREE.Vector3(...data.viewpoint).subSelf(focus);
	const radius = viewPoint.length();

	onMouseDownTheta = theta = Math.acos(viewPoint.z / radius);
	onMouseDownPhi = phi = (Math.atan2(viewPoint.y, viewPoint.x) + 2 * Math.PI) % (2 * Math.PI);

	// scene
	const scene = new THREE.Scene();
	scene.position = center;

	const camera = new THREE.PerspectiveCamera(
		35,           // field of view
		1,            // aspect ratio
		0.1 * radius, // near plane
		1000 * radius // far plane
	);

	function updateCameraPosition() {
		camera.position.x = radius * Math.sin(theta) * Math.cos(phi);
		camera.position.y = radius * Math.sin(theta) * Math.sin(phi);
		camera.position.z = radius * Math.cos(theta);
		camera.position.addSelf(focus);
		camera.lookAt(focus);
	}

	updateCameraPosition();
	camera.up = new THREE.Vector3(0, 0, 1);

	scene.add(camera);

	// lighting
	function addLight(l) {
		const color = new THREE.Color().setRGB(...l.color);
		var light;

		if (l.type === 'Ambient') {
			light = new THREE.AmbientLight(color.getHex());
		} else if (l.type === 'Directional') {
			light = new THREE.DirectionalLight(color.getHex(), 1);
		} else if (l.type === 'Spot') {
			light = new THREE.SpotLight(color.getHex());
			light.position.set(...l.position);
			light.target.position.set(...l.target);
			light.target.updateMatrixWorld(); // this fixes bug in THREE.js
			light.angle = l.angle;
		} else if (l.type === 'Point') {
			light = new THREE.PointLight(color.getHex());
			light.position.set(...l.position);

			// add visible light sphere
			var lightsphere = new THREE.Mesh(
				new THREE.SphereGeometry(0.007 * radius, 16, 8),
				new THREE.MeshBasicMaterial({ color: color.getHex() })
			);
			lightsphere.position = light.position;
			scene.add(lightsphere);
		} else {
			alert('Error: Internal Light Error', l.type);

			return;
		}

		return light;
	}

	function getInitLightPos(l) {
		// initial light position in spherical polar coordinates
		if (l.position instanceof Array) {
			const temporaryPosition = new THREE.Vector3(...l.position);

			const result = {
				radius: radius * temporaryPosition.length(),
				phi: 0,
				theta: 0
			};

			if (!temporaryPosition.isZero()) {
				result.phi = (Math.atan2(temporaryPosition.y, temporaryPosition.x) + 2 * Math.PI) % (2 * Math.PI);
				result.theta = Math.asin(temporaryPosition.z / result.radius);
			}

			return result;
		}
	}

	function positionLights() {
		for (let i = 0; i < lights.length; i++) {
			if (lights[i] instanceof THREE.DirectionalLight) {
				lights[i].position.x = initialLightPosition[i].radius * Math.sin(theta + initialLightPosition[i].theta) * Math.cos(phi + initialLightPosition[i].phi);
				lights[i].position.y = initialLightPosition[i].radius * Math.sin(theta + initialLightPosition[i].theta) * Math.sin(phi + initialLightPosition[i].phi);
				lights[i].position.z = initialLightPosition[i].radius * Math.cos(theta + initialLightPosition[i].theta);
				lights[i].position.addSelf(focus);
			}
		}
	}

	const lights = new Array(data.lighting.length);
	const initialLightPosition = new Array(data.lighting.length);

	for (var i = 0; i < data.lighting.length; i++) {
		initialLightPosition[i] = getInitLightPos(data.lighting[i]);

		lights[i] = addLight(data.lighting[i]);
		scene.add(lights[i]);
	}

	boundingBox = new THREE.Mesh(
		new THREE.CubeGeometry(
			data.extent.xmax - data.extent.xmin,
			data.extent.ymax - data.extent.ymin,
			data.extent.zmax - data.extent.zmin
		),
		new THREE.MeshBasicMaterial({ color: 0x666666, wireframe: true })
	);
	boundingBox.position = center;
	scene.add(boundingBox);

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
	const axesMaterial = new THREE.LineBasicMaterial({
		color: 0x000000,
		linewidth: 1.5
	});
	const axesGeometry = [];
	const axesIndexes = [
		[[0, 5], [1, 4], [2, 7], [3, 6]],
		[[0, 2], [1, 3], [4, 6], [5, 7]],
		[[0, 1], [2, 3], [4, 5], [6, 7]]
	];

	const axesMesh = new Array(3);
	for (let i = 0; i < 3; i++) {
		if (hasAxes[i]) {
			axesGeometry[i] = new THREE.Geometry();
			axesGeometry[i].vertices.push(new THREE.Vector3().add(
				boundingBox.geometry.vertices[axesIndexes[i][0][0]], boundingBox.position)
			);
			axesGeometry[i].vertices.push(new THREE.Vector3().add(
				boundingBox.geometry.vertices[axesIndexes[i][0][1]], boundingBox.position)
			);
			axesMesh[i] = new THREE.Line(axesGeometry[i], axesMaterial);
			axesMesh[i].geometry.dynamic = true;
			scene.add(axesMesh[i]);
		}
	}

	function boxEdgeLength(i, j) {
		const edge = new THREE.Vector3().sub(
			toCanvasCoords(boundingBox.geometry.vertices[axesIndexes[i][j][0]]),
			toCanvasCoords(boundingBox.geometry.vertices[axesIndexes[i][j][1]])
		);
		edge.z = 0;

		return edge.length();
	}

	function positionAxes() {
		// automatic axes placement
		let nearJ = null, nearLenght = 10 * radius, farJ = null, farLenght = 0;

		const temporaryVector = new THREE.Vector3();
		for (let i = 0; i < 8; i++) {
			temporaryVector.add(
				boundingBox.geometry.vertices[i],
				boundingBox.position
			).subSelf(camera.position);

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
				maxj = null;
				maxl = 0.0;
				for (let j = 0; j < 4; j++) {
					if (axesIndexes[i][j][0] !== nearJ &&
						axesIndexes[i][j][1] !== nearJ &&
						axesIndexes[i][j][0] !== farJ &&
						axesIndexes[i][j][1] !== farJ
					) {
						const temporaryLenght = boxEdgeLength(i, j);

						if (temporaryLenght > maxl) {
							maxl = temporaryLenght;
							maxj = j;
						}
					}
				}
				axesMesh[i].geometry.vertices[0].add(
					boundingBox.geometry.vertices[axesIndexes[i][maxj][0]],
					boundingBox.position
				);
				axesMesh[i].geometry.vertices[1].add(
					boundingBox.geometry.vertices[axesIndexes[i][maxj][1]],
					boundingBox.position
				);
				axesMesh[i].geometry.verticesNeedUpdate = true;
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
				tickgeom = new THREE.Geometry();
				tickgeom.vertices.push(new THREE.Vector3());
				tickgeom.vertices.push(new THREE.Vector3());
				ticks[i].push(new THREE.Line(tickgeom, tickMaterial));
				scene.add(ticks[i][j]);
			}

			ticksSmall[i] = [];

			for (let j = 0; j < data.axes.ticks[i][1].length; j++) {
				tickgeom = new THREE.Geometry();
				tickgeom.vertices.push(new THREE.Vector3());
				tickgeom.vertices.push(new THREE.Vector3());
				ticksSmall[i].push(new THREE.Line(tickgeom, tickMaterial));
				scene.add(ticksSmall[i][j]);
			}
		}
	}

	function getTickDir(i) {
		var tickdir = new THREE.Vector3();
		if (i === 0) {
			if (0.25 * Math.PI < theta && theta < 0.75 * Math.PI) {
				if (axesGeometry[0].vertices[0].z > boundingBox.position.z) {
					tickdir.setZ(-tickLength);
				} else {
					tickdir.setZ(tickLength);
				}
			} else {
				if (axesGeometry[0].vertices[0].y > boundingBox.position.y) {
					tickdir.setY(-tickLength);
				} else {
					tickdir.setY(tickLength);
				}
			}
		} else if (i === 1) {
			if (0.25 * Math.PI < theta && theta < 0.75 * Math.PI) {
				if (axesGeometry[1].vertices[0].z > boundingBox.position.z) {
					tickdir.setZ(-tickLength);
				} else {
					tickdir.setZ(tickLength);
				}
			} else {
				if (axesGeometry[1].vertices[0].x > boundingBox.position.x) {
					tickdir.setX(-tickLength);
				} else {
					tickdir.setX(tickLength);
				}
			}
		} else if (i === 2) {
			if ((0.25 * Math.PI < phi && phi < 0.75 * Math.PI) || (1.25 * Math.PI < phi && phi < 1.75 * Math.PI)) {
				if (axesGeometry[2].vertices[0].x > boundingBox.position.x) {
					tickdir.setX(-tickLength);
				} else {
					tickdir.setX(tickLength);
				}
			} else {
				if (axesGeometry[2].vertices[0].y > boundingBox.position.y) {
					tickdir.setY(-tickLength);
				} else {
					tickdir.setY(tickLength);
				}
			}
		}

		return tickdir;
	}

	function updateAxes() {
		for (let i = 0; i < 3; i++) {
			if (hasAxes[i]) {
				tickdir = getTickDir(i);
				let smallTickdir = tickdir.clone();
				smallTickdir.multiplyScalar(0.5);
				for (let j = 0; j < data.axes.ticks[i][0].length; j++) {
					let value = data.axes.ticks[i][0][j];

					ticks[i][j].geometry.vertices[0].copy(axesGeometry[i].vertices[0]);
					ticks[i][j].geometry.vertices[1].add(axesGeometry[i].vertices[0], tickdir);

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
					ticksSmall[i][j].geometry.vertices[1].add(axesGeometry[i].vertices[0], smallTickdir);

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
				tickNumbers[i][j] = document.createElement('div');
				tickNumbers[i][j].innerHTML = data.axes.ticks[i][2][j];

				// handle minus signs
				if (data.axes.ticks[i][0][j] >= 0) {
					tickNumbers[i][j].style.paddingLeft = '0.5em';
				} else {
					tickNumbers[i][j].style.paddingLeft = 0;
				}

				tickNumbers[i][j].style.position = 'absolute';
				tickNumbers[i][j].style.fontSize = '0.8em';
				container.appendChild(tickNumbers[i][j]);
			}
		}
	}

	function toCanvasCoords(position) {
		const positionClone = position.clone();

		const projScreenMat = new THREE.Matrix4();
		projScreenMat.multiply(camera.projectionMatrix, camera.matrixWorldInverse);
		projScreenMat.multiplyVector3(positionClone);

		return new THREE.Vector3(
			(positionClone.x + 1) * 200,
			(1 - positionClone.y) * 200,
			(positionClone.z + 1) * 200
		);
	}

	function positionticknums() {
		for (var i = 0; i < 3; i++) {
			if (hasAxes[i]) {
				for (var j = 0; j < tickNumbers[i].length; j++) {
					const tickPosition3D = ticks[i][j].geometry.vertices[0].clone();
					const tickDir = new THREE.Vector3().sub(
						ticks[i][j].geometry.vertices[0],
						ticks[i][j].geometry.vertices[1]
					);
					// tickDir.multiplyScalar(3);
					tickDir.setLength(3 * tickLength);
					tickDir.x *= 2.0;
					tickDir.y *= 2.0;

					tickPosition3D.addSelf(tickDir);

					const tickPosition = toCanvasCoords(tickPosition3D);
					tickPosition.x -= 10;
					tickPosition.y += 8;

					tickNumbers[i][j].style.left = tickPosition.x.toString() + 'px';
					tickNumbers[i][j].style.top = tickPosition.y.toString() + 'px';

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
		scene.add(drawFunctions[element.type](element));
	});

	// renderer (set preserveDrawingBuffer to deal with issue of weird canvas content after switching windows)
	if (Detector.webgl) {
		renderer = new THREE.WebGLRenderer({
			antialias: true,
			preserveDrawingBuffer: true
		});
	} else {
		renderer = new THREE.CanvasRenderer({
			antialias: true,
			preserveDrawingBuffer: true
		});

		const message = document.createElement('div');
		message.innerHTML = 'Canvas Renderer support is experimental, please enable WebGL where possible.';
		message.style.position = 'absolute';
		message.style.fontSize = '0.8em';
		message.style.color = '#FF6060';
		container.appendChild(message);
	}

	renderer.setSize(400, 400);
	container.appendChild(renderer.domElement);

	function render() {
		positionLights();
		renderer.render(scene, camera);
	}

	function scaleInView() {
		var temporaryFOV = 0;
		var proj2d = new THREE.Vector3();

		for (var i = 0; i < 8; i++) {
			proj2d.add(boundingBox.geometry.vertices[i], boundingBox.position);
			proj2d = camera.matrixWorldInverse.multiplyVector3(proj2d.clone());

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
			positionticknums();

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

				focus.x = onMouseDownFocus.x + (radius / 400) * (cameraX.x * (onMouseDownPosition.x - event.clientX) + cameraY.x * (onMouseDownPosition.y - event.clientY));
				focus.y = onMouseDownFocus.y + (radius / 400) * (cameraX.y * (onMouseDownPosition.x - event.clientX) + cameraY.y * (onMouseDownPosition.y - event.clientY));
				focus.z = onMouseDownFocus.z + (radius / 400) * (cameraX.z * (onMouseDownPosition.x - event.clientX) + cameraY.z * (onMouseDownPosition.y - event.clientY));

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

				phi = 2 * Math.PI * (onMouseDownPosition.x - event.clientX) / 400 + onMouseDownPhi;
				phi = (phi + 2 * Math.PI) % (2 * Math.PI);
				theta = 2 * Math.PI * (onMouseDownPosition.y - event.clientY) / 400 + onMouseDownTheta;
				var epsilon = 1e-12; // prevents spinnging from getting stuck
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
		positionticknums();
	}

	// bind mouse events
	container.addEventListener('mousemove', onDocumentMouseMove, false);
	container.addEventListener('mousedown', onDocumentMouseDown, false);
	container.addEventListener('mouseup', onDocumentMouseUp, false);
	onMouseDownPosition = new THREE.Vector2();
	var autoRescale = true;

	updateCameraPosition();
	positionAxes();
	render(); // rendering twice updates camera.matrixWorldInverse so that scaleInView works properly
	scaleInView();
	render();
	positionticknums();
}