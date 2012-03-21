#
# html5_audio.py <Peter.Bienstman@UGent.be>
#

import re
import urllib

from mnemosyne.libmnemosyne.filter import Filter

re_audio = re.compile(r"""<audio src=\"(.+?)\">""", re.DOTALL | re.IGNORECASE)

script = """
<script type="text/javascript">

    var soundFiles = new Array(_SOUNDFILES_);
    var next = 0;

    function loadPlayer() {
        var audioPlayer = new Audio();
        audioPlayer.controls = 'controls';
        audioPlayer.addEventListener('ended', nextSoundFile, false);
        document.getElementById('player').appendChild(audioPlayer);
        var autoplay = true;
        if (autoplay == true) {
            nextSoundFile();
        } else {
            audioPlayer.src = soundFiles[next];
            next++;
            audioPlayer.load();
        }
    }

    function nextSoundFile() {
        var audioPlayer = document.getElementsByTagName('audio')[0];
        if (soundFiles[next] != undefined) {
            audioPlayer.src = soundFiles[next];
            audioPlayer.load();
            audioPlayer.play();
        }
        else {
            // Reset playlist to first sound file.
            next = 0;
            audioPlayer.src = soundFiles[next];
            audioPlayer.load();
        }
        next++;
    }

    window.onload = function() {
        loadPlayer();
    };

</script>
"""


class Html5Audio(Filter):

    """Incorporate media player supporting more than 1 sound file."""

    def run(self, text, card, fact_key, **render_args):
        if not re_audio.search(text):
            return text
        sound_files = []
        for match in re_audio.finditer(text):
            sound_files.append("'" + \
                urllib.quote(match.group(1).encode("utf-8"), safe="/:") + "'")
            #sound_files.append("'" + urllib.quote(match.group(1).encode("utf-8"), safe="/:").replace("%","\\x") + "'")
            #sound_files.append("'" + match.group(1) + "'")
            #sound_files.append("'" + match.group(1).encode("mbcs") + "'")
            text = text.replace(match.group(0), "")
        #print sound_files, ",".join(sound_files)
        text = script + text + "<div id='player'></div>"
        text = text.replace("_SOUNDFILES_", ",".join(sound_files))
        if self.config()["media_autoplay"] == False:
            text = text.replace("autoplay = true", "autoplay = false")
        if self.config()["media_controls"] == False:
            text = text.replace("audioPlayer.controls = 'controls';", "")
        return text
