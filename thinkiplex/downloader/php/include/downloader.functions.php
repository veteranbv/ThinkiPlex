<?php
// MAIN FUNCTIONS

function init_course($datas)
{
    global $pwd, $root_project_dir;
    $course_name = filter_filename($datas["course"]["name"]);
    $prev_dir = getcwd();
    $root_project_dir = getcwd();

    // Create course folder safely
    if (!file_exists($course_name)) {
        mkdir($course_name, 0777);
    }

    chdir($course_name);
    $pwd = getcwd();
    // Init Done.
    create_chap_folder($datas);
    chdir($prev_dir);
}

function create_chap_folder($datas)
{
    global $pwd;
    $i = 1;
    foreach ($datas["chapters"] as $data) {
        $chap_folder_name = "$i. " . filter_filename($data["name"]);

        // Create chapter folder safely
        if (!file_exists($chap_folder_name)) {
            mkdir($chap_folder_name, 0777);
        }

        $prev_dir = getcwd();
        chdir($chap_folder_name);
        chapterwise_download($data["content_ids"]);
        chdir($prev_dir);
        $i++;
    }
}

function chapterwise_download($datas)
{
    global $contentsdata, $p, $root_project_dir, $FFMPEG_PRESENTATION_MERGE_FLAG, $video_download_quality;
    global $download_stats; // Add global stats variable
    global $pwd; // Add pwd to global variables

    // Initialize tracking data once - store in course directory instead of PHP directory
    $tracking_file = $pwd . "/.download_tracking";
    if (!file_exists($tracking_file)) {
        @mkdir(dirname($tracking_file), 0777, true);
        file_put_contents($tracking_file, "{}");
    }
    $tracking_data = json_decode(file_get_contents($tracking_file), true) ?: [];

    $index = 1;
    foreach ($datas as $data) {
        foreach ($contentsdata as $content) {
            if ($content["id"] == $data) {
                // Create a unique content identifier for tracking downloads
                $content_id = $content["id"];
                $content_type = $content["contentable_type"];
                $content_hash = md5($content_id . '_' . $content_type);

                // Get last_modified date safely (may not exist in all content types)
                $last_modified = isset($content['updated_at']) ? $content['updated_at'] :
                                (isset($content['created_at']) ? $content['created_at'] :
                                date('Y-m-d H:i:s')); // Fallback to current date if neither exists

                // Check if this content has already been downloaded
                $is_new = !isset($tracking_data[$content_hash]);
                $is_updated = isset($tracking_data[$content_hash]) &&
                             isset($tracking_data[$content_hash]['last_modified']) &&
                             $tracking_data[$content_hash]['last_modified'] != $last_modified;

                // Skip if already downloaded and content hasn't changed
                if (!$is_new && !$is_updated) {
                    echo "Skipping " . $content["name"] . " (already downloaded)" . PHP_EOL;
                    $download_stats['skipped_items'][] = $content["name"]; // Track skipped item
                    $index++;
                    continue;
                } else if ($is_updated) {
                    // Content has been updated
                    $download_stats['updated_items'][] = $content["name"]; // Track updated item
                } else {
                    // New content
                    $download_stats['new_items'][] = $content["name"]; // Track new item
                }

                if ($content["contentable_type"] == "HtmlItem") //For Downloading Notes which are in HTML Unicode Format
                {
                    $fname = $content["slug"].".html";
                    $fname = filter_filename($fname);
                    $dc = $index.'.'.$content["name"].' Text';
                    $dc = trim(filter_filename($dc));

                    // Create directory safely
                    if (!file_exists($dc)) {
                        mkdir($dc, 0777);
                    }

                    $prev_dir = getcwd();
                    chdir($dc);
                    echo "Downloading " . $content["name"] . PHP_EOL;
                    $result = query("https://" . $p['host'] . "/api/course_player/v2/html_items/" . $content['contentable']);
                    $temp = json_decode($result, true);
                    $temp2 = unicode_decode($temp["html_item"]["html_text"]); //Store Unicode Decoded HTML Code to temp2

                    # Find a string similar to https://platform.thinkific.com/videoproxy/v1/play/*
                    $regex = '/https:\/\/platform.thinkific.com\/videoproxy\/v1\/play\/[a-zA-Z0-9]+/';
                    preg_match_all($regex, $temp2, $matches, PREG_SET_ORDER, 0);
                    $video_set_matches = array_unique($matches, SORT_REGULAR);
                    // print_r($video_set_matches);

                    # Find mp3 files inside source, should contain "https://" "thinkific.com" and ".mp3"
                    $regex = '/https:\/\/[^"]+\.mp3/';
                    preg_match_all($regex, $temp2, $audio_matches, PREG_SET_ORDER, 0);
                    $audio_matches = array_unique($audio_matches, SORT_REGULAR);

                    if (!empty($video_set_matches)) {
                        echo "Found Videoproxy in HTML Item".PHP_EOL;
                        foreach ($video_set_matches as $match) {
                            $video_url = $match[0];
                            video_downloader_videoproxy($video_url, filter_filename($content["name"]), $video_download_quality);
                        }
                    }

                    if (!empty($audio_matches)) {
                        echo "Found Audios in HTML Item".PHP_EOL;
                        foreach ($audio_matches as $match) {
                            $audio_url = $match[0];
                            $audio_name = filter_filename(basename($audio_url));
                            downloadFileChunked($audio_url, $audio_name);
                        }
                    }

                    # Find a string similar to //fast.wistia.net/embed/iframe/*
                    // $regex = '/\/\/fast.wistia.net\/embed\/iframe\/[a-zA-Z0-9]+/';
                    $regex = '/(?:\w+\.)?(wistia\.(?:com|net)|wi\.st)\/(?:medias|embed(?:\/(?:iframe|medias))?)\/([a-zA-Z0-9]+)/';

                    preg_match_all($regex, $temp2, $matches, PREG_SET_ORDER, 0);
                    $first_set_matches = array_unique($matches, SORT_REGULAR);

                    if(!empty($first_set_matches)) {
                        echo "Found Wistia Videos in HTML Item".PHP_EOL;
                        foreach($first_set_matches as $match) {
                            $embed_video_url = $match[0];

                            $wistia_id = explode("/", $embed_video_url);
                            $wistia_id = end($wistia_id);
                            video_downloader_wistia($wistia_id, filter_filename($content["name"]), $video_download_quality);
                        }
                    }

                    $fname = str_replace(" ","-",$fname);
                    $myfile = fopen($fname, "w");
                    fwrite($myfile, $temp2);
                    fclose($myfile);
                    chdir($prev_dir);
                    $index++;

                    // Update tracking information
                    $tracking_data[$content_hash] = [
                        'id' => $content_id,
                        'type' => $content_type,
                        'name' => $content["name"],
                        'last_modified' => $last_modified,
                        'downloaded_at' => date('Y-m-d H:i:s')
                    ];
                    file_put_contents($tracking_file, json_encode($tracking_data, JSON_PRETTY_PRINT));
                }

                if ($content["default_lesson_type_label"] == "Multimedia") //Download multimedia type
                {
                    $dc = $index . '. ' . $content["name"] . ' Multimedia';
                    $dc = filter_filename($dc);

                    // Skip if directory exists and content hasn't changed
                    if(file_exists($dc) && isset($tracking_data[$content_hash])) {
                        echo "Skipping " . $content["name"] . " (already downloaded)" . PHP_EOL;
                        $index++;
                        continue;
                    }

                    // Create directory safely
                    if (!file_exists($dc)) {
                        mkdir($dc, 0777);
                    }

                    $prev_dir = getcwd();
                    chdir($dc);
                    echo "Downloading " . $content["name"] . PHP_EOL;
                    $result = query("https://" . $p['host'] . "/api/course_player/v2/iframes/" . $content['contentable']);
                    $temp = json_decode($result, true);
                    $temp2 = unicode_decode($temp["iframe"]["source_url"]);
                    // file_contents can be external links so if it isn't html, just put the link in the contents of the file instead of downloading it - this if/else statement might not be needed.
                    if ((preg_match("/\b(.md|.html|\/)\b/", $temp2)) !== 0) {
                        $file_contents = file_get_contents($temp2);
                    } else {
                        echo "Not a valid documents, continuing";
                        $file_contents = $temp2;
                    }

                    if(!empty($temp["download_files"])) {
                        foreach($temp["download_files"] as $download_file) {
                            $download_file_name = filter_filename($download_file["label"]);
                            $download_file_url = $download_file["download_url"];
                            downloadFileChunked($download_file_url, $download_file_name);
                        }
                    }

                    $fname = $content["name"] . ".html";
                    $fname = preg_replace("/[^A-Za-z0-9\_\-\. \?]/", '', $fname); //You can name multimedia things that won't fit in a filename
                    $fname = filter_filename($fname);
                    $myfile = fopen($fname, "w");
                    fwrite($myfile, $file_contents);
                    fclose($myfile);
                    chdir($prev_dir);
                    $index++;

                    // Update tracking information
                    $tracking_data[$content_hash] = [
                        'id' => $content_id,
                        'type' => $content_type,
                        'name' => $content["name"],
                        'last_modified' => $last_modified,
                        'downloaded_at' => date('Y-m-d H:i:s')
                    ];
                    file_put_contents($tracking_file, json_encode($tracking_data, JSON_PRETTY_PRINT));
                }

                if ($content["contentable_type"] == "Lesson") // To download videos
                {
                    $dc = $index . '. ' . $content["name"] . ' Lesson';
                    $dc = filter_filename($dc);

                    // Skip if directory exists and content hasn't changed
                    if(file_exists($dc) && isset($tracking_data[$content_hash])) {
                        echo "Skipping " . $content["name"] . " (already downloaded)" . PHP_EOL;
                        $index++;
                        continue;
                    }

                    // Create directory safely
                    if (!file_exists($dc)) {
                        mkdir($dc, 0777);
                    }

                    $prev_dir = getcwd();
                    chdir($dc);
                    $vname = filter_filename($content['name']);
                    echo "Downloading Video : " . $vname . PHP_EOL;
                    $sendurl = "https://" . $p['host'] . "/api/course_player/v2/lessons/" . $content['contentable'];
                    $query_result = query($sendurl);
                    $temp = json_decode($query_result, true);

                    if(empty($temp["videos"])) {
                        echo "No Lesson Videos found for ".$vname.PHP_EOL;
                    } else {
                        foreach ($temp["videos"] as $video) {
                            if($video["storage_location"] == "wistia") {
                                $wistia_id = $video["identifier"];
                                video_downloader_wistia($wistia_id, $vname, $video_download_quality);
                            } else if($video["storage_location"] == "videoproxy") {
                                $video_url = "https://platform.thinkific.com/videoproxy/v1/play/".$video["identifier"];
                                video_downloader_videoproxy($video_url, $vname, $video_download_quality);
                            } else {
                                echo "Unknown video storage location. Trying Native Method for . ".$vname.PHP_EOL;
                                fdownload($video["url"], $vname);
                            }
                        }
                    }

                    // save page content along with the Video
                    if(!empty($temp["lesson"]["html_text"])) {
                        echo "Saving HTML Text for ".$vname.PHP_EOL;
                        $html_fileName = $vname . ".html";
                        file_put_contents($html_fileName, $temp["lesson"]["html_text"]);
                    }

                    if(!empty($temp["download_files"])) {
                        foreach($temp["download_files"] as $download_file) {
                            $download_file_name = filter_filename($download_file["label"]);
                            $download_file_url = $download_file["download_url"];
                            downloadFileChunked($download_file_url, $download_file_name);
                        }
                    }

                    chdir($prev_dir);
                    $index++;

                    // Update tracking information
                    $tracking_data[$content_hash] = [
                        'id' => $content_id,
                        'type' => $content_type,
                        'name' => $content["name"],
                        'last_modified' => $last_modified,
                        'downloaded_at' => date('Y-m-d H:i:s')
                    ];
                    file_put_contents($tracking_file, json_encode($tracking_data, JSON_PRETTY_PRINT));
                }

                if ($content["contentable_type"] == "Quiz") // Download Quiz Questions with Answers
                {
                    echo "Downloading " . $content["name"] . PHP_EOL;
                    // format : "https://".$p['host']."/api/course_player/v2/quizzes/".CONTENTABLE-ID
                    $dc = $index . '. ' . $content["name"] . ' Quiz';
                    $dc = filter_filename($dc);

                    // Create directory safely
                    if (!file_exists($dc)) {
                        mkdir($dc, 0777);
                    }

                    $prev_dir = getcwd();
                    chdir($dc);
                    $fname = filter_filename($content["name"] . " Answers.html");
                    $qname = filter_filename($content["name"] . " Questions.html");
                    $result = json_decode(query("https://" . $p['host'] . "/api/course_player/v2/quizzes/" . $content["contentable"]), true);
                    $file_contents_with_answers = "<h3 style='color: red;'>Answers of this Quiz are marked in RED </h3>";
                    // credited - key in choices arr base64 decode and check if string contains true or false to get option answer.
                    foreach ($result["questions"] as $qs) {
                        $choice = 'A';
                        $file_contents_with_answers = $file_contents_with_answers . ++$qs["position"] . ") " . "<strong>" . unicode_decode($qs["prompt"]) . "</strong>" . "Explanation: " . unicode_decode($qs["text_explanation"]) . "<br><br>";

                        $decoded_prompt = unicode_decode($qs["prompt"]);

                        // $pattern = '/fast.wistia.net\/embed\/iframe\/[a-zA-Z0-9]+/';
                        $pattern = '/(?:\w+\.)?(wistia\.(?:com|net)|wi\.st)\/(?:medias|embed(?:\/(?:iframe|medias))?)\/([a-zA-Z0-9]+)/';
                        preg_match_all($pattern, $decoded_prompt, $matches, PREG_SET_ORDER, 0);
                        $first_set_matches = array_unique($matches, SORT_REGULAR);
                        if(!empty($first_set_matches)) {
                            foreach($first_set_matches as $match) {
                                $embed_video_url = $match[0];
                                $wistia_id = explode("/", $embed_video_url);
                                $wistia_id = end($wistia_id);
                                video_downloader_wistia($wistia_id, "QA Video ".$qs["position"], $video_download_quality);
                            }
                        }

                        $file_contents_with_questions = $file_contents_with_questions . $qs["position"] . ") " . "<strong>" . unicode_decode($qs["prompt"]) . "</strong>" . "<br><br>";
                        foreach ($result["choices"] as $ch) {
                            if ($ch["question_id"] == $qs["id"]) {
                                $ans = base64_decode($ch["credited"]);
                                $ans = preg_replace('/\d/', '', $ans);
                                if ($ans == "true") {
                                    $file_contents_with_questions .= $choice . ") " . unicode_decode($ch["text"]) . "<br>";
                                    $file_contents_with_answers .= "<em style='color: red;'>" . $choice++ . ") " . unicode_decode($ch["text"]) . "</em>";
                                } else {
                                    $file_contents_with_questions .= $choice . ") " . unicode_decode($ch["text"]) . "<br>";
                                    $file_contents_with_answers .= $choice++ . ") " . unicode_decode($ch["text"]) . "<br>";
                                }

                            }
                        }
                    }
                    $myfile = fopen($qname, "w");
                    fwrite($myfile, $file_contents_with_questions);
                    fclose($myfile);

                    $myfile = fopen($fname, "w");
                    fwrite($myfile, $file_contents_with_answers);
                    fclose($myfile);

                    chdir($prev_dir);
                    $index++;

                    // Update tracking information
                    $tracking_data[$content_hash] = [
                        'id' => $content_id,
                        'type' => $content_type,
                        'name' => $content["name"],
                        'last_modified' => $last_modified,
                        'downloaded_at' => date('Y-m-d H:i:s')
                    ];
                    file_put_contents($tracking_file, json_encode($tracking_data, JSON_PRETTY_PRINT));
                }

                if ($content["contentable_type"] == "Assignment") // Download assignment
                {

                }

                if ($content["contentable_type"] == "Pdf") // Download PDF
                {
                    echo "Downloading " . $content["name"] . PHP_EOL;
                    // format : "https://".$p['host']."/api/course_player/v2/pdfs/".CONTENTABLE-ID
                    $dc = $index . '. ' . $content["name"];
                    $dc = filter_filename($dc);

                    // Create directory safely
                    if (!file_exists($dc)) {
                        mkdir($dc, 0777);
                    }

                    $prev_dir = getcwd();
                    chdir($dc);

                    $result = json_decode(query("https://" . $p['host'] . "/api/course_player/v2/pdfs/" . $content["contentable"]), true);
                    $pdf_url = $result["pdf"]["url"];
                    $parts = parse_url($pdf_url);
                    $fileName = basename($parts["path"]);
                    $fileName = filter_filename($fileName);
                    downloadFileChunked($pdf_url, $fileName);

                    // Update tracking information
                    $tracking_data[$content_hash] = [
                        'id' => $content_id,
                        'type' => $content_type,
                        'name' => $content["name"],
                        'last_modified' => $last_modified,
                        'downloaded_at' => date('Y-m-d H:i:s')
                    ];
                    file_put_contents($tracking_file, json_encode($tracking_data, JSON_PRETTY_PRINT));

                    chdir($prev_dir);
                    $index++;
                }

                if ($content["contentable_type"] == "Download") // Download shared files
                {
                    echo "Downloading " . $content["name"] . PHP_EOL;
                    // format : "https://".$p['host']."/api/course_player/v2/downloads/".CONTENTABLE-ID
                    $dc = $index . '. ' . $content["name"];
                    $dc = filter_filename($dc);

                    // Create directory safely
                    if (!file_exists($dc)) {
                        mkdir($dc, 0777);
                    }

                    $prev_dir = getcwd();
                    chdir($dc);
                    $result = json_decode(query("https://" . $p['host'] . "/api/course_player/v2/downloads/" . $content["contentable"]), true);
                    foreach ($result["download_files"] as $res) {
                        downloadFileChunked($res["download_url"], filter_filename($res["label"]));
                    }

                    // Update tracking information
                    $tracking_data[$content_hash] = [
                        'id' => $content_id,
                        'type' => $content_type,
                        'name' => $content["name"],
                        'last_modified' => $last_modified,
                        'downloaded_at' => date('Y-m-d H:i:s')
                    ];
                    file_put_contents($tracking_file, json_encode($tracking_data, JSON_PRETTY_PRINT));

                    chdir($prev_dir);
                    $index++;
                }

                if ($content["contentable_type"] == "Survey") // Download Survey page
                {

                }

                if ($content["contentable_type"] == "Audio") // Download Audios
                {
                    echo "Downloading " . $content["name"] . PHP_EOL;
                    // format : "https://".$p['host']."/api/course_player/v2/audio/".CONTENTABLE-ID
                    $dc = $index . '. ' . $content["name"];
                    $dc = filter_filename($dc);

                    // Create directory safely
                    if (!file_exists($dc)) {
                        mkdir($dc, 0777);
                    }

                    $prev_dir = getcwd();
                    chdir($dc);

                    $result = json_decode(query("https://" . $p['host'] . "/api/course_player/v2/audio/" . $content["contentable"]), true);
                    $audio_url = $result["audio"]["url"];
                    $parts = parse_url($audio_url);
                    $fileName = filter_filename(urldecode(basename($parts["path"])));
                    downloadFileChunked($audio_url, $fileName);

                    // Update tracking information
                    $tracking_data[$content_hash] = [
                        'id' => $content_id,
                        'type' => $content_type,
                        'name' => $content["name"],
                        'last_modified' => $last_modified,
                        'downloaded_at' => date('Y-m-d H:i:s')
                    ];
                    file_put_contents($tracking_file, json_encode($tracking_data, JSON_PRETTY_PRINT));

                    chdir($prev_dir);
                    $index++;
                }

                if ($content["contentable_type"] == "Presentation") // Download Presentation PDFs with content audio
                {
                    echo "Downloading " . $content["name"] . PHP_EOL;
                    // format : "https://".$p['host']."/api/course_player/v2/presentations/".CONTENTABLE-ID
                    $dc = $index . '. ' . $content["name"];
                    $dc = filter_filename($dc);

                    // Create directory safely
                    if (!file_exists($dc)) {
                        mkdir($dc, 0777);
                    }

                    $prev_dir = getcwd();
                    chdir($dc);
                    $result = json_decode(query("https://" . $p['host'] . "/api/course_player/v2/presentations/" . $content["contentable"]), true);
                    $pdf_url = $result["presentation"]["source_file_url"];
                    $pdf_name = $result["presentation"]["source_file_name"];
                    $pdf_name = filter_filename($pdf_name);
                    downloadFileChunked($pdf_url, $pdf_name);

                    $MULTIPURPOSE_FLAG = false;
                    exec("ffmpeg -version", $output, $return);
                    if($return == 0){
                        $MULTIPURPOSE_FLAG = true;
                    } else {
                        echo "ffmpeg is not installed. Optionally, install ffmpeg to merge presentation images and audio into a video file.".PHP_EOL;
                    }

                    $merged_video_name_check = filter_filename($content["contentable"]."-".$content["name"]."-merged.mp4");
                    if(file_exists($merged_video_name_check)){
                       $MULTIPURPOSE_FLAG = false;
                       echo "Merged PPT Video already exists. Skipping. ".$dc.PHP_EOL;
                    }

                    if($MULTIPURPOSE_FLAG == true && $FFMPEG_PRESENTATION_MERGE_FLAG == true){

                        // Download Image and Audio files
                        echo "Downloading Images and Audio files".PHP_EOL;
                        foreach ($result["presentation_items"] as $res) {
                            if ($res["audio_file_url"] != null) {
                                downloadFileChunked("https:".$res["audio_file_url"], filter_filename($res["position"].$res["audio_file_name"]));
                            }

                            if($res["image_file_url"] != null) {
                                downloadFileChunked("https:".$res["image_file_url"], filter_filename($res["position"].$res["image_file_name"]));
                            }
                        }
                        echo "Merging Images and Audio files into a video file".PHP_EOL;
                        // Merge Image and Audio files into a video file with ffmpeg
                        foreach ($result["presentation_items"] as $res) {
                            if ($res["image_file_url"] != null) {
                                $audio_name = filter_filename($res["position"].$res["audio_file_name"]);
                                $image_name = filter_filename($res["position"].$res["image_file_name"]);
                                $video_name = filter_filename($res["position"]."-slide.mp4");
                                // Single quotes aren't working in Windows.
                                $cmd = 'ffmpeg -r 1 -loop 1 -y -i "'. $image_name .'" -i "'. $audio_name .'" -c:a copy -r 1 -vcodec libx264 -shortest "'. $video_name . '" -hide_banner -loglevel error';
                                // If there is no audio file, then merge only image file with a null audio file of 5 seconds duration
                                if($res["audio_file_url"] == null){
                                    $cmd = 'ffmpeg -r 1 -loop 1 -t 5 -y -i "'. $image_name .'" -f lavfi -i anullsrc -c:a aac -r 1 -vcodec libx264 -shortest "'. $video_name . '" -hide_banner -loglevel error';
                                }
                                echo $cmd . PHP_EOL;
                                exec($cmd, $output, $return);
                                $logs = implode(PHP_EOL, $output);
                                file_put_contents($root_project_dir."/ffmpeg.log", $logs, FILE_APPEND);
                                if($return == 0){
                                    echo "Merged ".$image_name." and ".$audio_name." into ".$video_name.PHP_EOL;
                                }

                                // Unlink the temporary audio and image files with real paths
                                unlink( getcwd() . '/' . $image_name);
                                if($res["audio_file_url"] != null){
                                    unlink( getcwd() . '/' . $audio_name );
                                }
                            }
                        }
                        // Create a list.txt file with all video files
                        echo "Creating a list.txt file with all video files".PHP_EOL;
                        $files = glob("*.mp4");
                        $list = "";
                        // Sort files by position
                        usort($files, function($a, $b) {
                            $a = explode(" - ", $a);
                            $b = explode(" - ", $b);
                            return $a[0] - $b[0];
                        });

                        foreach($files as $file){
                            // If video file name includes "Merged PPT Video.mp4", then skip it
                            if(strpos($file, "Merged PPT Video.mp4") === false){
                                $list .= "file '".$file."'" . PHP_EOL;
                            }
                        }
                        file_put_contents("list.txt", $list);
                        $merged_video_name = filter_filename($content["contentable"]."-".$content["name"]."-merged.mp4");
                        // Merge all video files into a single video file
                        echo "Merging all video files into a single video file".PHP_EOL;
                        $cmd = 'ffmpeg -n -f concat -safe 0 -i list.txt -c copy "'.$merged_video_name.'" -hide_banner';
                        exec($cmd, $output, $return);
                        $logs = implode(PHP_EOL, $output);
                        file_put_contents($root_project_dir."/ffmpeg.log", $logs, FILE_APPEND);
                        if($return == 0){
                            echo "Merged all videos into one video".PHP_EOL;
                        }
                        // Unlink the temporary video files
                        foreach($files as $file){
                            unlink(getcwd() . '/' . $file);
                        }
                        // Unlink the temporary list.txt file
                        unlink(getcwd() . '/list.txt');
                    }

                    chdir($prev_dir);
                    $index++;
                }
            }
        }
    }
}

function query($url)
{
    global $clientdate, $cookiedata;
    $headers = [];

    // Add required headers for new Thinkific security
    $headers[] = 'Accept: application/json, text/plain, */*';
    $headers[] = 'Accept-Encoding: gzip, deflate, br';
    $headers[] = 'Accept-Language: en-US,en;q=0.9';
    $headers[] = 'Cache-Control: no-cache';
    $headers[] = 'Connection: keep-alive';
    $headers[] = 'DNT: 1';
    $headers[] = 'Pragma: no-cache';
    $headers[] = 'Sec-Fetch-Dest: empty';
    $headers[] = 'Sec-Fetch-Mode: cors';
    $headers[] = 'Sec-Fetch-Site: same-origin';
    $headers[] = 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36';
    $headers[] = 'sec-ch-ua: "Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"';
    $headers[] = 'sec-ch-ua-mobile: ?0';
    $headers[] = 'sec-ch-ua-platform: "macOS"';

    // Add the course-specific headers
    $headers[] = 'x-thinkific-client-date: ' . $clientdate;
    $headers[] = 'cookie: ' . $cookiedata;

    // Parse URL to get the host for referer
    $parsed_url = parse_url($url);
    $base_url = $parsed_url['scheme'] . '://' . $parsed_url['host'];

    // Initialize cURL
    $process = curl_init($url);
    curl_setopt($process, CURLOPT_HTTPGET, true);  // Use GET instead of POST
    curl_setopt($process, CURLOPT_HTTPHEADER, $headers);
    curl_setopt($process, CURLOPT_HEADER, false);
    curl_setopt($process, CURLOPT_ENCODING, 'gzip,deflate,br');
    curl_setopt($process, CURLOPT_REFERER, $base_url);
    curl_setopt($process, CURLOPT_TIMEOUT, 60);
    curl_setopt($process, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($process, CURLOPT_SSL_VERIFYPEER, false);
    curl_setopt($process, CURLOPT_SSL_VERIFYHOST, false);
    curl_setopt($process, CURLOPT_FOLLOWLOCATION, true);

    // Execute the request
    $return = curl_exec($process);

    // Get HTTP status code
    $http_status = curl_getinfo($process, CURLINFO_HTTP_CODE);

    // Debug information
    if ($http_status !== 200) {
        echo "HTTP Status: " . $http_status . PHP_EOL;
        echo "URL: " . $url . PHP_EOL;
        echo "Response: " . $return . PHP_EOL;
    }

    curl_close($process);
    return $return;
}

function fdownload($url, $file_name = null)
{
    global $clientdate, $cookiedata;
    $referer = '';
    $headers[] = 'Accept-Encoding: gzip, deflate, br';
    $headers[] = 'Sec-Fetch-Mode: cors';
    $headers[] = 'Sec-Fetch-Site: same-origin';
    $headers[] = 'x-requested-with: XMLHttpRequest';
    $headers[] = 'x-thinkific-client-date: ' . $clientdate;
    $headers[] = 'cookie: ' . $cookiedata;
    $useragent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.70 Safari/537.36';
    $process = curl_init($url);
    curl_setopt($process, CURLOPT_POST, 0);
    curl_setopt($process, CURLOPT_HTTPHEADER, $headers);
    curl_setopt($process, CURLOPT_HEADER, 1);
    curl_setopt($process, CURLOPT_USERAGENT, $useragent);
    curl_setopt($process, CURLOPT_ENCODING, 'gzip,deflate,br');
    curl_setopt($process, CURLOPT_SSL_VERIFYPEER, 0);
    curl_setopt($process, CURLOPT_SSL_VERIFYHOST, 0);
    curl_setopt($process, CURLOPT_REFERER, $referer);
    curl_setopt($process, CURLOPT_TIMEOUT, 60);
    curl_setopt($process, CURLOPT_RETURNTRANSFER, 1);
    curl_setopt($process, CURLOPT_FOLLOWLOCATION, 0);
    $return = curl_exec($process);
    curl_close($process);

    $headers = [];
    $output = rtrim($return);
    $data = explode("\n", $return);
    $headers['status'] = $data[0];
    array_shift($data);
    foreach ($data as $part) {
        $middle = explode(":", $part, 2);
        if (!isset($middle[1])) {$middle[1] = null;}
        $headers[trim($middle[0])] = trim($middle[1]);
    }
    $durl = $headers["Location"] ?? $headers["location"];
    $path = parse_url($durl);
    echo $durl . PHP_EOL;
    $p = explode("/", $path["path"]);
    $fname = end($p);

    parse_str($path["query"], $out);
    if (isset($out["filename"])) {
        $fname = $out["filename"];
    }

    // Overwrite filename if provided
    if($file_name){
        $fname = $file_name.".".pathinfo($fname, PATHINFO_EXTENSION);
    }

    $fname = filter_filename($fname);
    echo $fname . PHP_EOL;
    //$downloadedFileContents = file_get_contents($durl);
    //file_put_contents($fname, $downloadedFileContents);
    clearstatcache();
    if (file_exists($fname)) {
        return;
    }
    $downloadedFileContents = downloadFileChunked($durl, $fname);
    //echo $downloadedFileContents." bytes downloaded.";
}

function downloadFileChunked($srcUrl, $dstName, $chunkSize = 1, $returnbytes = true)
{
    global $clientdate, $cookiedata;
    clearstatcache();
    if (file_exists($dstName)) {
        return;
    }
    $http = array(
        'request_fulluri' => 1,
        'ignore_errors' => true,
        'method' => 'GET',
    );
    $headers = array();
    $headers[] = 'Accept-Encoding: gzip, deflate, br';
    $headers[] = 'Sec-Fetch-Mode: cors';
    $headers[] = 'Sec-Fetch-Site: cross-site';
    $headers[] = 'x-requested-with: XMLHttpRequest';
    $headers[] = 'x-thinkific-client-date: ' . $clientdate;
    $headers[] = 'cookie: ' . $cookiedata;
    $headers[] = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.70 Safari/537.36';
    $http['header'] = $headers;
    $context = stream_context_create(array('http' => $http));

    $chunksize = $chunkSize * (1024 * 1024); // How many bytes per chunk. By default 1MB.
    $data = '';
    $bytesCount = 0;
    $handle = fopen($srcUrl, 'rb', false, $context);
    $fp = fopen($dstName, 'w');
    if ($handle === false) {
        return false;
    }
    while (!feof($handle)) {
        $data = fread($handle, $chunksize);
        fwrite($fp, $data, strlen($data));
        if ($returnbytes) {
            $bytesCount += strlen($data);
        }
    }
    $status = fclose($handle);
    fclose($fp);
    if ($returnbytes && $status) {
        return $bytesCount; // Return number of bytes delivered like readfile() does.
    }
    return $status;
}
