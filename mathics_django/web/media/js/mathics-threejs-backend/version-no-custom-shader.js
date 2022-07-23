{
	"name": "@mathicsorg/mathics-threejs-backend",
	"version": "1.0.3",
	"threejs_revision": 135,
	"description": "Mathics 3D Graphics backend using three.js",
	"source": "src/index.js",
	"main": "docs/build.js",
	"repository": {
		"type": "git",
		"url": "git+https://github.com/Mathics3/mathics-threejs-backend.git"
	},
	"keywords": [
		"graphics",
		"3d",
		"mathics",
		"three.js",
		"fast",
		"easy"
	],
	"author": "The Mathics Team",
	"license": "GPL-3.0",
	"bugs": {
		"url": "https://github.com/Mathics3/mathics-threejs-backend/issues"
	},
	"homepage": "https://github.com/Mathics3/mathics-threejs-backend",
	"scripts": {
		"approve": "backstop approve",
		"build": "rollup src/index.js --file docs/tmp.js --format iife && minify docs/tmp.js > docs/build.js && rm docs/tmp.js",
		"build-fast": "rollup src/index.js --file docs/build.js --format iife",
		"start-server": "node scripts/server.js",
		"test": "node scripts/test.js"
	},
	"dependencies": {
		"express": "^4"
	},
	"devDependencies": {
		"backstopjs": "^6",
		"minify": "^7",
		"rollup": "^2"
	}
}
