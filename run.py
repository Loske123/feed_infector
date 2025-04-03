import os
import random
import re
from pydub import AudioSegment
import numpy as np
from moviepy import *
import argparse


LYRICS_FOLDER = "lyrics"
SONGS_FOLDER = "songs"
BACKGROUNDS_FOLDER = "background"
OUTPUT_FOLDER = "output_videos"
FONT = "fonts/OpenSans-Bold.ttf"
DURATION = 15  # seconds


for folder in [LYRICS_FOLDER, SONGS_FOLDER, BACKGROUNDS_FOLDER, "fonts", OUTPUT_FOLDER]:
    os.makedirs(folder, exist_ok=True)

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

def create_video(background_path, audio_segment, lyrics_data, output_path, segment_start_time):
    background = VideoFileClip(background_path)
    temp_audio_file = os.path.join(OUTPUT_FOLDER, "temp_audio.mp3")
    audio_segment.export(temp_audio_file, format="mp3")
    audio = AudioFileClip(temp_audio_file)
    duration = audio.duration

    if background.duration < duration:
        n_loops = int(np.ceil(duration / background.duration))
        background = VideoFileClip(background_path).loop(n_loops)
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
    # If new_w < target_w, we could letterbox or do something else, but we only strictly handle the usual case here.
    # Get a random start point for the background video
    random_start = random.uniform(3, max(3, background.duration - duration))

    background = background.subclipped(random_start, random_start + duration)
    # Make final video 9:16
    background = background.resized((1080, 1920))

    background = background.with_audio(audio)

    text_clips = []
    for lyric in lyrics_data:
        relative_start = max(0, lyric['start_time'] - segment_start_time)
        relative_end = min(duration, lyric['end_time'] - segment_start_time)
        if relative_end > relative_start:
            txt = TextClip(
                text=lyric['text'],
                font_size=55,
                font=FONT,
                color='white',
                stroke_color='black',
                stroke_width=2,
                method='label',
                
                text_align='center'
            )
            txt = txt.with_position(('center', 'center')).with_start(relative_start).with_end(relative_end)
            text_clips.append(txt)

    final_clip = CompositeVideoClip([background] + text_clips)
    final_clip.write_videofile(output_path, codec='libx264', audio_codec='aac', write_logfile=False, logger = 'bar', preset="ultrafast", threads=8, fps = 24)

    background.close()
    final_clip.close()
    audio.close()
    os.remove(temp_audio_file)

def pick_random_song_segment(duration=DURATION):
    songs = [f for f in os.listdir(SONGS_FOLDER) if f.lower().endswith((".mp3", ".wav"))]
    if not songs:
        print("DEBUG: no songs found")
        return None

    selected_song = random.choice(songs)
    base_name = os.path.splitext(selected_song)[0]
    srt_file = os.path.join(LYRICS_FOLDER, base_name + ".srt")

    if not os.path.exists(srt_file):
        print(f"DEBUG: no matching srt found for {base_name}")
        return None

    subtitles = parse_srt_file(srt_file)
    if not subtitles:
        print("DEBUG: srt has no subtitles")
        return None

    audio_path = os.path.join(SONGS_FOLDER, selected_song)
    audio = AudioSegment.from_file(audio_path)
    full_duration = len(audio) / 1000

    possible_entries = [entry for entry in subtitles if entry['start_time'] <= (full_duration - duration)]
    if not possible_entries:
        print(f"DEBUG: no suitable lyric entries for a {duration}s segment")
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
        'song': selected_song,
        'base_name': base_name,
        'segment_audio': segment_audio,
        'segment_lyrics': segment_lyrics,
        'start_time': start_time,
        'end_time': end_time
    }

def pick_random_background():
    backgrounds = [f for f in os.listdir(BACKGROUNDS_FOLDER) if f.lower().endswith((".mp4", ".mov", ".avi"))]
    if not backgrounds:
        print("DEBUG: no background videos found")
        return None
    return random.choice(backgrounds)

def main():
    parser = argparse.ArgumentParser(description="Generate random videos with subtitles and a song snippet.")
    parser.add_argument("--num", type=int, default=1, help="Number of videos to generate")
    args = parser.parse_args()

    for i in range(args.num):
        # Generate the snippet
        song_segment = pick_random_song_segment()
        if not song_segment:
            return

        print("DEBUG: selected song", song_segment['song'])
        print("DEBUG: random lyric-based segment", song_segment['start_time'], "to", song_segment['end_time'])
        print("DEBUG: lyrics in segment:")
        for entry in song_segment['segment_lyrics']:
            print(entry)

        # Pick a background
        background_file = pick_random_background()
        if not background_file:
            return
        background_path = os.path.join(BACKGROUNDS_FOLDER, background_file)

        # Output file, e.g., "songname_segment_1.mp4"
        output_video_path = os.path.join(
            OUTPUT_FOLDER,
            f"{song_segment['base_name']}_segment_{i+1}.mp4"
        )

        # Create the video
        create_video(
            background_path=background_path,
            audio_segment=song_segment['segment_audio'],
            lyrics_data=song_segment['segment_lyrics'],
            output_path=output_video_path,
            segment_start_time=song_segment['start_time']
        )

if __name__ == "__main__":
    main()
