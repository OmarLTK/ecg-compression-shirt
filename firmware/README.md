# Firmware (ESP32)

Board: ESP32-WROOM-32 DevKit-style board with micro-USB (see `../hardware/photos/`). Lead I is on GPIO 34 and Lead II on GPIO 35 (ADC1, input-only pins).

**Source code: pending upload.** The behaviour below comes from Omar's contribution summary and the report.

## Acquisition (Omar Ali-Yare)

- Fixed 360 Hz output rate, chosen to match MIT-BIH.
- 16× oversampling per output sample, averaged to reduce ADC noise.
- A **moving-average filter for 60 Hz rejection**. The report calls this a digital notch, but it is a boxcar (FIR comb).
- A digital high-pass for baseline wander.
- Timestamped capture showed an early build only reached 190 Hz. Fixing the oversampling loop restored 360 Hz.

### Why the sample-rate bug also broke the 60 Hz filter

An N-sample moving average at rate fs has its first null at fs / N. A null at exactly 60 Hz with fs = 360 Hz means N = 6. That N is inferred, so confirm it from the code. At 190 Hz the same filter nulls at 31.7 Hz: mains passes untouched and real QRS energy gets removed. Restoring 360 Hz is what put the null back on 60 Hz.

### Cost of using a moving average as the mains filter

The 6-tap boxcar is also a low-pass:

| f | 10 Hz | 20 Hz | 26.6 Hz | 40 Hz | 60 Hz |
|---|---|---|---|---|---|
| Gain | −0.4 dB | −1.6 dB | **−3 dB** | −7.5 dB | null |

The −3 dB point is about 27 Hz, so R-wave peaks are slightly blunted. That is acceptable for heart rate and rhythm. It is worth knowing when comparing waveforms against MIT-BIH, which was recorded at 0.1–100 Hz. A second-order IIR notch at 60 Hz (Q ≈ 30) removes mains without the low-pass side effect.

## BLE (Tenzin Dhonyoe)

One GATT service with four notify characteristics:
- Three lead characteristics (12-bit samples packed in 16-bit words).
- One 8-byte classification packet (label, confidence, sample index, HR).

Sequence numbers in the packets let the app detect drops. Two leads are acquired; Lead III is derived as II − I.

## Wanted for this folder

- The sketch or ESP-IDF project.
- ADC attenuation setting.
- The sample-timer method (hardware timer vs. `delay`).
- The moving-average length.
- The high-pass filter coefficients.
- The GATT UUIDs and packet format.
