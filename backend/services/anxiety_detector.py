CALMING_MESSAGE = "Let's take a moment. There is no rush. Take a breath, collect your thoughts, and continue when you are ready."

# Thresholds
FAST_SPEECH_WPM = 180  # Words per minute considered "fast"
STUTTER_THRESHOLD = 2  # Number of repeated words indicating stuttering
LONG_PAUSE_THRESHOLD = 2  # Number of long pauses indicating anxiety


def detect_anxiety(speech_metrics: dict) -> dict:
    """Analyze speech metrics to detect signs of anxiety.

    Returns:
        dict with 'is_anxious' bool and 'reason' string
    """
    reasons = []

    wpm = speech_metrics.get("speech_rate_wpm", 0)
    stutters = speech_metrics.get("stutter_count", 0)
    pauses = speech_metrics.get("long_pauses", 0)

    if wpm > FAST_SPEECH_WPM:
        reasons.append(f"fast speech rate ({wpm:.0f} WPM)")

    if stutters >= STUTTER_THRESHOLD:
        reasons.append(f"stuttering detected ({stutters} repetitions)")

    if pauses >= LONG_PAUSE_THRESHOLD:
        reasons.append(f"multiple long pauses ({pauses} pauses >2s)")

    is_anxious = len(reasons) > 0

    return {
        "is_anxious": is_anxious,
        "reason": ", ".join(reasons) if reasons else "normal",
        "calming_message": CALMING_MESSAGE if is_anxious else None,
        "metrics": {
            "speech_rate_wpm": wpm,
            "stutter_count": stutters,
            "long_pauses": pauses,
        },
    }
