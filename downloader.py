import yt_dlp

def download_video(url, quality="360p", audio_only=False):
    format_string = "bestaudio" if audio_only else f"bestvideo[height<={quality[:-1]}]+bestaudio/best"

    ydl_opts = {
        "format": format_string,
        "outtmpl": "downloads/%(title).50s.%(ext)s",
        "merge_output_format": "mp4",
        "quiet": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)
