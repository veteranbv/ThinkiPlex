<?php
set_time_limit(0);
require("/app/scripts/config.php");
$pwd = getcwd(); // Current working directory is already the target directory
$root_project_dir = $pwd;
$revision = "Revision 6.4 ~ 27th November 2024";

// Get target directory from environment variable (should match current directory)
$target_dir = getenv('TARGET_DIR');
if (empty($target_dir)) {
	$target_dir = '/app/data';
}

// Verify we're in the target directory
if ($pwd != $target_dir) {
	echo "Warning: Current directory ($pwd) doesn't match target directory ($target_dir). This may cause issues." . PHP_EOL;
}

// Add global variables to track download statistics
$download_stats = [
	'new_items' => [],
	'skipped_items' => [],
	'updated_items' => []
];

error_reporting(E_ALL); //Enable error reporting to see any issues
ini_set('display_errors', 1);
echo "THINKIFIC DOWNLOADER".PHP_EOL.$revision.PHP_EOL."Author : SumeetWeb ~ https://github.com/sumeetweb".PHP_EOL."Consider buying me a coffee at : https://www.ko-fi.com/sumeet".PHP_EOL."Want to download only selected videos? Thinki-Parser is available! : https://sumeetweb.github.io/Thinki-Parser/".PHP_EOL;
echo "----------------------------------------------------------".PHP_EOL;
echo "Working directory: " . $pwd . PHP_EOL;
require("/app/scripts/include/file.functions.php");
require("/app/scripts/include/downloader.functions.php");
require("/app/scripts/include/wistia.downloader.php");

// Run.
// If --json, then read from json file.
// Else, download from url.
if(in_array("--json", $argv) && isset($argv[2])) {
	$json = file_get_contents($argv[2]);
	$data = json_decode($json, true);
	if ($data === null) {
		die("Error: Invalid JSON file format".PHP_EOL);
	}
	$contentsdata = $data["contents"];
	init_course($data);
} else if(isset($argv[1])) {
	// Clean up the URL to ensure proper format
	$url = $argv[1];
	$url = preg_replace('/\/take\//', '/', $url); // Remove /take/ if present

	// Extract the course ID
	$p = parse_url($url);
	$path = explode("/", $p["path"]);
	$course_id = end($path);

	// Build the API URL
	$api_url = "https://" . $p['host'] . "/api/course_player/v2/courses/" . $course_id;
	echo "Fetching course data from: " . $api_url . PHP_EOL;

	// Get course data
	$response = query($api_url);
	if (empty($response)) {
		die("Error: Failed to fetch course data. Please check your authentication credentials.".PHP_EOL);
	}

	// Parse response
	$data = json_decode($response, true);
	if ($data === null) {
		die("Error: Invalid API response format".PHP_EOL);
	}

	if(isset($data["error"])) {
		die("API Error: ".$data["error"].PHP_EOL);
	}

	$contentsdata = $data["contents"];
	echo "Fetching Course Contents... Please Wait...".PHP_EOL;

	// Initialize course directory
	init_course($data);

	// Save course data directly in the working directory
	$course_id = $data["course"]["slug"];
	file_put_contents($course_id.".json", $response);
	echo "Saved course data to: ".$course_id.".json".PHP_EOL;

	// Display download summary
	display_download_summary();
} else {
	echo "Usage for using course url: php thinkidownloader3.php <course_url>".PHP_EOL;
	echo "Usage for selective download: php thinkidownloader3.php --json <course.json>".PHP_EOL;
}

// Function to display download summary
function display_download_summary() {
	global $download_stats;

	echo PHP_EOL . "=== DOWNLOAD SUMMARY ===" . PHP_EOL;

	if (count($download_stats['new_items']) > 0) {
		echo PHP_EOL . "🆕 NEW ITEMS DOWNLOADED (" . count($download_stats['new_items']) . "):" . PHP_EOL;
		foreach ($download_stats['new_items'] as $item) {
			echo "  • " . $item . PHP_EOL;
		}
	}

	if (count($download_stats['updated_items']) > 0) {
		echo PHP_EOL . "🔄 UPDATED ITEMS (" . count($download_stats['updated_items']) . "):" . PHP_EOL;
		foreach ($download_stats['updated_items'] as $item) {
			echo "  • " . $item . PHP_EOL;
		}
	}

	if (count($download_stats['skipped_items']) > 0) {
		echo PHP_EOL . "⏭️ SKIPPED ITEMS (" . count($download_stats['skipped_items']) . "):" . PHP_EOL;
		echo "  • " . count($download_stats['skipped_items']) . " items were already downloaded and up-to-date" . PHP_EOL;
	}

	echo PHP_EOL . "Download complete! " .
		 (count($download_stats['new_items']) + count($download_stats['updated_items'])) .
		 " items downloaded, " . count($download_stats['skipped_items']) . " items skipped." . PHP_EOL;
}
?>
