"""Optional audio input using ComfyUI's native audio decoder."""

import hashlib
import os

import folder_paths
from comfy_extras.nodes_audio import load as load_audio


def _empty(value):
    return value is None or isinstance(value, str) and value.strip() in ("", "None")


class MTAIOptionalLoadAudio:
    @classmethod
    def INPUT_TYPES(cls):
        input_dir = folder_paths.get_input_directory()
        files = [name for name in os.listdir(input_dir)
                 if os.path.isfile(os.path.join(input_dir, name))]
        files = folder_paths.filter_files_content_types(files, ["audio"])
        return {"optional": {
            "audio": (["None", *sorted(files)], {"audio_upload": True, "default": "None"}),
            "enabled": ("BOOLEAN", {"default": True}),
            # Native AUDIOUPLOAD needs the audio preview widget created first.
            "audioUI": ("AUDIO_UI", {}),
            "upload": ("AUDIOUPLOAD", {}),
        }}

    RETURN_TYPES = ("AUDIO", "BOOLEAN")
    RETURN_NAMES = ("AUDIO", "has_audio")
    FUNCTION = "load_audio"
    CATEGORY = "MTAI/optional inputs"
    DESCRIPTION = (
        "Empty or disabled input returns None, False, without generating silence. "
        "Selected files use the native audio decoder; invalid files raise errors. "
        "The downstream node must support None."
    )

    @classmethod
    def VALIDATE_INPUTS(cls, audio=None, enabled=True):
        if not isinstance(enabled, bool):
            return "enabled must be a boolean."
        if not enabled or _empty(audio):
            return True
        if not isinstance(audio, str):
            return "audio must be a filename string or null."
        if not folder_paths.exists_annotated_filepath(audio):
            return f"Invalid audio file: {audio}"
        if not os.path.isfile(folder_paths.get_annotated_filepath(audio)):
            return f"Invalid audio file: {audio}"
        return True

    @classmethod
    def IS_CHANGED(cls, audio=None, enabled=True):
        if not enabled or _empty(audio):
            return "empty"
        digest = hashlib.sha256()
        with open(folder_paths.get_annotated_filepath(audio), "rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()

    def load_audio(self, audio=None, enabled=True):
        if not enabled or _empty(audio):
            return (None, False)
        waveform, sample_rate = load_audio(folder_paths.get_annotated_filepath(audio))
        return ({"waveform": waveform.unsqueeze(0), "sample_rate": sample_rate}, True)
