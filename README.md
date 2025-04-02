# Feed Infector

A Python script to generate short TikTok-style videos with:

- **Song snippets** (random 10-second selection).
- Overlaid **lyrics** from an SRT file.
- **Background videos** cropped to 9:16.

## Setup

It uses python 3.10.11

1. **Clone the repo** (or download the files).

2. **Create a virtual environment** (recommended):

   bash
   python -m venv venv

   # Windows

   venv\Scripts\activate

   # or

   # macOS/Linux

   source venv/bin/activate

3. **Install dependencies**:

   pip install -r requirements.txt

   Requirements typically include:
   -moviepy
   -pydub
   -numpy

## Usage

    Run the script with:
        python run.py --num 10

This will:
-Pick a random song and .srt pair.
-Select a 10-second random lyric snippet.
-Pick a random background.
-Create a 9:16 cropped video with overlaid lyrics in output_videos/.
-Repeat the process 10 times.

If you omit --num, it defaults to generating one video:
python run.py
