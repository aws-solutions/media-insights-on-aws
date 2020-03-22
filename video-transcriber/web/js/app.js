/**
 Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.

 Licensed under the Apache License, Version 2.0 (the "License").
 You may not use this file except in compliance with the License.
 A copy of the License is located at

 http://www.apache.org/licenses/LICENSE-2.0

 or in the "license" file accompanying this file. This file is distributed
 on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
 express or implied. See the License for the specific language governing
 permissions and limitations under the License.
 */

/**
 * Router Declaration
 */
var router = null;

/**
 * Global site config object
 */
var siteConfig = null;

/**
 * Global video player
 */
var player = null;

/**
 * Cached compiled templates loaded once
 */
var homeTemplate = null;
var videosTemplate = null;
var videoTemplate = null;
var tweaksTemplate = null;
var vocabularyTemplate = null;

/**
 * Main application div
 */
var appDiv = null;

/**
 * Save captions timer
 */
var saveCaptionsTimer = null;

/**
 * 2 second time out for toasts
 */
console.log('Default toast time out: ' + toastr.options.timeOut);
toastr.options.timeOut = 2;
console.log('New toast time out: ' + toastr.options.timeOut);

/**
 * Formats a date for display
 */
function formatDate(date)
{
	var d = new Date(date),
		month = '' + (d.getMonth() + 1),
		day = '' + d.getDate(),
		year = d.getFullYear();

	if (month.length < 2) month = '0' + month;
	if (day.length < 2) day = '0' + day;

	return [year, month, day].join('-');
}

/**
 * Formats a date time for display
 */
function formatDateTime(date)
{
	var d = new Date(date),
		month = '' + (d.getMonth() + 1),
		day = '' + d.getDate(),
		year = d.getFullYear(),
		hours = '' + d.getHours(),
		minutes = '' + d.getMinutes();

	if (month.length < 2) month = '0' + month;
	if (day.length < 2) day = '0' + day;
	if (hours.length < 2) hours = '0' + hours;
	if (minutes.length < 2) minutes = '0' + minutes;

	return [year, month, day].join('-') + ' ' + [hours, minutes].join(':');
}

/**
 * Saves the tweaks
 */
function saveTweaks(tweaksRequest)
{
	var api = siteConfig.api_base + siteConfig.api_tweaks;
	console.log('[INFO] saving tweaks: ' + api);
	let axiosConfig = {
		headers: {
			'Content-Type': 'application/json;charset=UTF-8',
			'X-Api-Key': localStorage.apiKey
		}
	};
	axios.put(api,
		{ 'tweaks': tweaksRequest.split(/\r?\n/) },
		axiosConfig)
		.then(function (response)
		{
			const { tweaks } = response.data;
			tweaks.sort();
			html = tweaksTemplate({ "loading": false, "tweaks": tweaks });
			appDiv.html(html);
			toastr.success('Saved tweaks');
		})
		.catch(function (error)
		{
			console.log('[ERROR] error while saving tweaks', error);
			toastr.error('Failed to save tweaks');
		});

	return true;
}

/**
 * Get a signed put URL for this file
 */
function getSignedUrl(file)
{
	var api = siteConfig.api_base + siteConfig.api_upload + '/' + file.name;
	console.log('[INFO] fetching signed url from: ' + api);

	let axiosConfig = {
		headers: {
			'Content-Type': 'application/json;charset=UTF-8',
			'X-Api-Key': localStorage.apiKey
		}
	};

	return axios.get(api, axiosConfig);
}

/**
 * Saves the captions edited from the video player
 */
function saveCaptions(assetId, workflowId, captions)
{
	var api = siteConfig.api_base + siteConfig.api_captions + '/' + assetId + '/' + workflowId;
	console.log('[INFO] saving captions: ' + api);
	let axiosConfig = {
		headers: {
			'Content-Type': 'application/json;charset=UTF-8',
			'X-Api-Key': localStorage.apiKey
		}
	};
	axios.delete(api, axiosConfig)
		.then(async function (response)
		{
			/**
			 * Post updated web captions to dataplane as metadata
			 */
			for (var i = 0; i < captions.length; i++) {
				let fetchConfig = {
					method: 'POST',
					headers: {
						'Content-Type': 'application/json'
					},
					body: JSON.stringify({
						"OperatorName": "WebCaptions",
						"Results": captions[i],
						"WorkflowId": workflowId
					})
				};

				if (i !== captions.length - 1) {
					await fetch(siteConfig.mie_dataplane + 'metadata/' + assetId + '?paginated=true', fetchConfig);
				} else {
					await fetch(siteConfig.mie_dataplane + 'metadata/' + assetId + '?paginated=true&end=true', fetchConfig);
				}
			}

			console.log('[INFO] successfully saved captions');
			toastr.success('Saved captions');
		})
		.catch(function (error)
		{
			console.log('[ERROR] error while saving captions" ' + error);
			toastr.error('Failed to save captions');
		});

	return true;
}

/**
 * Deletes a video and all associated assets
 */
async function deleteVideo(assetId)
{
	if (!confirm('Are you sure you want to delete this video? ' +
		'This will remove any existing captions and delete ' +
		'all assets associated with this video including the ' +
		'input video file. This action cannot be undone.'))
	{
		console.log('[INFO] user cancelled request to delete a video');
		return;
	}

	console.log('[INFO] commencing delete video and associated assets: AssetId: ' + assetId);

	getAssetData(assetId).then(async function(assetData) {
		/**
		 * Check if another video asset uses the same input video
		 */
		var videoName = assetData.videoName;
		var deleteS3 = true;
		var get = await fetch(siteConfig.mie_controlplane + 'workflow/execution/', {method: 'Get'});
		var assets = await get.json();
		for (var i = 0; i < assets.length; i++) {
			var asset = assets[i];
			if (asset["Workflow"]["Name"] === "TranscribeWorkflow") {
				if (asset["Workflow"]["Stages"]["MediaconvertStage"]["Input"]["Media"]["Video"]["S3Key"].split("/").pop() === videoName && asset["AssetId"] !== assetId) {
					deleteS3 = false;
					break;
				}
			}
		}

		/**
		 * Delete the video from s3 if no other asset is using it
		 */
		if (deleteS3) {
			var api = siteConfig.api_base + siteConfig.api_video + '/' + videoName;
			console.log('[INFO] deleting video: ' + api);
			let axiosConfig = {
				headers: {
					'Content-Type': 'application/json;charset=UTF-8',
					'X-Api-Key': localStorage.apiKey
				}
			};
			await axios.delete(api, axiosConfig);
		}
		await removeAsset(assetId, assetData.workflowId).then(function (response)
		{
			toastr.success("Successfully deleted video");
			console.log('[INFO] successfully deleted video');
			document.location.hash = "#videos?t=" + new Date().getTime();
		})
		.catch(function (error)
		{
			console.log('[ERROR] failed to delete video', error);
			toastr.error('Failed to delete video, check console logs');
		});
	});

}

/**
 * Removes an asset from the MIE controlplane and dataplane
 */
async function removeAsset(assetId, workflowId) {
	/**
	 * Delete metadata in data plane
	 */
	await fetch(siteConfig.mie_dataplane + 'metadata/' + assetId, {method: 'Delete'}).then(function (response) {
		console.log('[INFO] Removed workflow execution from control plane');
	}).catch(function (error) {
		console.log('[ERROR] failed to remove workflow execution from control plane', error);
	});

	/**
	 * Delete workflow from control plane
	 */
	await fetch(siteConfig.mie_controlplane + 'workflow/execution/' + workflowId, {method: 'Delete'}).then(function (response) {
		console.log('[INFO] Removed asset from data plane');
	}).catch(function (error) {
		console.log('[ERROR] failed to remove asset from data plane', error);
	});
}

/**
 * Reprocesses a video
 */
async function reprocessVideo(assetId)
{
	if (!confirm('Are you sure you want to restart ' +
		'processing this video? This will ' +
		'overwrite existing captions, This action ' +
		'cannot be undone.'))
	{
		console.log('[INFO] user cancelled request to restart processing');
		return;
	}

	try {

		getAssetData(assetId).then(async function(assetData) {

			let fetchConfig = {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					"Name": "TranscribeWorkflow",
					"Input": {
						"Media": {
							"Video": {
								"S3Bucket": siteConfig.mie_bucket,
								"S3Key": "videos/" + assetData.videoName
							}
						}
					},
					"Configuration": {
						"TranscribeStage": {
							"Transcribe": {
								"MediaType": "Audio",
								"Enabled": true,
								"TranscribeLanguage": siteConfig.TranscribeLanguage,
								"VocabularyName": siteConfig.vocabulary_name
							}
						}
					}
				})
			};
			fetch(siteConfig.mie_controlplane + 'workflow/execution', fetchConfig)
				.then(res => res.json())
				.then(function (response) {
					console.log('[INFO] successfully started reprocessing video: ' + assetId);
					toastr.success('Started reprocessing video');
					removeAsset(assetId, assetData.workflowId)
					.then(function (response) {
						document.location.hash = "#videos?t=" + new Date().getTime();
						console.log('[INFO] successfully removed asset from dataplane and controlplane');
					})
					.catch(function (error) {
						console.log('[ERROR] failed to delete video', error);
					});
				});
		});
	}
	catch(error) {
		console.log('[ERROR] error while reprocessing video', error);
		toastr.error('Failed to reprocess video');
	}
}

/**
 * Downloads captions in WEBVTT format
 */
async function downloadCaptionsVTT(assetId, videoName)
{
	try {
		var captions = await getCaptions(assetId);
		var vtt = await exportCaptionsVTT(captions);
		toastr.success('Downloaded WEBVTT captions');
		var blob = new Blob([vtt],
			{type: "text/vtt;charset=utf-8"});
		saveAs(blob, videoName.split(".")[0] + '.vtt');
	}
	catch (error) {
		console.log('[ERROR] error while generating WEBVTT captions" ' + error);
		toastr.error('Failed to generate WEBVTT captions');
	}
}

/**
 * Downloads captions in SRT format
 */
async function downloadCaptionsSRT(assetId, videoName)
{
	try {
		var captions = await getCaptions(assetId);
		var vtt = await exportCaptionsSRT(captions);
		toastr.success('Downloaded SRT captions');
		var blob = new Blob([vtt],
			{type: "text/srt;charset=utf-8"});
		saveAs(blob, videoName.split(".")[0] + '.srt');
	}
	catch (error) {
		console.log('[ERROR] error while generating SRT captions" ' + error);
		toastr.error('Failed to generate SRT captions');
	}
}

/**
 * Converts the web captions to webvtt format
 */
async function exportCaptionsVTT(captions) {
	var webvtt = 'WEBVTT\n\n';

	for (var i in captions) {
		var caption = captions[i];

		webvtt += formatTimeWEBVTT(caption.start) + ' --> ' + formatTimeWEBVTT(caption.end) + '\n';
		webvtt += caption.caption + '\n\n';
	}

	return webvtt;
}

/**
 * Converts the web captions to srt format
 */
async function exportCaptionsSRT(captions) {
	var srt = '';

	var index = 1;

	for (var i in captions)
	{
		var caption = captions[i];
		srt += index + '\n';
		srt += formatTimeSRT(caption.start) + ' --> ' + formatTimeSRT(caption.end) + '\n';
		srt += caption.caption + '\n\n';
		index++;
	}

	return srt;
}

/**
 * Format a VTT timestamp in HH:MM:SS.mmm
 */
function formatTimeWEBVTT(timeSeconds)
{
	const ONE_HOUR = 60 * 60;
	const ONE_MINUTE = 60;
	var hours = Math.floor(timeSeconds / ONE_HOUR);
	var remainder = timeSeconds - (hours * ONE_HOUR);
	var minutes = Math.floor(remainder / 60);
	remainder = remainder - (minutes * ONE_MINUTE);
	var seconds = Math.floor(remainder);
	remainder = remainder - seconds;
	var millis = remainder;

	return (hours + '').padStart(2, '0') + ':' +
		(minutes + '').padStart(2, '0') + ':' +
		(seconds + '').padStart(2, '0') + '.' +
		(Math.floor(millis * 1000) + '').padStart(3, '0');
}

/**
 * Format an SRT timestamp in HH:MM:SS,mmm
 */
function formatTimeSRT(timeSeconds)
{
	const ONE_HOUR = 60 * 60;
	const ONE_MINUTE = 60;
	var hours = Math.floor(timeSeconds / ONE_HOUR);
	var remainder = timeSeconds - (hours * ONE_HOUR);
	var minutes = Math.floor(remainder / 60);
	remainder = remainder - (minutes * ONE_MINUTE);
	var seconds = Math.floor(remainder);
	remainder = remainder - seconds;
	var millis = remainder;

	return (hours + '').padStart(2, '0') + ':' +
		(minutes + '').padStart(2, '0') + ':' +
		(seconds + '').padStart(2, '0') + ',' +
		(Math.floor(millis * 1000) + '').padStart(3, '0');
}

/**
 * Saves the vocabulary
 */
function saveVocabulary(vocabularyRequest)
{
	var api = siteConfig.api_base + siteConfig.api_vocabulary;
	console.log('[INFO] saving vocabulary: ' + api);
	let axiosConfig = {
		headers: {
			'Content-Type': 'application/json;charset=UTF-8',
			'X-Api-Key': localStorage.apiKey
		}
	};
	axios.put(api,
		{ 'vocabulary': vocabularyRequest.split(/\r?\n/) },
		axiosConfig)
		.then(function (response)
		{
			console.log('[INFO] got response: %j', response.data);
			var vocabulary = response.data.vocabulary;
			vocabulary.sort();
			html = vocabularyTemplate({ "loading": false,
				"vocabulary": vocabulary
			});
			appDiv.html(html);
			toastr.success('Saved vocabulary');
		}).catch(function (error)
	{
		console.log('[ERROR] error while saving vocabulary', error);
		toastr.error('Failed to save vocabulary');
	});

	return true;
}

/**
 * Retrieves web captions from the dataplane and applies tweaks
 * @param assetId
 */
async function getCaptions(assetId)
{
	try
	{
		var captions = [];

		var api = siteConfig.api_base + siteConfig.api_tweaks;
		console.log('[INFO] Loading tweaks from: ' + api);
		await axios.get(api, {'headers': {'X-Api-Key': localStorage.apiKey}}).then(async function (response) {
			var { tweaks } = response.data;

			var tweaksMap = new Map();
			for (var i in tweaks) {
				var tweak = tweaks[i];

				var splits = tweak.split("=");
				if (splits.length === 2) {
					tweaksMap.set(splits[0].toLowerCase().trim(), splits[1].trim());
				}
			}

			var get = await fetch(siteConfig.mie_dataplane + 'metadata/' + assetId + '/WebCaptions', {method: 'GET'});
			var getResponse = await get.json();
			getResponse.results.caption = await applyTweaks(getResponse.results.caption, tweaksMap);

			captions.push(getResponse.results);

			while (getResponse.hasOwnProperty("cursor")) {
				get = await fetch(siteConfig.mie_dataplane + 'metadata/' + assetId + '/WebCaptions?cursor=' + getResponse.cursor, {method: 'GET'});
				getResponse = await get.json();
				getResponse.results.caption = await applyTweaks(getResponse.results.caption, tweaksMap);

				captions.push(getResponse.results);
			}
		});
		return captions;
	}
	catch (error)
	{
		console.log(error);
		return '[]';
	}


}

/**
 * Applies the tweaks to the given captions
 */
async function applyTweaks(caption, tweaksMap) {
	var words = caption.split(' ');
	for (var i = 0; i < words.length; i++) {
		var lowerWord = words[i].toLowerCase();
		if (tweaksMap.has(lowerWord)) {
			console.log("Tweak " + words[i]);
			words[i] = tweaksMap.get(lowerWord);
		}
	}
	return words.join(' ');
}

/**
 * Retrieve video key and workflowid
 */
async function getAssetData(assetId) {

	var assetData = {};

	var get = await fetch(siteConfig.mie_controlplane + 'workflow/execution/', {method: 'Get'});
	var assets = await get.json();
	for (var i = 0; i < assets.length; i++) {
		var asset = assets[i];
		if (asset["AssetId"] === assetId) {
			assetData.videoKey = asset["Workflow"]["Stages"]["MediaconvertStage"]["Input"]["Media"]["Video"]["S3Key"];
			assetData.workflowId = asset["Globals"]["MetaData"]["WorkflowExecutionId"];
			assetData.videoName = assetData.videoKey.split('/').pop();
			break;
		}
	}
	return assetData;
}

/**
 * Logs in
 */
function login(passwordEdit)
{
	window.localStorage.apiKey = passwordEdit.val();
	passwordEdit.val("");
	renderLoginLogout();
	renderNavBar();
	highlightNav('#homeLink');
	console.log('[INFO] saved API key');
	toastr.success('Saved API key');
	return true;
}

/**
 * Logs out
 */
function logout()
{
	window.localStorage.removeItem("apiKey");
	renderLoginLogout();
	renderNavBar();
	highlightNav('#homeLink');
	console.log('[INFO] cleared API key');
	toastr.success('Cleared API Key');
	return true;
}

/**
 * Renders the login logout buttons
 */
function renderLoginLogout()
{
	if (window.localStorage.apiKey)
	{
		document.getElementById('loginLogout').innerHTML =
			"<button type='button' class='btn btn-default' onclick='javascript:logout();'><i class='fa fa-key'></i> Clear API Key</button>";
	}
	else
	{
		document.getElementById('loginLogout').innerHTML =
			"<p>To transcribe videos you provide the API key specified during deployment:</p>" +
			"<button type='button' class='btn btn-primary' data-toggle='modal' data-target='#loginModalDialog'><i class='fa fa-key'></i> Enter API Key</button>";
	}
}

/**
 * UI function to see if the custom vocabulary is ready to save
 */
function checkVocabularyReady()
{
	var api = siteConfig.api_base + siteConfig.api_vocabulary;

	axios.head(api, { 'headers': { 'X-Api-Key': localStorage.apiKey }}).then(function (response)
	{
		if (response.status == 200)
		{
			$('#beingUpdated').hide();
			$('#failedUpdate').hide();
			$('#bottomButton').show();
		}
		else if (response.status == 202) {
			$('#beingUpdated').hide();
			$('#failedUpdate').show();
			$('#bottomButton').show();
		}
		else
		{
			throw new Error('Not ready yet');
		}
	}).catch(function (error)
	{
		$('#beingUpdated').show();
		$('#failedUpdate').hide();
		$('#bottomButton').hide();
		setTimeout(checkVocabularyReady, 5000);
	});
}

/**
 * Highlights the current nav
 */
function highlightNav(navId)
{
	$('.nav-link').removeClass('active');
	$(navId).addClass('active');
}

/**
 * Renders the nav bar
 */
function renderNavBar()
{
	var nav = '<li class="nav-item"><a id="homeLink" class="nav-link" href="#">Home</a></li>';

	if (window.localStorage.apiKey)
	{
		nav += '<li class="nav-item"><a id="videosLink" class="nav-link" href="#videos">Videos</a></li>';
		nav += '<li class="nav-item"><a id="vocabularyLink" class="nav-link" href="#vocabulary">Vocabulary</a></li>';
		nav += '<li class="nav-item"><a id="tweaksLink" class="nav-link" href="#tweaks">Tweaks</a></li>';
	}

	document.getElementById('navBar').innerHTML = nav;
}

/**
 * Handles dynamic routing from pages created post load
 */
function dynamicRoute(event)
{
	event.preventDefault();
	const pathName = event.target.hash;
	console.log('[INFO] navigating dynamically to: ' + pathName);
	router.navigateTo(pathName);
}

/**
 * Fired once on page load, sets up the router
 * and navigates to current hash location
 */
window.addEventListener('load', () =>
{
	/**
	 * Set up the vanilla router
	 */
	router = new Router({
		mode: 'hash',
		root: '/index.html',
		page404: function (path)
		{
			console.log('[WARN] page not found: ' + path);
		}
	});

	/**
	 * Get a reference to the application div
	 */
	appDiv = $('#app');

	Handlebars.registerHelper('ifeq', function (a, b, options) {
		if (a == b) { return options.fn(this); }
		return options.inverse(this);
	});

	/**
	 * Load site configuration and Handlebars templates
	 * and compile them after they are all loaded
	 */
	$.when(
		$.get('site_config.json'),
		$.get('templates/home.hbs'),
		$.get('templates/videos.hbs'),
		$.get('templates/video.hbs'),
		$.get('templates/tweaks.hbs'),
		$.get('templates/vocabulary.hbs')
	).done(function(site, home, videos, video, tweaks, vocabulary)
	{
		siteConfig = site[0];
		console.log('[INFO] loaded site configuration, current version: ' + siteConfig.version);

		homeTemplate = Handlebars.compile(home[0]);
		videosTemplate = Handlebars.compile(videos[0]);
		videoTemplate = Handlebars.compile(video[0]);
		tweaksTemplate = Handlebars.compile(tweaks[0]);
		vocabularyTemplate = Handlebars.compile(vocabulary[0]);

		/**
		 * Set up home template
		 */
		router.add('', () => {
			let html = homeTemplate();
			appDiv.html(html);
			highlightNav('#homeLink');
		});

		/**
		 * Set up videos template
		 */
		router.add('videos', async () => {
			highlightNav('#videosLink');
			html = videosTemplate({
				"loading": true,
				"erroredVideos": [],
				"processingVideos": [],
				"readyVideos": [],
				"refreshLink": "#videos?t=" + new Date().getTime()
			});
			appDiv.html(html);

			/**
			 * Get the video list from the control plane
			 */
			var videoList = [];
			axios.get(siteConfig.mie_controlplane + 'workflow/execution/').then(function (response) {
				var assets = response.data;
				for (var i = 0; i < assets.length; i++) {
					var asset = assets[i];
					if (asset["Workflow"]["Name"] === "TranscribeWorkflow") {
						var s3key = asset["Workflow"]["Stages"]["MediaconvertStage"]["Input"]["Media"]["Video"]["S3Key"];
						var name = s3key.split("/").pop();
						var video = {
							"Name": name,
							"AssetId": asset["AssetId"],
							"WorkflowId": asset["Globals"]["MetaData"]["WorkflowExecutionId"],
							"CurrentStage": asset["CurrentStage"]
						};
						if (video.CurrentStage === "End") {
							video.CurrentStage = "Completed";
							video.status = "READY";
						} else if (asset["Workflow"]["Stages"][video.CurrentStage]["Status"] === "Error") {
							video.status = "ERROR";
						} else {
							video.status = "PROCESSING";
						}
						videoList.push(video);
					}
				}

				/**
				 * Filter videos by status
				 */

				var processingVideos = videoList.filter(function (video) {
					return video.status === "PROCESSING";
				});

				var readyVideos = videoList.filter(function (video) {
					return video.status === "READY";
				});

				var erroredVideos = videoList.filter(function (video) {
					return video.status === "ERROR";
				});

				html = videosTemplate({
					"loading": false,
					 "erroredVideos": erroredVideos,
					"processingVideos": processingVideos,
					"readyVideos": readyVideos,
					"refreshLink": "#videos?t=" + new Date().getTime()
				});
				appDiv.html(html);
			})
			.catch(function (error)
			{
				console.log('[ERROR] failed to load videos', error);
				alert('Error loading videos, please check your API Key and network status');
			});
		});

		/**
		 * Set up video player template
		 */
		router.add('video/(:any)', (assetId) => {
			highlightNav('#videosLink');
			html = videoTemplate({
				"loading": true,
				"video": null,
				"assetId": "Video_" + assetId
			});
			appDiv.html(html);
			getAssetData(assetId).then(function(assetData) {
				var api = siteConfig.api_base + siteConfig.api_video + '/' + escape(assetData.videoName);
				console.log('[INFO] Loading video from: ' + api);
				axios.get(api, { 'headers': { 'X-Api-Key': localStorage.apiKey }}).then(function (response) {
					var { video } = response.data;
					video.WorkflowId = assetData.workflowId;
					video.AssetId = assetId;
					video.Name = assetData.videoName;
					getCaptions(assetId).then(function(captions) {
						video.Captions = JSON.stringify(captions);
						html = videoTemplate({
							"loading": false,
							"assetId": "Video_" + assetId,
							"video": video,
						});
						appDiv.html(html);
					});
				})
					.catch(function (error)
					{
						console.log("[ERROR] Failed to load video", error);
						alert("Error loading video, please check your API Key and network status");
					});
			});
		});

		/**
		 * Set up tweaks template
		 */
		router.add('tweaks', () => {
			highlightNav('#tweaksLink');
			html = tweaksTemplate({ "loading": true, "tweaks": [] });
			appDiv.html(html);
			var api = siteConfig.api_base + siteConfig.api_tweaks;
			console.log('[INFO] Loading tweaks from: ' + api);
			axios.get(api, { 'headers': { 'X-Api-Key': localStorage.apiKey }}).then(function (response) {
				const { tweaks } = response.data;
				tweaks.sort();
				html = tweaksTemplate({ "loading": false, "tweaks": tweaks });
				appDiv.html(html);
			})
				.catch(function (error)
				{
					alert('Error loading tweaks, please check your API Key and network status');
				});
		});

		/**
		 * Set up vocabulary template
		 */
		router.add('vocabulary', () => {
			highlightNav('#vocabularyLink');
			html = vocabularyTemplate({ "loading": true, "vocabulary": [] });
			appDiv.html(html);
			var api = siteConfig.api_base + siteConfig.api_vocabulary;
			console.log('[INFO] Loading vocabulary from: ' + api);
			axios.get(api, { 'headers': { 'X-Api-Key': localStorage.apiKey }}).then(function (response) {
				var vocabulary = response.data.vocabulary;
				vocabulary.sort();
				html = vocabularyTemplate({ "loading": false,
					"vocabulary": vocabulary
				});
				appDiv.html(html);
			})
				.catch(function (error)
				{
					alert('Error loading vocabulary, please check your API Key and network status');
				});
		});

		/**
		 * Make hash links work
		 */
		router.addUriListener();

		/**
		 * Render the navigation bar
		 */
		renderNavBar();

		/**
		 * Load the current fragment
		 */
		router.check();
	});
});
