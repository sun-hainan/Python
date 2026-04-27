# -*- coding: utf-8 -*-

"""

算法实现：18_信号与图像 / time_frequency



本文件实现 time_frequency 相关的算法功能。

"""



import numpy as np



def short_time_energy(signal, frame_size=256, hop=128):

    n_frames = (len(signal) - frame_size) // hop + 1

    ste = np.zeros(n_frames)

    for i in range(n_frames):

        frame = signal[i*hop:i*hop+frame_size]

        ste[i] = np.sum(frame**2) / frame_size

    return ste



def zero_crossing_rate_tfc(signal, frame_size=256, hop=128):

    n_frames = (len(signal) - frame_size) // hop + 1

    zcr = np.zeros(n_frames)

    for i in range(n_frames):

        frame = signal[i*hop:i*hop+frame_size]

        zcr[i] = np.sum(np.abs(np.diff(np.sign(frame)))) / (2*frame_size)

    return zcr



def reassign_spectrogram(signal, window=512, hop=128):

    n_frames = (len(signal) - window) // hop + 1

    from scipy.signal import spectrogram

    f,t,Sxx = spectrogram(signal, nperseg=window, noverlap=window-hop)

    return t, f, np.abs(Sxx)



if __name__ == "__main__":

    np.random.seed(42)

    sig = np.sin(2*np.pi*50*np.linspace(0,1,2048))

    ste = short_time_energy(sig)

    zcr = zero_crossing_rate_tfc(sig)

    print(f"STE shape: {ste.shape}, ZCR shape: {zcr.shape}")

    print("\n时频分析测试完成!")

