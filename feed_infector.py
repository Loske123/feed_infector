import os
import random
import re
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip
from pydub import AudioSegment
import numpy as np

# Define folder paths
LYRICS_FOLDER = "lyrics"
SONGS_FOLDER = "songs"
BACKGROUNDS_FOLDER = "background"
OUTPUT_FOLDER = "output_videos"

# Create output folder if it doesn't exist
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def parse_srt_file(srt_file):
    """Parse an SRT file and return a list of subtitle entries with timestamps"""
    with open(srt_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern to match SRT entries
    pattern = r'(\d+)\s+(\d{2}:\d{2}:\d{2},\d{3})\s+-->\s+(\d{2}:\d{2}:\d{2},\d{3})\s+([\s\S]*?)(?=\n\n\d+|$)'
    matches = re.findall(pattern, content)
    
    subtitle_entries = []
    for match in matches:
        index, start_time_str, end_time_str, text = match
        
        # Convert HH:MM:SS,mmm to seconds
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

def get_random_segment(song_path, lyrics_data, min_duration=10, max_duration=30):
    """
    Extract a random segment from the song along with corresponding lyrics
    Returns: audio_segment, start_time, end_time, segment_lyrics
    """
    # Get full audio duration
    audio = AudioSegment.from_file(song_path)
    full_duration = len(audio) / 1000  # Convert to seconds
    
    if not lyrics_data:
        raise ValueError("No lyrics found in the SRT file")
    
    # Pick a random starting point from the timestamped lyrics
    start_entry = random.choice(lyrics_data)
    start_time = start_entry['start_time']
    
    # Determine end time (either based on desired duration or next few lyrics)
    desired_duration = random.uniform(min_duration, max_duration)
    end_time = min(start_time + desired_duration, full_duration)
    
    # Collect lyrics that fall within our segment
    segment_lyrics = []
    for entry in lyrics_data:
        if start_time <= entry['start_time'] < end_time or (entry['start_time'] <= start_time and entry['end_time'] > start_time):
            # Adjust entry if it stretches beyond our segment
            adjusted_entry = entry.copy()
            adjusted_entry['end_time'] = min(entry['end_time'], end_time)
            segment_lyrics.append(adjusted_entry)
    
    # Extract audio segment
    start_ms = int(start_time * 1000)
    end_ms = int(end_time * 1000)
    audio_segment = audio[start_ms:end_ms]
    
    return audio_segment, start_time, end_time, segment_lyrics

def create_video(background_path, audio_segment, lyrics_data, output_path, segment_start_time):
    """Create a video with background, audio segment and lyrics overlay"""
    # Load background video
    background = VideoFileClip(background_path)
    
    # Save temporary audio file
    temp_audio_file = os.path.join(OUTPUT_FOLDER, "temp_audio.mp3")
    audio_segment.export(temp_audio_file, format="mp3")
    
    # Load audio
    audio = AudioFileClip(temp_audio_file)
    
    # Get duration from audio
    duration = audio.duration
    
    # Trim or loop background video to match audio duration
    if background.duration < duration:
        # Loop video if needed
        n_loops = int(np.ceil(duration / background.duration))
        background = VideoFileClip(background_path).loop(n=n_loops)
    
    # Trim background to audio duration
    background = background.subclip(0, duration)
    
    # Set audio
    background = background.set_audio(audio)
    
    # Create text clips for each lyric
    text_clips = []
    
    for lyric in lyrics_data:
        # Adjust timestamps relative to our segment start time
        relative_start = max(0, lyric['start_time'] - segment_start_time)
        relative_end = min(duration, lyric['end_time'] - segment_start_time)
        
        if relative_end > relative_start:
            text = TextClip(
                lyric['text'],
                fontsize=70,
                color='white',
                font="Arial-Bold",
                stroke_color='black',
                stroke_width=2,
                method='caption',
                size=(background.w * 0.9, None),
                align='center'
            )
            text = text.set_position(('center', 'center')).set_start(relative_start).set_end(relative_end)
            text_clips.append(text)
    
    # Combine video and text
    final_clip = CompositeVideoClip([background] + text_clips)
    
    # Write output file
    final_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
    
    # Clean up
    background.close()
    final_clip.close()
    os.remove(temp_audio_file)

def generate_videos(num_videos=10):
    """Generate specified number of videos"""
    # Get all available files
    lyrics_files = [os.path.join(LYRICS_FOLDER, f) for f in os.listdir(LYRICS_FOLDER) if f.endswith('.srt')]
    song_files = [os.path.join(SONGS_FOLDER, f) for f in os.listdir(SONGS_FOLDER) if f.endswith(('.mp3', '.wav'))]
    background_files = [os.path.join(BACKGROUNDS_FOLDER, f) for f in os.listdir(BACKGROUNDS_FOLDER) if f.endswith(('.mp4', '.mov'))]
    
    # Make sure we have corresponding song and lyrics files
    valid_pairs = []
    for lyrics_file in lyrics_files:
        base_name = os.path.splitext(os.path.basename(lyrics_file))[0]
        for song_file in song_files:
            if base_name in os.path.basename(song_file):
                valid_pairs.append((lyrics_file, song_file))
                break
    
    if not valid_pairs:
        raise ValueError("No matching song and lyrics files found")
    
    if not background_files:
        raise ValueError("No background video files found")
    
    # Generate videos
    for i in range(num_videos):
        try:
            # Select random song-lyrics pair
            lyrics_file, song_file = random.choice(valid_pairs)
            
            # Select random background
            background_file = random.choice(background_files)
            
            # Load lyrics data
            lyrics_data = parse_sr t_file(lyrics_file)
            
            # Get random segment
            audio_segment, start_time, end_time, segment_lyrics = get_random_segment(song_file, lyrics_data)
            
            # Create output filename
            output_filename = f"video_{i+1}.mp4"
            output_path = os.path.join(OUTPUT_FOLDER, output_filename)
            
            print(f"Creating video {i+1}/{num_videos}...")
            print(f"Using song: {os.path.basename(song_file)}, background: {os.path.basename(background_file)}")
            print(f"Segment: {start_time:.2f}s to {end_time:.2f}s")
            
            create_video(background_file, audio_segment, segment_lyrics, output_path, start_time)
            print(f"Created {output_path}")
            
        except Exception as e:
            print(f"Error creating video {i+1}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate TikTok videos with random song segments and lyrics")
    parser.add_argument("--num", type=int, default=10, help="Number of videos to generate")
    args = parser.parse_args()
    
    generate_videos(args.num)