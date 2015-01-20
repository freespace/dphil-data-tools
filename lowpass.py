from scipy import signal

def lowpassfilter(yvec, sampling_rate, cutoff_freq, order=5):
    """
    Sampling rate and cutoff should be in Hz
    """
    # this is important because we cannot filter signals above this, as they will alias as a lower frequency signal
    nyq_freq = 0.5 * sampling_rate

    # divide by nyq_frequency because analog=False by default
    b, a = signal.butter(order, cutoff_freq/nyq_freq, 'lowpass')

    return signal.lfilter(b, a, yvec)
