 txt = TextClip(
                font = FONT,
                text = lyric['text'],
                font_size=40,
                color='white',
                stroke_color='black',
                stroke_width=2,
                method='label',
                
                text_align='center'
            )
            txt = txt.with_position(('center', 'center')).with_start(relative_start).with_end(relative_end)
            text_clips.append(txt)