import os
import random
import re
from pydub import AudioSegment

# Define folder paths
LYRICS_FOLDER = "lyrics"
SONGS_FOLDER = "songs"
BACKGROUNDS_FOLDER = "background"
OUTPUT_FOLDER = "output_videos"

# Create output folder if it doesn't exist
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
    # Filter entries that have enough time for a 10-second segment
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
    # Gather any lyrics that overlap this window
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
    output_audio_path = os.path.join(OUTPUT_FOLDER, base_name + "_segment.mp3")
    segment_audio.export(output_audio_path, format="mp3")
    print("DEBUG: saved segment", output_audio_path)

if __name__ == "__main__":
    main()
