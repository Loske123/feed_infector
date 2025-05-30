import os
import random
import re
import string
from datetime import datetime
from pydub import AudioSegment
import numpy as np
from moviepy import *
import argparse
from collections import defaultdict


LYRICS_FOLDER = "lyrics"
SONGS_FOLDER = "songs"
BACKGROUNDS_FOLDER = "background"
FONTS_FOLDER = "fonts"
RANDOM_CAPTIONS_FONTS_FOLDER = "random_captions_fonts"
OUTPUT_FOLDER = "output_videos"
RANDOM_CAPTIONS_FILE = "random_captions.txt"
DURATION = 15  # seconds


for folder in [LYRICS_FOLDER, SONGS_FOLDER, BACKGROUNDS_FOLDER, FONTS_FOLDER, RANDOM_CAPTIONS_FONTS_FOLDER, OUTPUT_FOLDER]:
    os.makedirs(folder, exist_ok=True)

def get_available_fonts():
    """Get list of available font files"""
    font_extensions = ('.ttf', '.otf', '.woff', '.woff2')
    fonts = []
    
    if os.path.exists(FONTS_FOLDER):
        for file in os.listdir(FONTS_FOLDER):
            if file.lower().endswith(font_extensions):
                fonts.append(os.path.join(FONTS_FOLDER, file))
    
    return fonts if fonts else ['Arial']  # Fallback to Arial if no fonts found

def get_random_caption_fonts():
    """Get list of available random caption font files"""
    font_extensions = ('.ttf', '.otf', '.woff', '.woff2')
    fonts = []
    
    if os.path.exists(RANDOM_CAPTIONS_FONTS_FOLDER):
        for file in os.listdir(RANDOM_CAPTIONS_FONTS_FOLDER):
            if file.lower().endswith(font_extensions):
                fonts.append(os.path.join(RANDOM_CAPTIONS_FONTS_FOLDER, file))
    
    return fonts if fonts else ['Arial']  # Fallback to Arial if no fonts found

def get_random_captions():
    """Read random captions from file"""
    if not os.path.exists(RANDOM_CAPTIONS_FILE):
        print(f"WARNING: {RANDOM_CAPTIONS_FILE} not found. Creating sample file...")
        # Create a sample file with some example captions
        sample_captions = [
            "🔥 This hits different 🔥",
            "When the beat drops just right ✨",
            "POV: You found your new favorite song",
            "This song lives rent-free in my head 🎵",
            "The vibes are immaculate ✨",
            "Main character energy 💫",
            "This is pure art 🎨",
            "When music becomes emotion 💭",
            "The perfect soundtrack to life 🌟",
            "This deserves more recognition 👑"
        ]
        with open(RANDOM_CAPTIONS_FILE, 'w', encoding='utf-8') as f:
            for caption in sample_captions:
                f.write(caption + '\n')
        print(f"Created sample {RANDOM_CAPTIONS_FILE} with example captions")
    
    try:
        with open(RANDOM_CAPTIONS_FILE, 'r', encoding='utf-8') as f:
            captions = [line.strip() for line in f.readlines() if line.strip()]
        return captions
    except Exception as e:
        print(f"Error reading {RANDOM_CAPTIONS_FILE}: {e}")
        return []

def pick_random_font():
    """Select a random font from available fonts"""
    fonts = get_available_fonts()
    return random.choice(fonts)

def pick_random_caption_font():
    """Select a random font from available caption fonts"""
    fonts = get_random_caption_fonts()
    return random.choice(fonts)

def pick_random_caption():
    """Select a random caption from the captions file"""
    captions = get_random_captions()
    if not captions:
        return None
    return random.choice(captions)

def parse_srt_file(srt_file):
    with open(srt_file, 'r', encoding='utf-8') as f:
        content = f.read()
    pattern = r'(?m)^\s*(\d+)\s+(\d{2}:\d{2}:\d{2},\d{3})\s+-->\s+(\d{2}:\d{2}:\d{2},\d{3})\s+([\s\S]*?)(?=\n\s*\n\s*\d+|$)'
    matches = re.findall(pattern, content)
    subtitle_entries = []
    for match in matches:
        index, start_time_str, end_time_str, text = match
        def time_to_seconds(time_str):
            hours, minutes, seconds = time_str.replace(',', '.').split(':')
            return float(hours) * 3600 + float(minutes) * 60 + float(seconds)
        start_time = time_to_seconds(start_time_str)
        end_time = time_to_seconds(end_time_str)
        subtitle_entries.append({
            'start_time': start_time,
            'end_time': end_time,
            'text': text.strip()
        })
    return subtitle_entries

def detect_gpu_codec():
    """Detect available GPU codec and return appropriate parameters"""
    import subprocess
    
    # Test for NVIDIA GPU (most reliable method)
    try:
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            # Double-check that NVENC is actually available
            try:
                test_result = subprocess.run([
                    'ffmpeg', '-hide_banner', '-f', 'lavfi', '-i', 'testsrc=duration=1:size=320x240:rate=1',
                    '-c:v', 'h264_nvenc', '-f', 'null', '-'
                ], capture_output=True, text=True, timeout=10)
                if test_result.returncode == 0:
                    print("DEBUG: NVIDIA GPU detected and NVENC available")
                    return 'h264_nvenc', ["-preset", "p4", "-cq", "23", "-b:v", "0"]
            except:
                pass
    except:
        pass
    
    # Test for AMD GPU
    try:
        result = subprocess.run(['rocm-smi'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            # Test if AMF encoder actually works
            try:
                test_result = subprocess.run([
                    'ffmpeg', '-hide_banner', '-f', 'lavfi', '-i', 'testsrc=duration=1:size=320x240:rate=1',
                    '-c:v', 'h264_amf', '-f', 'null', '-'
                ], capture_output=True, text=True, timeout=10)
                if test_result.returncode == 0:
                    print("DEBUG: AMD GPU detected and AMF available")
                    return 'h264_amf', ["-quality", "speed", "-rc", "cqp", "-qp", "23"]
            except:
                pass
    except:
        pass
    
    # Test for Intel GPU with actual functionality test
    try:
        # First check if Intel GPU device exists
        intel_gpu_check = subprocess.run(['lspci'], capture_output=True, text=True, timeout=5)
        if 'Intel' in intel_gpu_check.stdout and ('VGA' in intel_gpu_check.stdout or 'Display' in intel_gpu_check.stdout):
            # Test if QSV encoder actually works
            test_result = subprocess.run([
                'ffmpeg', '-hide_banner', '-f', 'lavfi', '-i', 'testsrc=duration=1:size=320x240:rate=1',
                '-c:v', 'h264_qsv', '-f', 'null', '-'
            ], capture_output=True, text=True, timeout=10)
            if test_result.returncode == 0:
                print("DEBUG: Intel GPU detected and QSV available")
                return 'h264_qsv', ["-preset", "fast", "-global_quality", "23"]
    except:
        pass
    
    # Fallback to CPU with optimized settings
    print("DEBUG: No GPU acceleration available, using optimized CPU encoding")
    return 'libx264', ["-preset", "ultrafast", "-crf", "23"]

def create_video(background_path, audio_segment, lyrics_data, output_path, segment_start_time, threads=1, use_random_caption=False):
    # Get GPU codec settings
    video_codec, ffmpeg_params = detect_gpu_codec()
    
    # Pick random font for this video
    selected_font = pick_random_font()
    print(f"DEBUG: Using lyrics font: {selected_font}")
    
    # Get random caption if requested
    random_caption = None
    caption_font = None
    if use_random_caption:
        random_caption = pick_random_caption()
        caption_font = pick_random_caption_font()
        print(f"DEBUG: Using caption: '{random_caption}' with font: {caption_font}")
    
    background = VideoFileClip(background_path)
    temp_audio_file = os.path.join(OUTPUT_FOLDER, "temp_audio.mp3")
    audio_segment.export(temp_audio_file, format="mp3")
    audio = AudioFileClip(temp_audio_file)
    duration = audio.duration

    if background.duration < duration:
        n_loops = int(np.ceil(duration / background.duration))
        background = VideoFileClip(background_path).with_effects([vfx.Loop(n_loops)])
        
    if background.duration > duration:
        background = background.subclipped(0, duration)
    
    # Crop to 9:16 without stretching
    w, h = background.size
    target_w, target_h = 1080, 1920
    scale = target_h / h
    new_w = int(w * scale)
    new_h = int(h * scale)
    background = background.resized((new_w, new_h))
    if new_w > target_w:
        x1 = (new_w - target_w) / 2
        x2 = x1 + target_w
        background = background.cropped(x1=x1, y1=0, x2=x2, y2=new_h)
    
    # Get a random start point for the background video
    offset = 0
    if background.duration > 35:
        offset = 4
    random_start = random.uniform(offset, max(offset, background.duration - duration))

    background = background.subclipped(random_start, random_start + duration)
    # Make final video 9:16
    background = background.resized((1080, 1920))

    background = background.with_audio(audio)

    text_clips = []
    
    # Add random caption at the top if requested
    if use_random_caption and random_caption:
        try:
            caption_clip = TextClip(
                text=random_caption,
                font_size=90,
                font=caption_font,
                color='white',
                stroke_color='black',
                stroke_width=3,
                method='label',
                text_align='center'
            )
            # Position at top of screen with some padding
            caption_clip = caption_clip.with_position(('center', 150)).with_duration(duration)
            text_clips.append(caption_clip)
        except Exception as e:
            print(f"DEBUG: Caption font error with {caption_font}, falling back to Arial: {e}")
            caption_clip = TextClip(
                text=random_caption,
                font_size=45,
                font='Arial',
                color='white',
                stroke_color='black',
                stroke_width=3,
                method='label',
                text_align='center'
            )
            caption_clip = caption_clip.with_position(('center', 150)).with_duration(duration)
            text_clips.append(caption_clip)
    
    # Add lyrics in the center
    for lyric in lyrics_data:
        relative_start = max(0, lyric['start_time'] - segment_start_time)
        relative_end = min(duration, lyric['end_time'] - segment_start_time)
        if relative_end > relative_start:
            try:
                txt = TextClip(
                    text=lyric['text'],
                    font_size=75,
                    font=selected_font,
                    color='white',
                    stroke_color='black',
                    stroke_width=2,
                    method='label',
                    text_align='center'
                )
                txt = txt.with_position(('center', 'center')).with_start(relative_start).with_end(relative_end)
                text_clips.append(txt)
            except Exception as e:
                print(f"DEBUG: Font error with {selected_font}, falling back to Arial: {e}")
                txt = TextClip(
                    text=lyric['text'],
                    font_size=55,
                    font='Arial',
                    color='white',
                    stroke_color='black',
                    stroke_width=2,
                    method='label',
                    text_align='center'
                )
                txt = txt.with_position(('center', 'center')).with_start(relative_start).with_end(relative_end)
                text_clips.append(txt)
            
    final_clip = CompositeVideoClip([background] + text_clips, size=background.size)
    
    # Use detected GPU codec and parameters
    final_clip.write_videofile(
        output_path, 
        codec=video_codec, 
        audio_codec='aac', 
        write_logfile=False, 
        logger='bar', 
        ffmpeg_params=ffmpeg_params, 
        fps=24, 
        threads=threads
    )

    background.close()
    final_clip.close()
    audio.close()
    os.remove(temp_audio_file)

def get_available_songs():
    """Get list of available songs with their base names"""
    songs = []
    for f in os.listdir(SONGS_FOLDER):
        if f.lower().endswith((".mp3", ".wav")):
            base_name = os.path.splitext(f)[0]
            srt_file = os.path.join(LYRICS_FOLDER, base_name + ".srt")
            if os.path.exists(srt_file):
                songs.append({
                    'file': f,
                    'base_name': base_name,
                    'srt_file': srt_file
                })
    return songs

def parse_duration_arg(duration_str):
    """Parse duration argument - can be single number or range like '12-20'"""
    if isinstance(duration_str, int):
        return duration_str, duration_str  # Single duration
    
    duration_str = str(duration_str)
    if '-' in duration_str:
        try:
            min_dur, max_dur = map(int, duration_str.split('-'))
            if min_dur > max_dur:
                min_dur, max_dur = max_dur, min_dur  # Swap if reversed
            return min_dur, max_dur
        except ValueError:
            print(f"Invalid duration range format: {duration_str}. Using default {DURATION}s")
            return DURATION, DURATION
    else:
        try:
            dur = int(duration_str)
            return dur, dur
        except ValueError:
            print(f"Invalid duration format: {duration_str}. Using default {DURATION}s")
            return DURATION, DURATION

def get_random_duration(min_dur, max_dur):
    """Get a random duration between min and max (inclusive)"""
    if min_dur == max_dur:
        return min_dur
    return random.randint(min_dur, max_dur)

def pick_song_segment(song_info, duration_range=(DURATION, DURATION)):
    """Pick a segment from a specific song"""
    # Get actual duration for this segment
    min_dur, max_dur = duration_range
    duration = get_random_duration(min_dur, max_dur)
    
    subtitles = parse_srt_file(song_info['srt_file'])
    if not subtitles:
        print(f"DEBUG: srt has no subtitles for {song_info['base_name']}")
        return None

    audio_path = os.path.join(SONGS_FOLDER, song_info['file'])
    audio = AudioSegment.from_file(audio_path)
    full_duration = len(audio) / 1000

    possible_entries = [entry for entry in subtitles if entry['start_time'] <= (full_duration - duration)]
    if not possible_entries:
        print(f"DEBUG: no suitable lyric entries for a {duration}s segment in {song_info['base_name']}")
        return None

    selected_entry = random.choice(possible_entries)
    start_time = selected_entry['start_time']
    end_time = min(start_time + duration, full_duration)

    start_ms = int(start_time * 1000)
    end_ms = int(end_time * 1000)
    segment_audio = audio[start_ms:end_ms]

    # Gather lyrics
    segment_lyrics = []
    for entry in subtitles:
        if entry['end_time'] > start_time and entry['start_time'] < end_time:
            segment_lyrics.append(entry)

    return {
        'song': song_info['file'],
        'base_name': song_info['base_name'],
        'segment_audio': segment_audio,
        'segment_lyrics': segment_lyrics,
        'start_time': start_time,
        'end_time': end_time,
        'actual_duration': duration
    }

def pick_random_song_segment(duration_range=(DURATION, DURATION)):
    """Pick a random song segment (legacy function for compatibility)"""
    songs = get_available_songs()
    if not songs:
        print("DEBUG: no songs found")
        return None
    
    selected_song = random.choice(songs)
    return pick_song_segment(selected_song, duration_range)

def pick_random_background():
    backgrounds = [f for f in os.listdir(BACKGROUNDS_FOLDER) if f.lower().endswith((".mp4", ".mov", ".avi"))]
    if not backgrounds:
        print("DEBUG: no background videos found")
        return None
    return random.choice(backgrounds)

def generate_datetime_filename(base_name):
    """Generate filename with current date and time"""
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Include milliseconds for uniqueness
    return f"{base_name}_{timestamp}.mp4"

def create_song_folder(song_base_name):
    """Create folder for specific song if it doesn't exist"""
    song_folder = os.path.join(OUTPUT_FOLDER, song_base_name)
    os.makedirs(song_folder, exist_ok=True)
    return song_folder

def generate_videos_per_song(songs, videos_per_song, duration_range, threads, use_random_caption=False):
    """Generate specific number of videos for each song"""
    total_videos = len(songs) * videos_per_song
    current_video = 0
    min_dur, max_dur = duration_range
    
    for song_info in songs:
        print(f"\n=== Processing song: {song_info['base_name']} ===")
        song_folder = create_song_folder(song_info['base_name'])
        
        for i in range(videos_per_song):
            current_video += 1
            
            # Generate the snippet
            song_segment = pick_song_segment(song_info, duration_range)
            if not song_segment:
                print(f"Could not generate segment for {song_info['base_name']}, skipping...")
                continue

            actual_duration = song_segment.get('actual_duration', max_dur)
            print(f"DEBUG: segment {song_segment['start_time']:.1f}s to {song_segment['end_time']:.1f}s (duration: {actual_duration}s)")
            print(f"Video {current_video} of {total_videos} ({i+1}/{videos_per_song} for this song)")
            
            # Pick a background
            background_file = pick_random_background()
            if not background_file:
                print("No background videos found, skipping...")
                continue
            background_path = os.path.join(BACKGROUNDS_FOLDER, background_file)
            
            # Generate datetime-based filename
            output_filename = generate_datetime_filename(song_segment['base_name'])
            output_video_path = os.path.join(song_folder, output_filename)

            # Create the video
            try:
                create_video(
                    background_path=background_path,
                    audio_segment=song_segment['segment_audio'],
                    lyrics_data=song_segment['segment_lyrics'],
                    output_path=output_video_path,
                    segment_start_time=song_segment['start_time'],
                    threads=threads,
                    use_random_caption=use_random_caption
                )
                print(f"✓ Created: {output_video_path}")
            except Exception as e:
                print(f"✗ Failed to create video: {e}")

def generate_random_videos(num_videos, duration_range, threads, use_random_caption=False):
    """Generate random videos from random songs"""
    min_dur, max_dur = duration_range
    
    for i in range(num_videos):
        # Generate the snippet
        song_segment = pick_random_song_segment(duration_range)
        if not song_segment:
            print("Could not generate random segment, skipping...")
            continue

        actual_duration = song_segment.get('actual_duration', max_dur)
        print(f"\nDEBUG: selected song {song_segment['song']}")
        print(f"DEBUG: segment {song_segment['start_time']:.1f}s to {song_segment['end_time']:.1f}s (duration: {actual_duration}s)")
        print(f"Video {i + 1} of {num_videos}")
        
        # Create song folder
        song_folder = create_song_folder(song_segment['base_name'])
        
        # Pick a background
        background_file = pick_random_background()
        if not background_file:
            print("No background videos found, skipping...")
            continue
        background_path = os.path.join(BACKGROUNDS_FOLDER, background_file)
        
        # Generate datetime-based filename
        output_filename = generate_datetime_filename(song_segment['base_name'])
        output_video_path = os.path.join(song_folder, output_filename)

        # Create the video
        try:
            create_video(
                background_path=background_path,
                audio_segment=song_segment['segment_audio'],
                lyrics_data=song_segment['segment_lyrics'],
                output_path=output_video_path,
                segment_start_time=song_segment['start_time'],
                threads=threads,
                use_random_caption=use_random_caption
            )
            print(f"✓ Created: {output_video_path}")
        except Exception as e:
            print(f"✗ Failed to create video: {e}")

def main():
    parser = argparse.ArgumentParser(description="Generate videos with subtitles and song snippets using GPU acceleration.")
    parser.add_argument("--duration", type=str, default=str(DURATION), help="Duration of each video segment in seconds (single number or range like '12-20')")
    parser.add_argument("--threads", type=int, default=1, help="Number of threads to use for video generation")
    parser.add_argument("--random-cap", action="store_true", help="Add random captions at the top of videos")
    
    # Mutually exclusive group for generation mode
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--random", type=int, help="Generate N random videos from random songs")
    group.add_argument("--per-song", type=int, help="Generate N videos for each available song")
    
    args = parser.parse_args()

    # Parse duration argument
    duration_range = parse_duration_arg(args.duration)
    min_dur, max_dur = duration_range
    
    if min_dur == max_dur:
        print(f"Using fixed duration: {min_dur} seconds")
    else:
        print(f"Using random duration range: {min_dur}-{max_dur} seconds")

    # Get available songs
    songs = get_available_songs()
    if not songs:
        print("No songs with matching SRT files found!")
        return

    print(f"Found {len(songs)} songs with lyrics:")
    for song in songs:
        print(f"  - {song['base_name']}")
    
    # List available fonts
    fonts = get_available_fonts()
    print(f"\nFound {len(fonts)} fonts available for random selection")
    
    # Check random captions setup if requested
    if args.random_cap:
        captions = get_random_captions()
        caption_fonts = get_random_caption_fonts()
        print(f"Random captions enabled: {len(captions)} captions, {len(caption_fonts)} caption fonts")

    if args.random:
        print(f"\n=== Generating {args.random} random videos ===")
        generate_random_videos(args.random, duration_range, args.threads, args.random_cap)
    
    elif args.per_song:
        print(f"\n=== Generating {args.per_song} videos per song ({len(songs) * args.per_song} total) ===")
        generate_videos_per_song(songs, args.per_song, duration_range, args.threads, args.random_cap)

if __name__ == "__main__":
    main()