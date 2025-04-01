import os
import random
import re
from pydub import AudioSegment
import numpy as np
from moviepy import *

LYRICS_FOLDER = "lyrics"
SONGS_FOLDER = "songs"
BACKGROUNDS_FOLDER = "background"
OUTPUT_FOLDER = "output_videos"
FONT = "fonts/font.otf"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

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

    background = background.subclipped(0, duration)
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
                font_size=40,
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
    final_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')

    background.close()
    final_clip.close()
    audio.close()
    os.remove(temp_audio_file)

def main():
    songs = [f for f in os.listdir(SONGS_FOLDER) if f.lower().endswith((".mp3", ".wav"))]
    if not songs:
        print("DEBUG: no songs found")
        return

    selected_song = random.choice(songs)
    print("DEBUG: selected song", selected_song)

    base_name = os.path.splitext(selected_song)[0]
    srt_file = os.path.join(LYRICS_FOLDER, base_name + ".srt")

    if not os.path.exists(srt_file):
        print("DEBUG: no matching srt found for", base_name)
        return

    print("DEBUG: found matching srt", srt_file)
    subtitles = parse_srt_file(srt_file)
    if not subtitles:
        print("DEBUG: srt has no subtitles")
        return

    audio_path = os.path.join(SONGS_FOLDER, selected_song)
    audio = AudioSegment.from_file(audio_path)
    full_duration = len(audio) / 1000

    possible_entries = [entry for entry in subtitles if entry['start_time'] <= (full_duration - 10)]
    if not possible_entries:
        print("DEBUG: no suitable lyric entries for a 10s segment")
        return

    selected_entry = random.choice(possible_entries)
    start_time = selected_entry['start_time']
    end_time = start_time + 10
    if end_time > full_duration:
        end_time = full_duration

    print("DEBUG: random lyric-based segment", start_time, "to", end_time)

    segment_lyrics = []
    for entry in subtitles:
        if entry['end_time'] > start_time and entry['start_time'] < end_time:
            segment_lyrics.append(entry)
    print("DEBUG: lyrics in segment:")
    for entry in segment_lyrics:
        print(entry)

    start_ms = int(start_time * 1000)
    end_ms = int(end_time * 1000)
    segment_audio = audio[start_ms:end_ms]

    backgrounds = [f for f in os.listdir(BACKGROUNDS_FOLDER) if f.lower().endswith((".mp4", ".mov", ".avi"))]
    if not backgrounds:
        print("DEBUG: no background videos found")
        return

    selected_background = random.choice(backgrounds)
    background_path = os.path.join(BACKGROUNDS_FOLDER, selected_background)

    output_video_path = os.path.join(OUTPUT_FOLDER, base_name + "_segment.mp4")
    create_video(
        background_path=background_path,
        audio_segment=segment_audio,
        lyrics_data=segment_lyrics,
        output_path=output_video_path,
        segment_start_time=start_time
    )

if __name__ == "__main__":
    main()
